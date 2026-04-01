import { useState, useEffect } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import Welcome from './pages/Welcome';
import Home from './pages/Home';
import Scanner from './pages/Scanner';
import MapView from './pages/MapView';
import About from './pages/About';
import Profile from './pages/Profile';

export default function App() {
  const [showWelcome, setShowWelcome] = useState(
    () => !localStorage.getItem('amr-guard-onboarded')
  );
  const location = useLocation();

  useEffect(() => {
    if (localStorage.getItem('amr-guard-onboarded')) {
      setShowWelcome(false);
    }
  }, [location]);

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then((registration) => {
        registration.addEventListener('updatefound', () => {
          console.log('[AMR-Guard] New service worker update found');
        });
      });
    }
  }, []);

  if (showWelcome) {
    return <Welcome />;
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/scan" element={<Scanner />} />
        <Route path="/map" element={<MapView />} />
        <Route path="/about" element={<About />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Layout>
  );
}
