import { useState, useEffect } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import Welcome from './pages/Welcome';
import Home from './pages/Home';
import Scanner from './pages/Scanner';
import MapView from './pages/MapView';
import About from './pages/About';
import Profile from './pages/Profile';
import TakeBack from './pages/TakeBack';
import MyRequests from './pages/MyRequests';
import PharmacyLogin from './pages/pharmacy/PharmacyLogin';
import PharmacyDashboard from './pages/pharmacy/PharmacyDashboard';


export default function App() {
  const [showWelcome, setShowWelcome] = useState(
    () => !localStorage.getItem('amr-guard-onboarded')
  );
  const location = useLocation();

  // Pharmacy portal — completely separate from the main app layout
  if (location.pathname.startsWith('/pharmacy')) {
    return (
      <Routes>
        <Route path="/pharmacy/login"     element={<PharmacyLogin />} />
        <Route path="/pharmacy/dashboard" element={<PharmacyDashboard />} />
        <Route path="/pharmacy"           element={<PharmacyLogin />} />
      </Routes>
    );
  }

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
        <Route path="/takeback" element={<TakeBack />} />
        <Route path="/my-requests" element={<MyRequests />} />
      </Routes>
    </Layout>
  );
}
