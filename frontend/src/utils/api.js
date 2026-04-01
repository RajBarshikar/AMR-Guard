import { saveToOfflineQueue, saveScanResult } from './offlineQueue';

const API_BASE = '/api/v1';

export async function analyzeMedication(imageBlob) {
  if (!navigator.onLine) {
    await saveToOfflineQueue(imageBlob);
    return { result: null, offline: true };
  }
  try {
    const formData = new FormData();
    formData.append('file', imageBlob, 'medication.jpg');
    const response = await fetch(`${API_BASE}/analyze-medication`, { method: 'POST', body: formData });
    if (!response.ok) throw new Error(`Server responded with ${response.status}`);
    const result = await response.json();
    await saveScanResult(result);
    return { result, offline: false };
  } catch (err) {
    console.warn('[AMR-Guard] API failed, queuing offline:', err.message);
    await saveToOfflineQueue(imageBlob);
    return { result: null, offline: true };
  }
}

export async function getNearestBins(lat, lng) {
  const response = await fetch(`${API_BASE}/nearest-bins?lat=${lat}&lng=${lng}`);
  if (!response.ok) throw new Error(`Failed to fetch centres: ${response.status}`);
  return response.json();
}

export async function getLeaderboard() {
  const response = await fetch(`${API_BASE}/leaderboard`);
  if (!response.ok) throw new Error(`Failed to fetch leaderboard: ${response.status}`);
  return response.json();
}

export async function getDeviceToken() {
  const response = await fetch(`${API_BASE}/device-token`);
  if (!response.ok) throw new Error(`Failed to get token: ${response.status}`);
  return response.json();
}
