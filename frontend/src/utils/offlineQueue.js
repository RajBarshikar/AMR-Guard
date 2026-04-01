import { openDB } from 'idb';

const DB_NAME = 'snap-drop-db';
const STORE_QUEUE = 'offline-queue';
const STORE_SCANS = 'scan-history';
const DB_VERSION = 1;

async function getDB() {
  return openDB(DB_NAME, DB_VERSION, {
    upgrade(db) {
      if (!db.objectStoreNames.contains(STORE_QUEUE)) {
        db.createObjectStore(STORE_QUEUE, { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains(STORE_SCANS)) {
        db.createObjectStore(STORE_SCANS, { keyPath: 'id', autoIncrement: true });
      }
    },
  });
}

/**
 * Save an image blob to the offline queue for later syncing.
 */
export async function saveToOfflineQueue(imageBlob) {
  const db = await getDB();
  const entry = {
    imageBlob,
    timestamp: Date.now(),
    status: 'pending',
  };
  const id = await db.add(STORE_QUEUE, entry);
  return id;
}

/**
 * Get all pending submissions from the offline queue.
 */
export async function getPendingSubmissions() {
  const db = await getDB();
  return db.getAll(STORE_QUEUE);
}

/**
 * Remove a submission from the queue after successful sync.
 */
export async function clearSubmission(id) {
  const db = await getDB();
  await db.delete(STORE_QUEUE, id);
}

/**
 * Save a completed scan result to local history.
 */
export async function saveScanResult(result) {
  const db = await getDB();
  const entry = {
    ...result,
    scannedAt: Date.now(),
  };
  return db.add(STORE_SCANS, entry);
}

/**
 * Get all scan results from local history.
 */
export async function getScanHistory() {
  const db = await getDB();
  const all = await db.getAll(STORE_SCANS);
  return all.sort((a, b) => b.scannedAt - a.scannedAt);
}

/**
 * Attempt to sync all offline-queued submissions to the backend.
 * Called automatically when the device goes back online.
 */
export async function syncOfflineQueue() {
  const pending = await getPendingSubmissions();
  const results = [];

  for (const submission of pending) {
    try {
      const formData = new FormData();
      formData.append('file', submission.imageBlob, `scan-${submission.id}.jpg`);

      const response = await fetch('/api/v1/analyze-medication', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        await saveScanResult(result);
        await clearSubmission(submission.id);
        results.push({ id: submission.id, success: true, result });
      } else {
        results.push({ id: submission.id, success: false, error: 'Server error' });
      }
    } catch (err) {
      results.push({ id: submission.id, success: false, error: err.message });
    }
  }

  return results;
}

// Register the online event listener for auto-sync
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    syncOfflineQueue().then((results) => {
      const synced = results.filter((r) => r.success).length;
      if (synced > 0) {
        console.log(`[Snap & Drop] Synced ${synced} offline submissions`);
      }
    });
  });
}
