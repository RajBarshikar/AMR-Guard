import { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import Icons from '../components/Icons';

// ── Leaflet default icon fix ────────────────────────────────────────────────
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// ── Custom Icons ─────────────────────────────────────────────────────────────
const userIcon = new L.DivIcon({
  html: `<div style="width:18px;height:18px;border-radius:50%;background:#0d9488;border:3px solid white;box-shadow:0 0 0 4px rgba(13,148,136,0.25),0 2px 6px rgba(0,0,0,0.25);"></div>`,
  className: '', iconSize: [18, 18], iconAnchor: [9, 9],
});

// 🟢 Green: Verified SafeDrop Partner
const verifiedIcon = new L.DivIcon({
  html: `<div style="width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#16a34a,#22c55e);display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(34,197,94,0.4);border:2px solid white;">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
      <path d="M12 6v4M14 14h-4M14 18h-4M14 8h-4"/><rect x="6" y="2" width="12" height="20" rx="2"/>
    </svg>
  </div>`,
  className: '', iconSize: [34, 34], iconAnchor: [17, 17],
});

// 🔵 Blue: Nearby Pharmacy from Overpass
const pharmacyIcon = new L.DivIcon({
  html: `<div style="width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#3b82f6,#60a5fa);display:flex;align-items:center;justify-content:center;box-shadow:0 3px 8px rgba(59,130,246,0.35);border:2px solid white;">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
    </svg>
  </div>`,
  className: '', iconSize: [30, 30], iconAnchor: [15, 15],
});

// ── Hardcoded Verified Partners (green) ─────────────────────────────────────
// These represent the full product vision: confirmed SafeDrop partnerships
const VERIFIED_PARTNERS = [
  {
    id: 'vp1',
    name: 'SafeDrop Partner — Apollo Pharmacy',
    address: 'Shop 4, MG Road, Near City Hospital',
    phone: '+91-22-4000-1111',
    type: 'verified_partner',
    accepts: ['antibiotics', 'general_medication', 'syringes'],
    offset: [0.004, 0.003],
  },
  {
    id: 'vp2',
    name: 'SafeDrop Partner — District Health Center',
    address: '45, Station Road, Opp. Railway Station',
    phone: '+91-22-2500-4567',
    type: 'verified_partner',
    accepts: ['antibiotics', 'controlled_substances', 'biomedical_waste'],
    offset: [-0.005, 0.007],
  },
  {
    id: 'vp3',
    name: 'AMR-Guard Biomedical Waste Hub',
    address: 'Civil Lines, District Hospital Complex',
    phone: '+91-22-2501-8800',
    type: 'biomedical',
    accepts: ['biomedical_waste', 'sharps', 'antibiotics'],
    offset: [0.007, -0.004],
  },
];

// ── Radius options ───────────────────────────────────────────────────────────
const RADIUS_OPTIONS = [
  { label: '2 km', value: 2000 },
  { label: '5 km', value: 5000 },
  { label: '10 km', value: 10000 },
];

// ── Haversine distance calc ──────────────────────────────────────────────────
function getDistKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return +(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))).toFixed(2);
}

