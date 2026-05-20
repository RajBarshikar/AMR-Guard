import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useRewards } from '../contexts/RewardsContext';
import { searchDrugs, getNearestBins, createTakeBackBundle, calculateErs } from '../utils/api';
import Icons from '../components/Icons';
import LoadingTips from '../components/LoadingTips';

const MEDICINE_TYPES = ['Tablet', 'Capsule', 'Syrup'];

function MedicineTypeSelector({ value, onChange }) {
  return (
    <div style={{ display: 'flex', gap: '8px' }}>
      {MEDICINE_TYPES.map((type) => (
        <button
          key={type}
          type="button"
          onClick={() => onChange(type)}
          style={{
            flex: 1,
            padding: '10px 0',
            borderRadius: '10px',
            border: `2px solid ${value === type ? 'var(--accent)' : 'var(--border-primary)'}`,
            background: value === type ? 'var(--accent-bg-strong)' : 'var(--bg-secondary)',
            color: value === type ? 'var(--accent)' : 'var(--text-secondary)',
            fontWeight: value === type ? '700' : '500',
            fontSize: '13px',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          {type}
        </button>
      ))}
    </div>
  );
}

function DrugSearchInput({ value, onChange, onSelect }) {
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef(null);
  const wrapperRef = useRef(null);

  const handleChange = (e) => {
    const val = e.target.value;
    onChange(val);
    if (val.length < 2) { setSuggestions([]); setOpen(false); return; }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await searchDrugs(val);
        setSuggestions(res.results || []);
        setOpen(true);
      } catch {}
    }, 300);
  };

  const pick = (s) => {
    onSelect(s);
    setSuggestions([]);
    setOpen(false);
  };

  return (
    <div ref={wrapperRef} style={{ position: 'relative' }}>
      <input
        type="text"
        value={value}
        onChange={handleChange}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onFocus={() => suggestions.length > 0 && setOpen(true)}
        placeholder="e.g. Amoxicillin"
        style={{
          width: '100%',
          padding: '11px 14px',
          borderRadius: '10px',
          border: '1.5px solid var(--border-primary)',
          background: 'var(--bg-secondary)',
          color: 'var(--text-primary)',
          fontSize: '14px',
          outline: 'none',
          boxSizing: 'border-box',
        }}
      />
      {open && suggestions.length > 0 && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 4px)',
          left: 0,
          right: 0,
          background: 'var(--bg-card)',
          border: '1px solid var(--border-primary)',
          borderRadius: '10px',
          boxShadow: 'var(--shadow-md)',
          zIndex: 100,
          maxHeight: '180px',
          overflowY: 'auto',
        }}>
          {suggestions.map((s, i) => (
            <div
              key={i}
              onMouseDown={() => pick(s)}
              style={{
                padding: '10px 14px',
                cursor: 'pointer',
                borderBottom: i < suggestions.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                fontSize: '13px',
                color: 'var(--text-primary)',
              }}
            >
              <span style={{ fontWeight: '600' }}>{s.name}</span>
              <span style={{ color: 'var(--text-tertiary)', marginLeft: '6px', fontSize: '11px' }}>
                {s.type}{s.is_antibiotic ? ' · Antibiotic' : ''}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const emptyItem = () => ({
  drug_name: '',
  medicine_type: 'Tablet',
  quantity: 1,
  expiry_date: '',
  is_antibiotic: false,
  ersLoading: false,
  ersData: null,
  lastFetchedSignature: null,
});

export default function TakeBack() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useLanguage();
  const { deviceId, district } = useRewards();

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Bundle of medicines
  const [items, setItems] = useState([{
    ...emptyItem(),
    drug_name: location.state?.drugName || '',
    expiry_date: location.state?.expiryDate || '',
    is_antibiotic: location.state?.isAntibiotic || false,
  }]);

  // Pharmacy selection — pre-populated if coming from MapView
  const preselectedPharmacy = location.state?.pharmacy || null;
  const [centres, setCentres] = useState([]);
  const [centresLoaded, setCentresLoaded] = useState(false);
  const [selectedCentre, setSelectedCentre] = useState(preselectedPharmacy ? { ...preselectedPharmacy, id: preselectedPharmacy.pharmacy_id } : null);
  const [customPharmacy, setCustomPharmacy] = useState({ name: '', address: '' });
  const [useCustom, setUseCustom] = useState(false);
  const [pharmacyLocked, setPharmacyLocked] = useState(!!preselectedPharmacy); // locked = came from map

  const updateItem = (index, field, value) => {
    setItems(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item));
  };

  const addItem = () => setItems(prev => [...prev, emptyItem()]);

  const removeItem = (index) => {
    if (items.length === 1) return;
    setItems(prev => prev.filter((_, i) => i !== index));
  };

  useEffect(() => {
    items.forEach((item, index) => {
      if (item.drug_name && item.expiry_date && !item.ersLoading) {
        const sig = `${item.drug_name}-${item.expiry_date}-${item.is_antibiotic}`;
        if (item.lastFetchedSignature !== sig) {
          setItems(prev => prev.map((it, i) => i === index ? { ...it, ersLoading: true } : it));
          calculateErs({
            drug_name: item.drug_name,
            expiry_date: item.expiry_date,
            is_antibiotic: item.is_antibiotic
          }).then(res => {
            setItems(prev => prev.map((it, i) => i === index ? { 
              ...it, 
              ersLoading: false, 
              ersData: res.ers_data,
              lastFetchedSignature: sig 
            } : it));
          }).catch(() => {
            setItems(prev => prev.map((it, i) => i === index ? { ...it, ersLoading: false, lastFetchedSignature: sig } : it));
          });
        }
      }
    });
  }, [items]);

  const loadCentres = async () => {
    if (centresLoaded) return;
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(async (pos) => {
        try {
          const bins = await getNearestBins(pos.coords.latitude, pos.coords.longitude);
          setCentres(bins);
        } catch {}
        setCentresLoaded(true);
      }, () => setCentresLoaded(true));
    } else {
      setCentresLoaded(true);
    }
  };

  const goToStep2 = () => {
    const valid = items.every(i => i.drug_name.trim().length > 0 && i.expiry_date.trim().length > 0);
    if (!valid) { alert('Please enter a medicine name and expiry date for each item.'); return; }
    loadCentres();
    setStep(2);
  };

  const submitBundle = async () => {
    const pharmacy = useCustom
      ? { id: `custom-${customPharmacy.name.toLowerCase().replace(/\s+/g, '-')}`, name: customPharmacy.name, address: customPharmacy.address }
      : { id: selectedCentre?.pharmacy_id || 'pharmacy-001', name: selectedCentre?.name || 'Unknown', address: selectedCentre?.address || '' };

    if (!pharmacy.name.trim()) { alert('Please select or enter a pharmacy.'); return; }

    setLoading(true);
    try {
      const payload = {
        device_id: deviceId,
        district: district,
        items: items.map(i => ({
          drug_name: i.drug_name,
          medicine_type: i.medicine_type,
          quantity: i.quantity,
          expiry_date: i.expiry_date || null,
          is_antibiotic: i.is_antibiotic,
        })),
        pharmacy_id: pharmacy.id,
        pharmacy_name: pharmacy.name,
        pharmacy_address: pharmacy.address,
      };
      const res = await createTakeBackBundle(payload);
      setResult(res);
      setStep(3);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  };

  const totalPoints = items.reduce((sum, i) => sum + (i.is_antibiotic ? 70 : 50), 0);

  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '10px',
    border: '1.5px solid var(--border-primary)',
    background: 'var(--bg-secondary)',
    color: 'var(--text-primary)',
    fontSize: '14px',
    outline: 'none',
    boxSizing: 'border-box',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '12px',
    fontWeight: '600',
    color: 'var(--text-tertiary)',
    marginBottom: '6px',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  };

  return (
    <div className="page pb-24" style={{ maxWidth: '480px', margin: '0 auto' }}>

      {/* Show loading tips if submitting */}
      {loading && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 50, background: 'var(--bg-primary)', overflowY: 'auto' }}>
          <LoadingTips district={district} title="Submitting Request..." />
        </div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <button
          onClick={() => step > 1 ? setStep(step - 1) : navigate(-1)}
          style={{
            width: '36px', height: '36px', borderRadius: '10px',
            border: '1.5px solid var(--border-primary)',
            background: 'var(--bg-card)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', flexShrink: 0,
          }}
        >
          <Icons.ChevronLeft style={{ width: '18px', height: '18px', color: 'var(--text-secondary)' }} />
        </button>
        <div>
          <h1 style={{ fontSize: '17px', fontWeight: '700', color: 'var(--text-primary)', margin: 0 }}>
            {step === 1 ? 'Add Medicines' : step === 2 ? 'Choose Pharmacy' : 'Request Submitted'}
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', margin: 0 }}>
            {step === 1 ? 'Step 1 of 2' : step === 2 ? 'Step 2 of 2' : 'Pending pharmacy approval'}
          </p>
        </div>
      </div>

      {/* Step indicator */}
      {step < 3 && (
        <div style={{ display: 'flex', gap: '6px', marginBottom: '20px' }}>
          {[1, 2].map(s => (
            <div key={s} style={{
              flex: 1, height: '3px', borderRadius: '4px',
              background: s <= step ? 'var(--accent)' : 'var(--bg-tertiary)',
              transition: 'background 0.3s ease',
            }} />
          ))}
        </div>
      )}

      {/* ── STEP 1: Bundle Builder ── */}
      {step === 1 && (
        <div>
          {items.map((item, index) => (
            <div key={index} style={{
              background: 'var(--bg-card)',
              border: '1.5px solid var(--border-primary)',
              borderRadius: '14px',
              padding: '16px',
              marginBottom: '12px',
            }}>
              {/* Item header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-secondary)' }}>
                  Medicine {index + 1}
                </span>
                {items.length > 1 && (
                  <button
                    onClick={() => removeItem(index)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: '#ef4444', fontSize: '12px', fontWeight: '600',
                      padding: '2px 6px',
                    }}
                  >
                    Remove
                  </button>
                )}
              </div>

              {/* Drug name */}
              <div style={{ marginBottom: '12px' }}>
                <label style={labelStyle}>Medicine Name</label>
                <DrugSearchInput
                  value={item.drug_name}
                  onChange={(val) => updateItem(index, 'drug_name', val)}
                  onSelect={(s) => {
                    updateItem(index, 'drug_name', s.name);
                    updateItem(index, 'is_antibiotic', s.is_antibiotic);
                  }}
                />
              </div>

              {/* Medicine type */}
              <div style={{ marginBottom: '12px' }}>
                <label style={labelStyle}>Type</label>
                <MedicineTypeSelector
                  value={item.medicine_type}
                  onChange={(val) => updateItem(index, 'medicine_type', val)}
                />
              </div>

              {/* Quantity + Expiry row */}
              <div style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={item.quantity}
                    onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                    style={inputStyle}
                  />
                </div>
                <div style={{ flex: 2 }}>
                  <label style={labelStyle}>Expiry Date</label>
                  <input
                    type="month"
                    value={item.expiry_date}
                    onChange={(e) => updateItem(index, 'expiry_date', e.target.value)}
                    style={inputStyle}
                  />
                </div>
              </div>

              {/* Antibiotic toggle and ER Score */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
                  <div
                    onClick={() => updateItem(index, 'is_antibiotic', !item.is_antibiotic)}
                    style={{
                      width: '42px', height: '24px', borderRadius: '12px',
                      background: item.is_antibiotic ? 'var(--accent)' : 'var(--bg-tertiary)',
                      position: 'relative', transition: 'background 0.2s', flexShrink: 0,
                    }}
                  >
                    <div style={{
                      position: 'absolute', top: '2px',
                      left: item.is_antibiotic ? '20px' : '2px',
                      width: '20px', height: '20px', borderRadius: '50%',
                      background: 'white', transition: 'left 0.2s',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                    }} />
                  </div>
                  <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: '500' }}>
                    This is an antibiotic
                    {item.is_antibiotic && (
                      <span style={{ color: 'var(--accent)', marginLeft: '4px', fontSize: '11px' }}>
                        (+70 pts)
                      </span>
                    )}
                  </span>
                </label>

                {item.ersData && (
                  <div className="animate-fade-in" style={{ 
                    display: 'flex', alignItems: 'center', gap: '6px', 
                    background: 'var(--bg-secondary)', padding: '6px 10px', 
                    borderRadius: '8px', border: `1.5px solid ${item.ersData.risk_color}30`
                  }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: item.ersData.risk_color, boxShadow: `0 0 8px ${item.ersData.risk_color}80` }} />
                    <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-primary)' }}>
                      Risk: {item.ersData.risk_level}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Add another medicine */}
          <button
            onClick={addItem}
            style={{
              width: '100%', padding: '12px',
              borderRadius: '12px',
              border: '1.5px dashed var(--border-primary)',
              background: 'transparent',
              color: 'var(--accent)',
              fontWeight: '600',
              fontSize: '14px',
              cursor: 'pointer',
              marginBottom: '16px',
            }}
          >
            + Add Another Medicine
          </button>

          {/* Points preview */}
          <div style={{
            padding: '12px 16px',
            borderRadius: '10px',
            background: 'var(--accent-bg)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
          }}>
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              Points you'll earn ({items.length} medicine{items.length > 1 ? 's' : ''})
            </span>
            <span style={{ fontSize: '16px', fontWeight: '700', color: 'var(--accent)' }}>
              +{totalPoints} pts
            </span>
          </div>

          <button
            onClick={goToStep2}
            style={{
              width: '100%', padding: '14px',
              borderRadius: '12px',
              background: 'var(--accent)',
              color: 'white',
              fontWeight: '700',
              fontSize: '15px',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            {pharmacyLocked ? 'Review & Submit' : 'Next: Choose Pharmacy'}
          </button>
        </div>
      )}

      {/* STEP 2: Pharmacy Selection */}
      {step === 2 && (
        <div>
          {pharmacyLocked ? (
            <div style={{ background: 'var(--bg-card)', border: '1.5px solid var(--accent)', borderRadius: '14px', padding: '16px', marginBottom: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Selected Pharmacy</span>
                <span style={{ fontSize: '11px', fontWeight: '700', padding: '2px 8px', borderRadius: '20px', background: 'rgba(22,163,74,0.12)', color: '#16a34a' }}>Confirmed</span>
              </div>
              <p style={{ fontSize: '15px', fontWeight: '700', color: 'var(--text-primary)', margin: '4px 0 2px' }}>{preselectedPharmacy?.name}</p>
              {preselectedPharmacy?.address && preselectedPharmacy.address !== 'Address not listed' && (
                <p style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>{preselectedPharmacy.address}</p>
              )}
              <button onClick={() => setPharmacyLocked(false)} style={{ marginTop: '10px', background: 'none', border: 'none', color: 'var(--text-tertiary)', fontSize: '12px', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}>
                Change pharmacy
              </button>
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', marginBottom: '16px', background: 'var(--bg-secondary)', borderRadius: '10px', padding: '4px' }}>
                {['Nearby', 'Enter Manually'].map((tab, i) => (
                  <button key={tab} onClick={() => setUseCustom(i === 1)} style={{ flex: 1, padding: '9px', borderRadius: '8px', border: 'none', background: useCustom === (i === 1) ? 'var(--bg-card)' : 'transparent', color: 'var(--text-primary)', fontWeight: useCustom === (i === 1) ? '700' : '500', fontSize: '13px', cursor: 'pointer', transition: 'all 0.15s' }}>
                    {tab}
                  </button>
                ))}
              </div>
              {!useCustom && (
                <div>
                  {!centresLoaded ? (
                    <p style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '13px', padding: '24px 0' }}>Finding nearby centres...</p>
                  ) : centres.length === 0 ? (
                    <p style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: '13px', padding: '24px 0' }}>No nearby centres found. Please enter manually.</p>
                  ) : centres.map((c) => (
                    <label key={c.id} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '14px', borderRadius: '12px', border: `1.5px solid ${selectedCentre?.id === c.id ? 'var(--accent)' : 'var(--border-primary)'}`, background: selectedCentre?.id === c.id ? 'var(--accent-bg)' : 'var(--bg-card)', marginBottom: '10px', cursor: 'pointer', transition: 'all 0.15s' }}>
                      <input type="radio" name="centre" checked={selectedCentre?.id === c.id} onChange={() => setSelectedCentre(c)} style={{ marginTop: '2px', accentColor: 'var(--accent)' }} />
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: '600', fontSize: '14px', color: 'var(--text-primary)' }}>{c.name}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '2px' }}>{c.address}</div>
                        <div style={{ fontSize: '12px', color: 'var(--accent)', marginTop: '4px', fontWeight: '600' }}>{c.distance_km} km away</div>
                      </div>
                    </label>
                  ))}
                </div>
              )}
              {useCustom && (
                <div style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border-primary)', borderRadius: '14px', padding: '16px', marginBottom: '12px' }}>
                  <div style={{ marginBottom: '12px' }}>
                    <label style={labelStyle}>Pharmacy Name</label>
                    <input type="text" value={customPharmacy.name} onChange={(e) => setCustomPharmacy(p => ({ ...p, name: e.target.value }))} placeholder="e.g. City Medical Store" style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Address (optional)</label>
                    <input type="text" value={customPharmacy.address} onChange={(e) => setCustomPharmacy(p => ({ ...p, address: e.target.value }))} placeholder="e.g. MG Road, Pune" style={inputStyle} />
                  </div>
                </div>
              )}
            </div>
          )}

          <div style={{ background: 'var(--bg-card)', border: '1.5px solid var(--border-primary)', borderRadius: '12px', padding: '14px', marginBottom: '16px', marginTop: '8px' }}>
            <p style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>
              Your Bundle ({items.length} medicine{items.length > 1 ? 's' : ''})
            </p>
            {items.map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0', borderBottom: i < items.length - 1 ? '1px solid var(--border-subtle)' : 'none' }}>
                <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{item.drug_name} ({item.medicine_type}) x{item.quantity}</span>
                <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--accent)' }}>+{item.is_antibiotic ? 70 : 50} pts</span>
              </div>
            ))}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border-primary)' }}>
              <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)' }}>Total (pending approval)</span>
              <span style={{ fontSize: '16px', fontWeight: '700', color: 'var(--accent)' }}>+{totalPoints} pts</span>
            </div>
          </div>

          <div style={{ padding: '10px 14px', borderRadius: '10px', background: 'rgba(251,191,36,0.1)', border: '1px solid rgba(251,191,36,0.3)', marginBottom: '16px' }}>
            <p style={{ fontSize: '12px', color: '#d97706', margin: 0 }}>Points credited only after pharmacist verifies and shares OTP.</p>
          </div>

          <button onClick={submitBundle} disabled={loading || (pharmacyLocked ? false : useCustom ? !customPharmacy.name.trim() : !selectedCentre)} style={{ width: '100%', padding: '14px', borderRadius: '12px', background: loading ? 'var(--bg-tertiary)' : 'var(--accent)', color: loading ? 'var(--text-tertiary)' : 'white', fontWeight: '700', fontSize: '15px', border: 'none', cursor: loading ? 'not-allowed' : 'pointer' }}>
            {loading ? 'Submitting...' : 'Submit Take-Back Request'}
          </button>
        </div>
      )}

      {/* ── STEP 3: Success / Pending ── */}
      {step === 3 && (
        <div style={{ textAlign: 'center', paddingTop: '20px' }}>
          <div style={{
            width: '72px', height: '72px', borderRadius: '50%',
            background: 'rgba(251,191,36,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 20px',
          }}>
            <span style={{ fontSize: '36px' }}>⏳</span>
          </div>

          <h2 style={{ fontSize: '20px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '8px' }}>
            Request Submitted!
          </h2>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '24px', lineHeight: '1.5' }}>
            Visit the pharmacy with your medicines. The pharmacist will verify and share an OTP with you.
          </p>

          <div style={{
            background: 'var(--bg-card)',
            border: '1.5px solid var(--border-primary)',
            borderRadius: '14px',
            padding: '16px',
            marginBottom: '16px',
            textAlign: 'left',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Pending Points</span>
              <span style={{ fontSize: '18px', fontWeight: '700', color: 'var(--accent)' }}>+{totalPoints} pts</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Status</span>
              <span style={{ fontSize: '12px', fontWeight: '700', padding: '3px 10px', borderRadius: '20px', background: 'rgba(251,191,36,0.15)', color: '#d97706' }}>
                Pending Approval
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Medicines</span>
              <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                {items.length} item{items.length > 1 ? 's' : ''}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Pharmacy</span>
              <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', textAlign: 'right', maxWidth: '60%' }}>
                {useCustom ? customPharmacy.name : selectedCentre?.name}
              </span>
            </div>
            {/* Pharmacy ID — needed for pharmacist to log in */}
            <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
              <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginBottom: '4px' }}>Pharmacy Login ID (share with pharmacist):</p>
              <div style={{ padding: '7px 10px', borderRadius: '8px', background: 'var(--bg-secondary)', fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent)', wordBreak: 'break-all' }}>
                {useCustom
                  ? `custom-${customPharmacy.name.toLowerCase().replace(/\s+/g, '-')}`
                  : selectedCentre?.pharmacy_id}
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '4px' }}>PIN: <strong>0000</strong> (if newly registered)</p>
            </div>
          </div>

          {/* ERS Summary Card */}
          {(result?.bundle_ers_score > 0 || result?.bundle_risk_level) && (
            <div style={{
              background: 'var(--bg-card)',
              border: `1.5px solid ${result?.bundle_risk_level === 'Critical Risk' ? '#7f1d1d' : result?.bundle_risk_level === 'High Risk' ? 'rgba(239,68,68,0.4)' : result?.bundle_risk_level === 'Moderate Risk' ? 'rgba(245,158,11,0.4)' : 'rgba(34,197,94,0.4)'}`,
              borderRadius: '12px', padding: '14px', marginBottom: '16px', textAlign: 'left',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '14px' }}>🌿</span>
                  <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Environmental Risk Score</span>
                </div>
                <span style={{
                  fontSize: '11px', fontWeight: '800', padding: '3px 10px', borderRadius: '20px',
                  background: result?.bundle_risk_level === 'Critical Risk' ? 'rgba(127,29,29,0.2)' : result?.bundle_risk_level === 'High Risk' ? 'rgba(239,68,68,0.12)' : result?.bundle_risk_level === 'Moderate Risk' ? 'rgba(245,158,11,0.12)' : 'rgba(34,197,94,0.12)',
                  color: result?.bundle_risk_level === 'Critical Risk' ? '#fca5a5' : result?.bundle_risk_level === 'High Risk' ? '#ef4444' : result?.bundle_risk_level === 'Moderate Risk' ? '#f59e0b' : '#22c55e',
                }}>
                  {result?.bundle_risk_level || 'Low Impact'}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <div style={{ flex: 1, height: '6px', borderRadius: '6px', background: 'var(--bg-tertiary)', overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', borderRadius: '6px',
                    width: `${((result?.bundle_ers_score || 0) / 10) * 100}%`,
                    background: result?.bundle_risk_level === 'Critical Risk' ? '#7f1d1d' : result?.bundle_risk_level === 'High Risk' ? '#ef4444' : result?.bundle_risk_level === 'Moderate Risk' ? '#f59e0b' : '#22c55e',
                    transition: 'width 0.8s ease',
                  }} />
                </div>
                <span style={{ fontSize: '13px', fontWeight: '800', color: 'var(--text-primary)', minWidth: '35px' }}>
                  {result?.bundle_ers_score || 0}/10
                </span>
              </div>
              <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', lineHeight: '1.5', margin: 0 }}>
                Safe pharmacy disposal prevents antibiotics and pharmaceuticals from contaminating groundwater and contributing to AMR spread.
              </p>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              onClick={() => navigate('/my-requests')}
              style={{
                width: '100%', padding: '13px',
                borderRadius: '12px',
                background: 'var(--accent)',
                color: 'white', fontWeight: '700', fontSize: '14px',
                border: 'none', cursor: 'pointer',
              }}
            >
              View My Requests
            </button>
            <button
              onClick={() => navigate('/')}
              style={{
                width: '100%', padding: '13px',
                borderRadius: '12px',
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)', fontWeight: '600', fontSize: '14px',
                border: '1.5px solid var(--border-primary)', cursor: 'pointer',
              }}
            >
              Back to Home
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
