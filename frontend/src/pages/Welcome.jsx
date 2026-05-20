import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import { useTheme } from '../contexts/ThemeContext';
import Icons from '../components/Icons';

export default function Welcome() {
  const { lang, setLang, t } = useLanguage();
  const { isDark } = useTheme();
  const navigate = useNavigate();
  const [exiting, setExiting] = useState(false);

  const handleStart = () => {
    setExiting(true);
    localStorage.setItem('amr-guard-onboarded', 'true');
    setTimeout(() => navigate('/'), 350);
  };

  return (
    <div
      className={`fixed inset-0 z-[100] flex flex-col items-center justify-center px-6 transition-all duration-350 ${
        exiting ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
      }`}
      style={{
        background: isDark
          ? 'radial-gradient(ellipse at 50% 30%, rgba(13,148,136,0.15) 0%, #0f172a 70%)'
          : 'radial-gradient(ellipse at 50% 30%, rgba(13,148,136,0.08) 0%, #ffffff 70%)',
      }}
    >
      <div className="animate-fade-in-up mb-8">
        <div className="w-24 h-24 rounded-3xl gradient-primary flex items-center justify-center" style={{ boxShadow: 'var(--shadow-accent)' }}>
          <Icons.ShieldCheck className="w-12 h-12 text-white" />
        </div>
      </div>

      <h1 className="text-4xl font-extrabold gradient-text animate-fade-in-up stagger-1 mb-2">
        {t('app_name')}
      </h1>
      <p className="text-lg font-medium animate-fade-in-up stagger-2 mb-3 italic" style={{ color: 'var(--accent)' }}>
        {t('tagline')}
      </p>
      <p className="text-sm text-center leading-relaxed max-w-xs animate-fade-in-up stagger-3 mb-10" style={{ color: 'var(--text-secondary)' }}>
        {t('welcome_subtitle')}
      </p>

      <div className="animate-fade-in-up stagger-4 w-full max-w-xs mb-6">
        <p className="text-xs uppercase tracking-widest text-center mb-3 font-medium" style={{ color: 'var(--text-tertiary)' }}>
          {t('select_language')}
        </p>
        <div className="flex gap-3">
          {[{ code: 'en', label: 'English' }, { code: 'mr', label: 'मराठी' }].map(({ code, label }) => (
            <button key={code} onClick={() => setLang(code)}
              className={`flex-1 py-3 rounded-2xl font-semibold text-sm transition-all duration-300 ${lang === code ? 'gradient-primary text-white' : 'card'}`}
              style={lang === code ? { boxShadow: 'var(--shadow-accent)' } : { color: 'var(--text-secondary)' }}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <button onClick={handleStart}
        className="animate-fade-in-up stagger-5 w-full max-w-xs py-4 rounded-2xl gradient-primary text-white font-bold text-lg active:scale-[0.97] transition-transform duration-200"
        style={{ boxShadow: 'var(--shadow-accent)' }}>
        {t('get_started')}
        <Icons.ChevronRight className="w-5 h-5 inline ml-1 -mt-0.5" />
      </button>
    </div>
  );
}