// ── FlyTo helper ─────────────────────────────────────────────────────────────
function FlyToUser({ position }) {
  const map = useMap();
  useEffect(() => {
    if (position) map.flyTo(position, 14, { duration: 1.5 });
  }, [position, map]);
  return null;
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function MapView() {
  const { t } = useLanguage();
  const { isDark } = useTheme();
  const navigate = useNavigate();

  const [userPos, setUserPos]           = useState(null);
  const [pharmacies, setPharmacies]     = useState([]);
  const [verifiedPts, setVerifiedPts]   = useState([]);
  const [loading, setLoading]           = useState(true);
  const [loadingPharm, setLoadingPharm] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [radius, setRadius]             = useState(5000);
  const [error, setError]               = useState(null);

  // ── Fetch from Overpass ────────────────────────────────────────────────────
  const fetchPharmacies = useCallback(async (lat, lng, radiusM) => {
    setLoadingPharm(true);
    setError(null);
    try {
      const query = `[out:json][timeout:20];node["amenity"="pharmacy"](around:${radiusM},${lat},${lng});out body;`;
      const res = await fetch('https://overpass-api.de/api/interpreter', {
        method: 'POST',
        body: query,
      });
      if (!res.ok) throw new Error(`Overpass HTTP ${res.status}`);
      const data = await res.json();
      const results = (data.elements || [])
        .filter(e => e.lat && e.lon)
        .map(e => ({
          id: `osm-${e.id}`,
          name: e.tags?.name || 'Pharmacy',
          address: [
            e.tags?.['addr:housenumber'],
            e.tags?.['addr:street'],
            e.tags?.['addr:city'],
          ].filter(Boolean).join(', ') || 'Address not listed',
          phone: e.tags?.phone || e.tags?.['contact:phone'] || null,
          lat: e.lat,
          lng: e.lon,
          type: 'osm_pharmacy',
          distance_km: getDistKm(lat, lng, e.lat, e.lon),
        }))
        .sort((a, b) => a.distance_km - b.distance_km)
        .slice(0, 15);
      setPharmacies(results);
    } catch (e) {
      console.error('[Overpass] Error:', e);
      setError('Could not load nearby pharmacies. Check your connection.');
    } finally {
      setLoadingPharm(false);
    }
  }, []);

  // ── Geolocation on mount ───────────────────────────────────────────────────
  useEffect(() => {
    const fallback = [19.076, 72.877]; // Mumbai
    if (!navigator.geolocation) {
      setUserPos(fallback);
      fetchPharmacies(fallback[0], fallback[1], radius);
      setLoading(false);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords: { latitude: lat, longitude: lng } }) => {
        setUserPos([lat, lng]);
        // Attach verified partners offset from user position
        setVerifiedPts(
          VERIFIED_PARTNERS.map(vp => ({
            ...vp,
            lat: lat + vp.offset[0],
            lng: lng + vp.offset[1],
            distance_km: getDistKm(lat, lng, lat + vp.offset[0], lng + vp.offset[1]),
          }))
        );
        fetchPharmacies(lat, lng, radius);
        setLoading(false);
      },
      () => {
        setUserPos(fallback);
        setVerifiedPts(
          VERIFIED_PARTNERS.map(vp => ({
            ...vp,
            lat: fallback[0] + vp.offset[0],
            lng: fallback[1] + vp.offset[1],
            distance_km: getDistKm(fallback[0], fallback[1], fallback[0] + vp.offset[0], fallback[1] + vp.offset[1]),
          }))
        );
        fetchPharmacies(fallback[0], fallback[1], radius);
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Radius change refetch ─────────────────────────────────────────────────
  const handleRadiusChange = (newRadius) => {
    setRadius(newRadius);
    if (userPos) fetchPharmacies(userPos[0], userPos[1], newRadius);
  };

  const tileUrl = isDark
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

  const totalCount = pharmacies.length + verifiedPts.length;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-5 pt-7 pb-4">
        <div className="flex items-center gap-3.5">
          <div className="icon-box w-12 h-12 rounded-2xl gradient-primary" style={{ boxShadow: 'var(--shadow-accent)' }}>
            <Icons.MapPin className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h1 className="text-lg font-bold animate-fade-in" style={{ color: 'var(--text-primary)' }}>
              {t('nearest_centres')}
            </h1>
            <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
              {loading ? t('locating') : loadingPharm ? 'Fetching pharmacies…' : `${totalCount} locations found`}
            </p>
          </div>
        </div>

        {/* Radius Toggle */}
        {!loading && (
          <div className="flex gap-2 mt-4">
            {RADIUS_OPTIONS.map(({ label, value }) => (
              <button
                key={value}
                onClick={() => handleRadiusChange(value)}
                className={`flex-1 py-2 rounded-xl text-[12px] font-semibold transition-all duration-200 ${
                  radius === value
                    ? 'gradient-primary text-white'
                    : 'card'
                }`}
                style={radius !== value ? { color: 'var(--text-secondary)' } : { boxShadow: 'var(--shadow-accent)' }}
              >
                {label}
              </button>
            ))}
          </div>
        )}

        {/* Legend */}
        {!loading && (
          <div className="flex items-center gap-4 mt-3">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span className="text-[10px] font-medium" style={{ color: 'var(--text-tertiary)' }}>Verified SafeDrop</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-blue-500" />
              <span className="text-[10px] font-medium" style={{ color: 'var(--text-tertiary)' }}>Nearby Pharmacy</span>
            </div>
          </div>
        )}
      </div>

      {/* Map */}
      <div className="px-5 pb-3" style={{ height: '45%', minHeight: '240px' }}>
        {loading ? (
          <div className="h-full flex flex-col items-center justify-center rounded-2xl card">
            <div className="w-10 h-10 rounded-full border-[3px] border-t-transparent animate-spin mb-4" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
            <p className="text-[13px]" style={{ color: 'var(--accent)' }}>{t('loading_map')}</p>
          </div>
        ) : (
          <div className="h-full rounded-2xl overflow-hidden relative" style={{ boxShadow: 'var(--shadow-md)', border: '1px solid var(--border-primary)' }}>
            <MapContainer center={userPos || [19.076, 72.877]} zoom={14} style={{ height: '100%', width: '100%' }} zoomControl={false}>
              <TileLayer attribution='&copy; <a href="https://openstreetmap.org">OSM</a> contributors' url={tileUrl} />
              {userPos && <FlyToUser position={userPos} />}
              {userPos && (
                <>
                  <Marker position={userPos} icon={userIcon}>
                    <Popup><b>{t('your_location')}</b></Popup>
                  </Marker>
                  <Circle center={userPos} radius={radius} pathOptions={{ color: '#0d9488', fillColor: '#0d9488', fillOpacity: 0.04, weight: 1 }} />
                </>
              )}

              {/* 🟢 Verified Partners */}
              {verifiedPts.map(vp => (
                <Marker key={vp.id} position={[vp.lat, vp.lng]} icon={verifiedIcon} eventHandlers={{ click: () => setSelectedItem({ ...vp, isVerified: true }) }}>
                  <Popup>
                    <div className="min-w-[180px]">
                      <div className="flex items-center gap-1 mb-1">
                        <span style={{ color: '#16a34a', fontSize: 10, fontWeight: 700 }}>✓ VERIFIED SAFEDROP</span>
                      </div>
                      <p className="font-bold text-sm">{vp.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{vp.address}</p>
                      <p className="text-xs font-semibold mt-1" style={{ color: '#16a34a' }}>{vp.distance_km} km away</p>
                    </div>
                  </Popup>
                </Marker>
              ))}

              {/* 🔵 OSM Pharmacies */}
              {pharmacies.map(p => (
                <Marker key={p.id} position={[p.lat, p.lng]} icon={pharmacyIcon} eventHandlers={{ click: () => setSelectedItem({ ...p, isVerified: false }) }}>
                  <Popup>
                    <div className="min-w-[160px]">
                      <p className="font-bold text-sm">{p.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{p.address}</p>
                      {p.phone && <p className="text-xs mt-1">{p.phone}</p>}
                      <p className="text-xs font-semibold mt-1" style={{ color: '#3b82f6' }}>{p.distance_km} km away</p>
                      <p className="text-[10px] text-gray-400 mt-1 italic">Call to confirm take-back</p>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>

            {/* Overpass loading overlay */}
            {loadingPharm && (
              <div className="absolute inset-0 bg-black/20 flex items-center justify-center z-[999] rounded-2xl backdrop-blur-sm">
                <div className="bg-white dark:bg-gray-800 rounded-2xl px-5 py-4 flex items-center gap-3 shadow-xl">
                  <div className="w-5 h-5 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: '#3b82f6', borderTopColor: 'transparent' }} />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Fetching live pharmacies…</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mx-5 mb-2 px-4 py-3 rounded-xl text-sm flex items-center gap-2"
             style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#ef4444' }}>
          <Icons.AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Centre Cards List */}
      <div className="flex-1 px-5 pb-6 space-y-3 overflow-y-auto mt-1">
        {loading ? (
          <>{[1, 2, 3].map(i => <div key={i} className="card p-5"><div className="skeleton h-14 rounded" /></div>)}</>
        ) : (
          <>
            {/* Verified Partners first */}
            {verifiedPts.map(vp => (
              <div key={vp.id}
                   onClick={() => setSelectedItem({ ...vp, isVerified: true })}
                   className={`card p-4 cursor-pointer transition-all duration-200 ${selectedItem?.id === vp.id ? 'ring-2 ring-green-500' : ''}`}>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                       style={{ background: 'rgba(34,197,94,0.1)', color: '#16a34a' }}>
                    <Icons.ShieldCheck className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 justify-between">
                      <p className="font-semibold text-[13px] truncate" style={{ color: 'var(--text-primary)' }}>{vp.name}</p>
                      <span className="text-[11px] font-bold shrink-0 text-green-600">{vp.distance_km} km</span>
                    </div>
                    <p className="text-[11px] mt-0.5 truncate" style={{ color: 'var(--text-tertiary)' }}>{vp.address}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-green-500/10 text-green-600">✓ Verified SafeDrop</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 mt-3">
                  <button
                    onClick={(e) => { e.stopPropagation(); navigate('/takeback', { state: { pharmacy: { id: vp.id, name: vp.name, address: vp.address, pharmacy_id: vp.id } } }); }}
                    className="flex-1 py-2.5 rounded-xl text-[12px] font-bold flex items-center justify-center gap-1.5 text-white"
                    style={{ background: 'linear-gradient(135deg,#16a34a,#22c55e)' }}
                  >
                    <Icons.Recycle className="w-3.5 h-3.5" />
                    Request Take-Back
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); window.open(`https://www.google.com/maps/dir/?api=1&destination=${vp.lat},${vp.lng}`, '_blank'); }}
                    className="flex-1 py-2.5 rounded-xl card text-[12px] font-semibold flex items-center justify-center gap-1.5"
                    style={{ color: 'var(--accent)' }}
                  >
                    <Icons.Navigation className="w-3.5 h-3.5" />
                    Directions
                  </button>
                </div>
              </div>
            ))}

            {/* OSM Pharmacies */}
            {loadingPharm ? (
              <div className="card p-5 flex items-center gap-3">
                <div className="w-5 h-5 rounded-full border-2 border-t-transparent animate-spin shrink-0" style={{ borderColor: '#3b82f6', borderTopColor: 'transparent' }} />
                <span className="text-[13px]" style={{ color: 'var(--text-secondary)' }}>Searching nearby pharmacies via OpenStreetMap…</span>
              </div>
            ) : pharmacies.length === 0 ? (
              <div className="card p-5 text-center">
                <p className="text-[13px]" style={{ color: 'var(--text-tertiary)' }}>No pharmacies found in this area. Try expanding the radius.</p>
              </div>
            ) : (
              pharmacies.map(p => (
                <div key={p.id}
                     onClick={() => setSelectedItem({ ...p, isVerified: false })}
                     className={`card p-4 cursor-pointer transition-all duration-200 ${selectedItem?.id === p.id ? 'ring-2 ring-blue-400' : ''}`}>
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                         style={{ background: 'rgba(59,130,246,0.08)', color: '#3b82f6' }}>
                      <Icons.Hospital className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="font-semibold text-[13px] truncate" style={{ color: 'var(--text-primary)' }}>{p.name}</p>
                        <span className="text-[11px] font-bold shrink-0 ml-2" style={{ color: '#3b82f6' }}>{p.distance_km} km</span>
                      </div>
                      <p className="text-[11px] mt-0.5 truncate" style={{ color: 'var(--text-tertiary)' }}>{p.address}</p>
                      {p.phone && (
                        <p className="text-[11px] mt-1 font-medium" style={{ color: 'var(--text-secondary)' }}>{p.phone}</p>
                      )}
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600 font-medium">OpenStreetMap</span>
                        <span className="text-[10px] text-gray-400 italic">Call to confirm take-back</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate('/takeback', { state: { pharmacy: { id: p.id, name: p.name, address: p.address, pharmacy_id: p.id } } }); }}
                      className="flex-1 py-2.5 rounded-xl text-[12px] font-bold flex items-center justify-center gap-1.5 text-white"
                      style={{ background: 'linear-gradient(135deg,#16a34a,#22c55e)' }}
                    >
                      <Icons.Recycle className="w-3.5 h-3.5" />
                      Take-Back
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); window.open(`https://www.google.com/maps/dir/?api=1&destination=${p.lat},${p.lng}`, '_blank'); }}
                      className="flex-1 py-2.5 rounded-xl card text-[12px] font-semibold flex items-center justify-center gap-1.5"
                      style={{ color: 'var(--accent)' }}
                    >
                      <Icons.Navigation className="w-3.5 h-3.5" />
                      Directions
                    </button>
                  </div>
                </div>
              ))
            )}
          </>
        )}
      </div>
    </div>
  );
}
