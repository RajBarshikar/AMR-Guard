import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { pharmacyLogin, seedPharmacies } from '../../utils/api';

const DEMO_PHARMACIES = [
  { id: 'pharmacy-001', name: 'MedPlus Pune', pin: '1234' },
  { id: 'pharmacy-002', name: 'Apollo Mumbai', pin: '5678' },
  { id: 'pharmacy-003', name: 'Jan Aushadhi', pin: '4321' },
];

export default function PharmacyLogin() {
  const navigate = useNavigate();
  const [pharmacyId, setPharmacyId] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [seeding, setSeeding] = useState(false);
  const [seeded, setSeeded] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!pharmacyId.trim()) { setError('Enter a Pharmacy ID'); return; }
    if (pin.length < 4) { setError('PIN must be at least 4 digits'); return; }
    setLoading(true);
    setError('');
    try {
      const res = await pharmacyLogin(pharmacyId.trim(), pin);
      localStorage.setItem('amr-pharmacy-session', JSON.stringify({
        token: res.token,
        pharmacy_id: res.pharmacy_id,
        pharmacy_name: res.pharmacy_name,
        expires_at: Date.now() + 86400 * 1000,
      }));
      navigate('/pharmacy/dashboard');
    } catch (e) {
      setError(e.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await seedPharmacies();
      setSeeded(true);
      setTimeout(() => setSeeded(false), 3000);
    } catch (e) {
      setError('Seed failed: ' + e.message);
    } finally {
      setSeeding(false);
    }
  };

  const inputStyle = {
    width: '100%', padding: '14px 16px', borderRadius: '12px',
    background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
    color: 'white', fontSize: '14px', outline: 'none', boxSizing: 'border-box',
  };
  const labelStyle = {
    color: 'rgba(255,255,255,0.7)', fontSize: '12px', fontWeight: '600',
    letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', marginBottom: '8px',
  };

  const canSubmit = pin.length >= 4 && pharmacyId.trim().length > 0;

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'Inter', sans-serif", padding: '20px' }}>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />

      <div style={{ width: '100%', maxWidth: '420px' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '36px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '18px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px', boxShadow: '0 0 40px rgba(99,102,241,0.4)' }}>
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </div>
          <h1 style={{ color: 'white', fontSize: '24px', fontWeight: '800', margin: '0 0 4px' }}>SafeDrop Portal</h1>
          <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: '13px', margin: 0 }}>Pharmacy Take-Back Management</p>
        </div>

        {/* Card */}
        <div style={{ background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(20px)', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)', padding: '28px' }}>
          <form onSubmit={handleLogin}>

            {/* Pharmacy ID */}
            <div style={{ marginBottom: '16px' }}>
              <label style={labelStyle}>Pharmacy ID</label>
              <input
                type="text"
                value={pharmacyId}
                onChange={e => { setPharmacyId(e.target.value); setError(''); }}
                placeholder="e.g. pharmacy-001 or osm-12345678"
                style={inputStyle}
                autoFocus
              />
              {/* Quick-select demo pharmacies */}
              <div style={{ display: 'flex', gap: '6px', marginTop: '8px', flexWrap: 'wrap' }}>
                {DEMO_PHARMACIES.map(p => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => { setPharmacyId(p.id); setPin(p.pin); setError(''); }}
                    style={{
                      padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '600', cursor: 'pointer',
                      background: pharmacyId === p.id ? 'rgba(99,102,241,0.3)' : 'rgba(255,255,255,0.06)',
                      border: `1px solid ${pharmacyId === p.id ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.1)'}`,
                      color: pharmacyId === p.id ? '#a5b4fc' : 'rgba(255,255,255,0.5)',
                    }}
                  >
                    {p.name}
                  </button>
                ))}
              </div>
            </div>

            {/* PIN */}
            <div style={{ marginBottom: '8px' }}>
              <label style={labelStyle}>PIN</label>
              <input
                type="password"
                maxLength={6}
                value={pin}
                onChange={e => { setPin(e.target.value.replace(/\D/g, '')); setError(''); }}
                placeholder="Enter PIN"
                style={{ ...inputStyle, fontSize: '20px', letterSpacing: '0.4em', textAlign: 'center' }}
              />
            </div>

            {/* Hint */}
            <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '11px', textAlign: 'center', marginBottom: '16px', lineHeight: '1.5' }}>
              Newly registered pharmacies use PIN <strong style={{ color: 'rgba(255,255,255,0.5)' }}>0000</strong>.
              The Pharmacy ID is shown on the user's request confirmation screen.
            </p>

            {error && (
              <div style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '10px', padding: '10px 14px', color: '#f87171', fontSize: '13px', marginBottom: '16px', textAlign: 'center' }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !canSubmit}
              style={{
                width: '100%', padding: '15px', borderRadius: '12px',
                background: canSubmit ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'rgba(255,255,255,0.1)',
                color: 'white', fontWeight: '700', fontSize: '15px', border: 'none',
                cursor: canSubmit ? 'pointer' : 'not-allowed',
                boxShadow: canSubmit ? '0 4px 20px rgba(99,102,241,0.4)' : 'none',
              }}
            >
              {loading ? 'Logging in…' : 'Login to Portal'}
            </button>
          </form>

          <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.08)', textAlign: 'center' }}>
            <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: '11px', marginBottom: '8px' }}>First time? Seed demo pharmacies into Firebase:</p>
            <button
              onClick={handleSeed}
              disabled={seeding}
              style={{ padding: '8px 20px', borderRadius: '8px', background: seeded ? 'rgba(34,197,94,0.2)' : 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: seeded ? '#4ade80' : 'rgba(255,255,255,0.5)', fontSize: '12px', cursor: 'pointer' }}
            >
              {seeding ? 'Seeding…' : seeded ? '✓ Seeded!' : 'Seed Demo Data'}
            </button>
          </div>
        </div>

        <p style={{ textAlign: 'center', color: 'rgba(255,255,255,0.2)', fontSize: '11px', marginTop: '20px' }}>
          AMR-Guard SafeDrop Network · Pharmacist Portal
        </p>
      </div>
    </div>
  );
}
