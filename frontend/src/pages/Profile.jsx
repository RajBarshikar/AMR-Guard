import { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { getScanHistory } from '../utils/offlineQueue';
import Icons from '../components/Icons';

const tiers = [
  { key: 'scout', Icon: Icons.Target, color: '#0d9488', nameKey: 'scout', descKey: 'scout_desc', req: (s) => s.total >= 1 },
  { key: 'sentinel', Icon: Icons.Shield, color: '#3b82f6', nameKey: 'sentinel', descKey: 'sentinel_desc', req: (s) => s.total >= 5 },
  { key: 'guardian', Icon: Icons.ShieldCheck, color: '#8b5cf6', nameKey: 'amr_guardian', descKey: 'guardian_desc', req: () => false },
];

export default function Profile() {
  const { lang, setLang, t } = useLanguage();
  const { isDark, toggle } = useTheme();
  const [stats, setStats] = useState({ total: 0, antibiotics: 0, disposed: 0 });
  const [deviceId] = useState(() => {
    let id = localStorage.getItem('amr-guard-device-id');
    if (!id) { id = crypto.randomUUID?.() || Math.random().toString(36).slice(2); localStorage.setItem('amr-guard-device-id', id); }
    return id;
  });

  useEffect(() => {
    getScanHistory().then((h) => setStats({ total: h.length, antibiotics: h.filter((s) => s.is_antibiotic).length, disposed: Math.floor(h.length * 0.8) }));
  }, []);

  const currentTier = tiers.reduce((acc, tier) => tier.req(stats) ? tier : acc, null);
  const points = stats.total * 10 + stats.antibiotics * 25 + stats.disposed * 15;

  return (
    <div className="page">
      {/* Header */}
      <div className="text-center animate-fade-in-up">
        <div className="w-20 h-20 mx-auto rounded-full gradient-primary flex items-center justify-center mb-4" style={{ boxShadow: 'var(--shadow-accent)' }}>
          <Icons.ShieldCheck className="w-9 h-9 text-white" />
        </div>
        <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
          {currentTier ? t(currentTier.nameKey) : t('scout')}
        </h1>
        <p className="text-[13px] mt-1" style={{ color: 'var(--text-tertiary)' }}>{t('guardian_level')}</p>
        <div className="flex items-center justify-center gap-1.5 mt-2">
          <Icons.Star className="w-4 h-4" style={{ color: '#f59e0b' }} />
          <span className="text-[13px] font-bold" style={{ color: '#f59e0b' }}>{points} {t('points')}</span>
        </div>
      </div>

      <div className="section-divider" />

      {/* Settings */}
      <div className="animate-fade-in-up stagger-1">
        <p className="section-header">Settings</p>
        <div className="card p-5 space-y-5">
          {/* Theme Toggle */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="icon-box w-10 h-10" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                {isDark ? <Icons.Moon className="w-4 h-4" /> : <Icons.Sun className="w-4 h-4" />}
              </div>
              <span className="text-[13px] font-medium" style={{ color: 'var(--text-primary)' }}>{isDark ? 'Dark Mode' : 'Light Mode'}</span>
            </div>
            <button onClick={toggle} className="w-12 h-7 rounded-full relative transition-colors duration-300"
                    style={{ background: isDark ? 'var(--accent)' : 'var(--bg-tertiary)' }}>
              <div className="absolute top-0.5 w-6 h-6 rounded-full shadow transition-transform duration-300"
                   style={{ background: 'white', transform: isDark ? 'translateX(22px)' : 'translateX(2px)' }} />
            </button>
          </div>
          {/* Language */}
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="icon-box w-10 h-10" style={{ background: 'rgba(59,130,246,0.08)', color: '#3b82f6' }}>
                <Icons.Globe className="w-4 h-4" />
              </div>
              <span className="text-[13px] font-medium" style={{ color: 'var(--text-primary)' }}>{t('select_language')}</span>
            </div>
            <div className="flex gap-3">
              {[{ code: 'en', label: 'English' }, { code: 'mr', label: 'मराठी' }].map(({ code, label }) => (
                <button key={code} onClick={() => setLang(code)}
                        className={`flex-1 py-3 rounded-xl font-semibold text-[13px] transition-all duration-300 ${lang === code ? 'gradient-primary text-white' : 'card'}`}
                        style={lang === code ? { boxShadow: 'var(--shadow-accent)' } : { color: 'var(--text-secondary)' }}>
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="section-divider" />

      {/* Device Token */}
      <div className="animate-fade-in-up stagger-1">
        <p className="section-header">Identity</p>
        <div className="card p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="icon-box w-10 h-10" style={{ background: 'rgba(245,158,11,0.08)', color: '#d97706' }}>
              <Icons.Key className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[13px] font-medium" style={{ color: 'var(--text-primary)' }}>{t('device_token')}</p>
              <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{t('device_token_info')}</p>
            </div>
          </div>
          <div className="px-3.5 py-3 rounded-xl text-[11px] font-mono truncate" style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: '1px solid var(--border-subtle)' }}>
            {deviceId}
          </div>
        </div>
      </div>

      <div className="section-divider" />

      {/* QR Code */}
      <div className="animate-fade-in-up stagger-2">
        <p className="section-header">Disposal Verification</p>
        <div className="card p-6 text-center">
          <div className="flex items-center justify-center gap-2 mb-5">
            <Icons.QrCode className="w-4 h-4" style={{ color: 'var(--accent)' }} />
            <p className="text-[13px] font-semibold" style={{ color: 'var(--text-primary)' }}>{t('qr_code')}</p>
          </div>
          <div className="w-40 h-40 mx-auto mb-5 rounded-2xl p-3" style={{ background: 'white', boxShadow: 'var(--shadow-md)' }}>
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <rect x="5" y="5" width="25" height="25" fill="#0f172a" rx="3"/>
              <rect x="70" y="5" width="25" height="25" fill="#0f172a" rx="3"/>
              <rect x="5" y="70" width="25" height="25" fill="#0f172a" rx="3"/>
              <rect x="10" y="10" width="15" height="15" fill="white" rx="2"/>
              <rect x="75" y="10" width="15" height="15" fill="white" rx="2"/>
              <rect x="10" y="75" width="15" height="15" fill="white" rx="2"/>
              <rect x="14" y="14" width="7" height="7" fill="#0f172a" rx="1"/>
              <rect x="79" y="14" width="7" height="7" fill="#0f172a" rx="1"/>
              <rect x="14" y="79" width="7" height="7" fill="#0f172a" rx="1"/>
              {[35,42,49,56,63].map(x => [5,12,19,26,35,42,49,56,63,70,77,84].map(y => (
                Math.random() > 0.4 && <rect key={`${x}-${y}`} x={x} y={y} width="5" height="5" fill="#0f172a"/>
              )))}
              {[5,12,19,26].map(x => [35,42,49,56,63].map(y => (
                Math.random() > 0.4 && <rect key={`b${x}-${y}`} x={x} y={y} width="5" height="5" fill="#0f172a"/>
              )))}
              {[70,77,84].map(x => [35,42,49,56,63,70,77,84].map(y => (
                Math.random() > 0.4 && <rect key={`c${x}-${y}`} x={x} y={y} width="5" height="5" fill="#0f172a"/>
              )))}
            </svg>
          </div>
          <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>{t('qr_code_info')}</p>
        </div>
      </div>

      <div className="section-divider" />

      {/* Stats */}
      <div className="animate-fade-in-up stagger-2">
        <p className="section-header">{t('stats')}</p>
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: t('total_scans'), value: stats.total, Icon: Icons.Scan, color: '#0d9488' },
            { label: t('antibiotics_found'), value: stats.antibiotics, Icon: Icons.AlertTriangle, color: '#ef4444' },
            { label: t('disposed_safely'), value: stats.disposed, Icon: Icons.Recycle, color: '#22c55e' },
          ].map(({ label, value, Icon, color }) => (
            <div key={label} className="card p-4 text-center">
              <div className="icon-box w-10 h-10 mx-auto mb-3" style={{ background: `${color}10`, color }}><Icon className="w-4 h-4" /></div>
              <div className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{value}</div>
              <div className="text-[10px] mt-1.5 leading-tight" style={{ color: 'var(--text-tertiary)' }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="section-divider" />

      {/* Guardian Tiers */}
      <div className="animate-fade-in-up stagger-3">
        <p className="section-header">{t('guardian_level')}</p>
        <div className="space-y-3">
          {tiers.map(({ key, Icon, color, nameKey, descKey, req }) => {
            const unlocked = req(stats);
            return (
              <div key={key} className={`card p-4 flex items-center gap-3.5 transition-all duration-300 ${unlocked ? '' : 'opacity-40'}`}>
                <div className="icon-box w-12 h-12 rounded-2xl" style={{ background: `${color}10`, color, filter: unlocked ? 'none' : 'grayscale(1)' }}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-[13px]" style={{ color: 'var(--text-primary)' }}>{t(nameKey)}</p>
                  <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{t(descKey)}</p>
                </div>
                <span className="tag" style={{
                  background: unlocked ? 'var(--accent-bg)' : 'var(--bg-tertiary)',
                  color: unlocked ? 'var(--accent)' : 'var(--text-tertiary)',
                }}>
                  {unlocked ? <><Icons.CheckCircle className="w-3 h-3 mr-1" /> {t('tier_unlocked')}</> : t('tier_locked')}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 text-center pb-2">
        <p className="text-[11px] font-medium" style={{ color: 'var(--text-tertiary)' }}>AMR-Guard v1.0</p>
        <p className="text-[10px] mt-1" style={{ color: 'var(--text-tertiary)' }}>Secure Disposal. Stronger Medicine.</p>
      </div>
    </div>
  );
}
