import { NavLink } from 'react-router-dom';
import { useLanguage } from '../contexts/LanguageContext';
import Icons from './Icons';

const navItems = [
  { path: '/', labelKey: 'home', Icon: Icons.Home },
  { path: '/map', labelKey: 'map', Icon: Icons.MapPin },
  { path: '/scan', labelKey: 'scan', Icon: Icons.Camera, isScan: true },
  { path: '/about', labelKey: 'about', Icon: Icons.BookOpen },
  { path: '/profile', labelKey: 'profile', Icon: Icons.User },
];

export default function BottomNav() {
  const { t } = useLanguage();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bottom-nav safe-bottom">
      <div className="flex items-end justify-around h-[68px] max-w-lg mx-auto px-2">
        {navItems.map(({ path, labelKey, Icon, isScan }) => (
          <NavLink
            key={path}
            to={path}
            className="flex flex-col items-center justify-center py-2"
            style={{ width: '60px' }}
          >
            {({ isActive }) =>
              isScan ? (
                <div className="relative -mt-7">
                  <div className="w-[54px] h-[54px] rounded-full gradient-primary flex items-center justify-center transition-transform duration-200 active:scale-90"
                       style={{ boxShadow: 'var(--shadow-accent)' }}>
                    <Icon className="w-6 h-6" style={{ color: '#fff' }} />
                  </div>
                </div>
              ) : (
                <>
                  <Icon
                    className={`w-[22px] h-[22px] transition-all duration-200 ${isActive ? 'scale-110' : ''}`}
                    style={{ color: isActive ? 'var(--accent)' : 'var(--text-tertiary)' }}
                  />
                  <span
                    className="text-[10px] font-semibold mt-1"
                    style={{ color: isActive ? 'var(--accent)' : 'var(--text-tertiary)' }}
                  >
                    {t(labelKey)}
                  </span>
                </>
              )
            }
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
