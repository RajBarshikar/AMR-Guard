import BottomNav from './BottomNav';

export default function Layout({ children }) {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)', overflow: 'hidden' }}>
      <main style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', paddingBottom: 'calc(68px + env(safe-area-inset-bottom, 0px) + 16px)', WebkitOverflowScrolling: 'touch' }}>
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
