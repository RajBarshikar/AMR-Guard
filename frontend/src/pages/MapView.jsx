import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { getNearestBins } from '../utils/api';
import Icons from '../components/Icons';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const userIcon = new L.DivIcon({
  html: `<div style="width:18px;height:18px;border-radius:50%;background:#0d9488;border:3px solid white;box-shadow:0 0 0 3px rgba(13,148,136,0.25),0 2px 6px rgba(0,0,0,0.2);"></div>`,
  className: '', iconSize: [18, 18], iconAnchor: [9, 9],
});

const centreIcon = new L.DivIcon({
  html: `<div style="width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#0d9488,#14b8a6);display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.25);border:2px solid white;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M12 6v4M14 14h-4M14 18h-4M14 8h-4"/><rect x="6" y="2" width="12" height="20" rx="2"/></svg></div>`,
  className: '', iconSize: [30, 30], iconAnchor: [15, 15],
});

function FlyToUser({ position }) {
  const map = useMap();
  useEffect(() => { if (position) map.flyTo(position, 15, { duration: 1.5 }); }, [position, map]);
  return null;
}

export default function MapView() {
  const { t } = useLanguage();
  const { isDark } = useTheme();
  const [userPos, setUserPos] = useState(null);
  const [centres, setCentres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCentre, setSelectedCentre] = useState(null);

  useEffect(() => {
    if (!navigator.geolocation) { setLoading(false); return; }
    navigator.geolocation.getCurrentPosition(
      async ({ coords: { latitude: lat, longitude: lng } }) => {
        setUserPos([lat, lng]);
        try { setCentres(await getNearestBins(lat, lng)); } catch {}
        setLoading(false);
      },
      () => {
        const fb = [19.076, 72.877]; setUserPos(fb);
        getNearestBins(fb[0], fb[1]).then(setCentres).catch(() => {});
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }, []);

  const tileUrl = isDark
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="px-5 pt-7 pb-4">
        <div className="flex items-center gap-3.5">
          <div className="icon-box w-12 h-12 rounded-2xl gradient-primary" style={{ boxShadow: 'var(--shadow-accent)' }}>
            <Icons.MapPin className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold animate-fade-in" style={{ color: 'var(--text-primary)' }}>{t('nearest_centres')}</h1>
            <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>
              {loading ? t('locating') : `${centres.length} SafeDrop locations found`}
            </p>
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="flex-1 px-5 pb-3">
        {loading ? (
          <div className="h-full flex flex-col items-center justify-center">
            <div className="w-10 h-10 rounded-full border-[3px] border-t-transparent animate-spin mb-4" style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
            <p className="text-[13px]" style={{ color: 'var(--accent)' }}>{t('loading_map')}</p>
          </div>
        ) : (
          <div className="h-full rounded-2xl overflow-hidden" style={{ boxShadow: 'var(--shadow-md)', border: '1px solid var(--border-primary)' }}>
            <MapContainer center={userPos || [19.076, 72.877]} zoom={14} style={{ height: '100%', width: '100%' }} zoomControl={false}>
              <TileLayer attribution='&copy; OSM' url={tileUrl} />
              {userPos && <FlyToUser position={userPos} />}
              {userPos && <Marker position={userPos} icon={userIcon}><Popup><b>{t('your_location')}</b></Popup></Marker>}
              {centres.map((c) => (
                <Marker key={c.id} position={[c.lat, c.lng]} icon={centreIcon} eventHandlers={{ click: () => setSelectedCentre(c) }}>
                  <Popup><div className="min-w-[160px]"><p className="font-bold text-sm">{c.name}</p><p className="text-xs text-gray-600 mt-1">{c.address}</p><p className="text-xs font-medium mt-1" style={{ color: '#0d9488' }}>{c.distance_km} km</p></div></Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        )}
      </div>

      {/* Centre Cards */}
      <div className="px-5 pt-2 pb-4 space-y-3 max-h-[35%] overflow-y-auto">
        {loading ? (
          <>{[1, 2].map((i) => <div key={i} className="card p-5"><div className="skeleton h-12 rounded" /></div>)}</>
        ) : (
          centres.map((c) => (
            <div key={c.id} onClick={() => setSelectedCentre(c)}
                 className={`card p-4 transition-all duration-200 cursor-pointer ${selectedCentre?.id === c.id ? 'ring-1' : ''}`}
                 style={selectedCentre?.id === c.id ? { borderColor: 'var(--accent)', ringColor: 'rgba(13,148,136,0.2)' } : {}}>
              <div className="flex items-start gap-3">
                <div className="icon-box w-10 h-10" style={{ background: c.type === 'govt_health_center' ? 'rgba(59,130,246,0.08)' : 'var(--accent-bg)', color: c.type === 'govt_health_center' ? '#3b82f6' : 'var(--accent)' }}>
                  <Icons.Hospital className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="font-semibold text-[13px] truncate" style={{ color: 'var(--text-primary)' }}>{c.name}</p>
                    <span className="text-[11px] font-semibold ml-2 shrink-0" style={{ color: 'var(--accent)' }}>{c.distance_km} km</span>
                  </div>
                  <p className="text-[11px] mt-1 truncate" style={{ color: 'var(--text-tertiary)' }}>{c.address}</p>
                  <div className="flex gap-1.5 mt-2.5 flex-wrap">
                    {c.accepts.map((a) => <span key={a} className="tag" style={{ background: 'var(--bg-tertiary)', color: 'var(--text-tertiary)' }}>{a.replace(/_/g, ' ')}</span>)}
                  </div>
                </div>
              </div>
              <button onClick={(e) => { e.stopPropagation(); window.open(`https://www.google.com/maps/dir/?api=1&destination=${c.lat},${c.lng}`, '_blank'); }}
                      className="mt-3 w-full py-3 rounded-xl card font-semibold text-[11px] flex items-center justify-center gap-1.5 active:scale-[0.98] transition-transform"
                      style={{ color: 'var(--accent)' }}>
                <Icons.Navigation className="w-3.5 h-3.5" />
                {t('get_directions')}
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
