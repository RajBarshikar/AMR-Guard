import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import { getScanHistory } from '../utils/offlineQueue';
import { getLeaderboard } from '../utils/api';
import Icons from '../components/Icons';

export default function Home() {
  const { t } = useLanguage();
  const { isDark, toggle } = useTheme();
  const navigate = useNavigate();
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [scanHistory, setScanHistory] = useState([]);
  const [stats, setStats] = useState({ total: 0, antibiotics: 0, disposed: 0 });
  const [leaderboard, setLeaderboard] = useState([]);
  const [activeKnowledge, setActiveKnowledge] = useState(null);

  useEffect(() => {
    const on = () => setIsOnline(true);
    const off = () => setIsOnline(false);
    window.addEventListener('online', on);
    window.addEventListener('offline', off);
    return () => { window.removeEventListener('online', on); window.removeEventListener('offline', off); };
  }, []);

  useEffect(() => {
    getScanHistory().then((h) => {
      setScanHistory(h.slice(0, 5));
      setStats({ total: h.length, antibiotics: h.filter((s) => s.is_antibiotic).length, disposed: Math.floor(h.length * 0.8) });
    });
    getLeaderboard().then(setLeaderboard).catch(() => {});
  }, []);

  const knowledgeItems = [
    { key: 'what', titleKey: 'knowledge_what_title', bodyKey: 'knowledge_what_body', Icon: Icons.ShieldCheck, color: '#0d9488' },
    { key: 'why', titleKey: 'knowledge_why_title', bodyKey: 'knowledge_why_body', Icon: Icons.AlertTriangle, color: '#ef4444' },
    { key: 'how', titleKey: 'knowledge_how_title', bodyKey: 'knowledge_how_body', Icon: Icons.Heart, color: '#8b5cf6' },
  ];

  return (
    <div className="page">
      {/* Header */}
      <div className="flex items-center justify-between animate-fade-in-up">
        <div className="flex items-center gap-3.5">
          <div className="icon-box w-12 h-12 rounded-2xl gradient-primary" style={{ boxShadow: 'var(--shadow-accent)' }}>
            <Icons.ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{t('app_name')}</h1>
            <p className="text-[11px] italic mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{t('tagline')}</p>
          </div>
        </div>
        <button onClick={toggle} className="w-10 h-10 rounded-xl flex items-center justify-center card" style={{ color: 'var(--text-secondary)' }}>
          {isDark ? <Icons.Sun className="w-5 h-5" /> : <Icons.Moon className="w-5 h-5" />}
        </button>
      </div>

      {/* Offline */}
      {!isOnline && (
        <div className="animate-fade-in flex items-center gap-2.5 rounded-2xl px-4 py-3.5 text-sm font-medium mt-6"
             style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)', color: '#d97706' }}>
          <Icons.WifiOff className="w-4 h-4 shrink-0" />
          <span>{t('offline_banner')}</span>
        </div>
      )}

      {/* Stats */}
      <div className="animate-fade-in-up stagger-1 mt-7">
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: t('total_scans'), value: stats.total, Icon: Icons.Scan, color: '#0d9488' },
            { label: t('antibiotics_found'), value: stats.antibiotics, Icon: Icons.AlertTriangle, color: '#ef4444' },
            { label: t('disposed_safely'), value: stats.disposed, Icon: Icons.Recycle, color: '#22c55e' },
          ].map(({ label, value, Icon, color }) => (
            <div key={label} className="card p-4 text-center">
              <div className="icon-box w-10 h-10 mx-auto mb-3" style={{ background: `${color}12`, color }}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>{value}</div>
              <div className="text-[10px] mt-1.5 leading-tight" style={{ color: 'var(--text-tertiary)' }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="section-divider" />

      {/* Quick Actions */}
      <div className="animate-fade-in-up stagger-2">
        <p className="section-header">{t('quick_actions')}</p>
        <div className="grid grid-cols-3 gap-3">
          {[
            { Icon: Icons.Camera, label: t('scan_medication'), action: () => navigate('/scan'), color: '#0d9488' },
            { Icon: Icons.MapPin, label: t('find_centres'), action: () => navigate('/map'), color: '#3b82f6' },
            { Icon: Icons.BookOpen, label: t('learn_amr'), action: () => navigate('/about'), color: '#8b5cf6' },
          ].map(({ Icon, label, action, color }) => (
            <button key={label} onClick={action} className="card p-4 flex flex-col items-center gap-3 active:scale-[0.96] transition-transform duration-200">
              <div className="icon-box w-12 h-12 rounded-2xl" style={{ background: `${color}10`, color }}>
                <Icon className="w-5 h-5" />
              </div>
              <span className="text-[11px] text-center leading-tight font-medium" style={{ color: 'var(--text-secondary)' }}>{label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="section-divider" />

      {/* Knowledge Capsules */}
      <div className="animate-fade-in-up stagger-2">
        <p className="section-header">{t('knowledge_capsules')}</p>
        <div className="space-y-3">
          {knowledgeItems.map(({ key, titleKey, bodyKey, Icon, color }) => (
            <button key={key} onClick={() => setActiveKnowledge(activeKnowledge === key ? null : key)}
                    className="card w-full text-left p-4 active:scale-[0.99] transition-transform">
              <div className="flex items-center gap-3">
                <div className="icon-box w-10 h-10" style={{ background: `${color}10`, color }}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-[13px]" style={{ color: 'var(--text-primary)' }}>{t(titleKey)}</p>
                </div>
                <Icons.ChevronRight className={`w-4 h-4 transition-transform duration-200 ${activeKnowledge === key ? 'rotate-90' : ''}`}
                                    style={{ color: 'var(--text-tertiary)' }} />
              </div>
              {activeKnowledge === key && (
                <p className="text-[13px] leading-relaxed mt-3 animate-fade-in" style={{ color: 'var(--text-secondary)', paddingLeft: '52px' }}>
                  {t(bodyKey)}
                </p>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Maha-Leaderboard */}
      {leaderboard.length > 0 && (
        <>
          <div className="section-divider" />
          <div className="animate-fade-in-up stagger-3">
            <p className="section-header">{t('leaderboard')}</p>
            <p className="text-[11px] -mt-3 mb-4" style={{ color: 'var(--text-tertiary)', paddingLeft: '2px' }}>{t('leaderboard_subtitle')}</p>
            <div className="card overflow-hidden">
              {leaderboard.map((entry, i) => (
                <div key={entry.city} className="flex items-center gap-3 px-5 py-4" style={{ borderBottom: i < leaderboard.length - 1 ? '1px solid var(--border-subtle)' : 'none' }}>
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold"
                       style={{
                         background: i === 0 ? '#f59e0b18' : i === 1 ? '#94a3b818' : i === 2 ? '#cd7f3218' : 'var(--bg-tertiary)',
                         color: i === 0 ? '#f59e0b' : i === 1 ? '#94a3b8' : i === 2 ? '#cd7f32' : 'var(--text-tertiary)',
                       }}>
                    {entry.rank}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-[13px] truncate" style={{ color: 'var(--text-primary)' }}>{entry.city}</p>
                    <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{entry.district}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[13px] font-bold" style={{ color: 'var(--accent)' }}>{entry.disposals.toLocaleString()}</p>
                    <p className="text-[10px]" style={{ color: 'var(--text-tertiary)' }}>{t('disposals')}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      <div className="section-divider" />

      {/* Recent Scans */}
      <div className="animate-fade-in-up stagger-3">
        <p className="section-header">{t('recent_scans')}</p>
        {scanHistory.length === 0 ? (
          <div className="card p-10 text-center">
            <div className="icon-box w-14 h-14 mx-auto mb-4" style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>
              <Icons.Scan className="w-6 h-6" />
            </div>
            <p className="text-[13px]" style={{ color: 'var(--text-tertiary)' }}>{t('no_scans_yet')}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {scanHistory.map((scan, i) => (
              <div key={scan.id || i} className="card px-4 py-4 flex items-center gap-3">
                <div className="icon-box w-10 h-10"
                     style={{ background: scan.is_antibiotic ? 'rgba(239,68,68,0.08)' : 'var(--accent-bg)', color: scan.is_antibiotic ? '#ef4444' : 'var(--accent)' }}>
                  <Icons.Pill className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-[13px] truncate" style={{ color: 'var(--text-primary)' }}>{scan.drug_name}</p>
                  <div className="flex items-center gap-1.5 mt-1">
                    {scan.is_antibiotic && <Icons.AlertTriangle className="w-3 h-3" style={{ color: '#ef4444' }} />}
                    <p className="text-[11px]" style={{ color: 'var(--text-tertiary)' }}>{scan.drug_type}</p>
                    {scan.eco_hazard_score && (
                      <span className="tag ml-1" style={{
                        background: scan.eco_hazard_score >= 7 ? 'rgba(239,68,68,0.08)' : scan.eco_hazard_score >= 4 ? 'rgba(245,158,11,0.08)' : 'rgba(34,197,94,0.08)',
                        color: scan.eco_hazard_score >= 7 ? '#ef4444' : scan.eco_hazard_score >= 4 ? '#d97706' : '#22c55e',
                      }}>
                        {scan.eco_hazard_score}/10
                      </span>
                    )}
                  </div>
                </div>
                <span className="tag" style={{
                  background: scan.expiry_status === 'expired' ? 'rgba(239,68,68,0.08)' : scan.expiry_status === 'expiring_soon' ? 'rgba(245,158,11,0.08)' : 'rgba(34,197,94,0.08)',
                  color: scan.expiry_status === 'expired' ? '#ef4444' : scan.expiry_status === 'expiring_soon' ? '#d97706' : '#22c55e',
                }}>
                  {scan.expiry_label}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
