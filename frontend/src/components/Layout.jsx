import BottomNav from './BottomNav';

export default function Layout({ children }) {
  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--bg-primary)' }}>
      <main className="flex-1 overflow-y-auto pb-24">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
