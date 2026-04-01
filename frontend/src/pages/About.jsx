import { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import Icons from '../components/Icons';

const sections = [
  { titleKey: 'about_amr_title', bodyKey: 'about_amr_body', Icon: Icons.ShieldCheck, color: '#ef4444' },
  { titleKey: 'about_why_title', bodyKey: 'about_why_body', Icon: Icons.AlertTriangle, color: '#d97706' },
  { titleKey: 'about_env_title', bodyKey: 'about_env_body', Icon: Icons.Recycle, color: '#22c55e' },
  { titleKey: 'about_how_title', bodyKey: 'about_how_body', Icon: Icons.Hospital, color: '#3b82f6' },
  { titleKey: 'about_you_title', bodyKey: 'about_you_body', Icon: Icons.Heart, color: '#8b5cf6' },
];

const tips = ['about_tip_1', 'about_tip_2', 'about_tip_3', 'about_tip_4', 'about_tip_5'];

export default function About() {
  const { t } = useLanguage();
  const [expanded, setExpanded] = useState(null);

  return (
    <div className="page">
      {/* Header */}
      <div className="animate-fade-in-up">
        <div className="flex items-center gap-3.5">
          <div className="icon-box w-12 h-12 rounded-2xl gradient-primary" style={{ boxShadow: 'var(--shadow-accent)' }}>
            <Icons.BookOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>{t('about_title')}</h1>
            <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-tertiary)' }}>{t('about_subtitle')}</p>
          </div>
        </div>
      </div>

      {/* Hero Card */}
      <div className="animate-fade-in-up stagger-1 card p-6 text-center mt-7" style={{ borderTop: '3px solid var(--accent)' }}>
        <div className="icon-box w-16 h-16 mx-auto mb-4 rounded-2xl" style={{ background: 'rgba(239,68,68,0.08)', color: '#ef4444' }}>
          <Icons.AlertTriangle className="w-7 h-7" />
        </div>
        <h2 className="text-base font-bold mb-3" style={{ color: 'var(--text-primary)' }}>{t('about_hero_title')}</h2>
        <p className="text-[13px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{t('about_hero_body')}</p>
      </div>

      <div className="section-divider" />

      {/* Expandable Sections */}
      <div className="animate-fade-in-up stagger-2">
        <p className="section-header">Learn More</p>
        <div className="space-y-3">
          {sections.map(({ titleKey, bodyKey, Icon, color }, i) => (
            <button key={titleKey}
                    onClick={() => setExpanded(expanded === i ? null : i)}
                    className="card w-full text-left p-4 active:scale-[0.99] transition-transform">
              <div className="flex items-center gap-3">
                <div className="icon-box w-10 h-10 shrink-0" style={{ background: `${color}10`, color }}>
                  <Icon className="w-4 h-4" />
                </div>
                <p className="flex-1 font-semibold text-[13px]" style={{ color: 'var(--text-primary)' }}>{t(titleKey)}</p>
                <Icons.ChevronRight
                  className={`w-4 h-4 transition-transform duration-200 ${expanded === i ? 'rotate-90' : ''}`}
                  style={{ color: 'var(--text-tertiary)' }}
                />
              </div>
              {expanded === i && (
                <p className="text-[13px] leading-relaxed mt-3 animate-fade-in" style={{ color: 'var(--text-secondary)', paddingLeft: '52px' }}>
                  {t(bodyKey)}
                </p>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="section-divider" />

      {/* Quick Tips */}
      <div className="animate-fade-in-up stagger-3">
        <p className="section-header">{t('about_tips_title')}</p>
        <div className="card p-5 space-y-5">
          {tips.map((tipKey, i) => (
            <div key={tipKey} className="flex items-start gap-3.5">
              <div className="w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-bold shrink-0 mt-0.5"
                   style={{ background: 'var(--accent-bg)', color: 'var(--accent)' }}>
                {i + 1}
              </div>
              <p className="text-[13px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{t(tipKey)}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="section-divider" />

      {/* CTA Footer */}
      <div className="animate-fade-in-up stagger-4 card p-6 text-center" style={{ borderTop: '2px solid var(--accent)' }}>
        <p className="text-[13px] font-bold mb-2" style={{ color: 'var(--accent)' }}>{t('about_cta')}</p>
        <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text-tertiary)' }}>{t('about_cta_sub')}</p>
      </div>
    </div>
  );
}
