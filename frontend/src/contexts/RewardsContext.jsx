import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getRewardsBalance, awardPoints as apiAwardPoints } from '../utils/api';

const RewardsContext = createContext(null);

const DEVICE_ID_KEY = 'amr-guard-device-id';
const CACHE_KEY     = 'amr-guard-rewards-cache';
const CACHE_TTL_MS  = 5 * 60 * 1000; // 5 min

function getDeviceId() {
  let id = localStorage.getItem(DEVICE_ID_KEY);
  if (!id) {
    id = (crypto.randomUUID?.() || Math.random().toString(36).slice(2) + Date.now().toString(36));
    localStorage.setItem(DEVICE_ID_KEY, id);
    // Also randomly assign a simulated district on first load for demo purposes
    const districts = ['Satara', 'Gadchiroli', 'Raigad'];
    localStorage.setItem('amr-guard-district', districts[Math.floor(Math.random() * districts.length)]);
  }
  return id;
}

function getDistrict() {
  let district = localStorage.getItem('amr-guard-district');
  if (!district) {
    const districts = ['Satara', 'Gadchiroli', 'Raigad'];
    district = districts[Math.floor(Math.random() * districts.length)];
    localStorage.setItem('amr-guard-district', district);
  }
  return district;
}

const DEFAULT_STATE = {
  points: 0,
  tier: 'Scout',
  badges: [],
  total_scans: 0,
  total_disposed: 0,
  next_tier: 'Sentinel',
  points_to_next_tier: 100,
  transactions: [],
};

export function RewardsProvider({ children }) {
  const [deviceId] = useState(getDeviceId);
  const [district] = useState(getDistrict);
  const [rewards, setRewards] = useState(() => {
    try {
      const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null');
      if (cached && Date.now() - cached._ts < CACHE_TTL_MS) return cached;
    } catch { /* ignore */ }
    return DEFAULT_STATE;
  });
  const [loading, setLoading] = useState(false);
  const [newBadges, setNewBadges] = useState([]);   // badges just earned — shown as toasts

  const refresh = useCallback(async () => {
    if (!navigator.onLine) return;
    setLoading(true);
    try {
      const data = await getRewardsBalance(deviceId);
      const withTs = { ...data, _ts: Date.now() };
      setRewards(withTs);
      localStorage.setItem(CACHE_KEY, JSON.stringify(withTs));
    } catch (e) {
      console.warn('[Rewards] Could not refresh balance:', e.message);
    } finally {
      setLoading(false);
    }
  }, [deviceId]);

  // Award points locally + sync with backend
  const addPoints = useCallback(async (amount, reason) => {
    // Optimistic update
    setRewards(prev => {
      const newPts = (prev.points || 0) + amount;
      return { ...prev, points: newPts, transactions: [{ id: Date.now(), type: 'earn', amount, reason, timestamp: new Date().toISOString() }, ...(prev.transactions || []).slice(0, 19)] };
    });
    try {
      const result = await apiAwardPoints(deviceId, amount, reason);
      // Check for newly earned badges
      const prevBadges = rewards.badges || [];
      const newOnes = (result.new_badges || []).filter(b => !prevBadges.includes(b));
      if (newOnes.length) setNewBadges(newOnes);
      await refresh();
    } catch (e) {
      console.warn('[Rewards] Award failed:', e.message);
    }
  }, [deviceId, refresh, rewards.badges]);

  const clearNewBadges = useCallback(() => setNewBadges([]), []);

  useEffect(() => { refresh(); }, [refresh]);

  // Re-fetch when coming back online
  useEffect(() => {
    const handler = () => refresh();
    window.addEventListener('online', handler);
    return () => window.removeEventListener('online', handler);
  }, [refresh]);

  // Re-fetch when tab becomes visible again (e.g. returning from pharmacy portal)
  useEffect(() => {
    const handler = () => { if (document.visibilityState === 'visible') refresh(); };
    document.addEventListener('visibilitychange', handler);
    return () => document.removeEventListener('visibilitychange', handler);
  }, [refresh]);

  return (
    <RewardsContext.Provider value={{ rewards, deviceId, district, loading, addPoints, refresh, newBadges, clearNewBadges }}>
      {children}
    </RewardsContext.Provider>
  );
}

export function useRewards() {
  const ctx = useContext(RewardsContext);
  if (!ctx) throw new Error('useRewards must be used within RewardsProvider');
  return ctx;
}
