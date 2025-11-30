import { useState, useEffect, useCallback } from 'react';
import { getPendingCounts, offlineStorage } from '../services/offlineStorage';

interface OfflineState {
  isOnline: boolean;
  pendingMortality: number;
  pendingIssues: number;
  totalPending: number;
  lastSyncTime: Date | null;
  isSyncing: boolean;
}

interface UseOfflineReturn extends OfflineState {
  sync: () => Promise<void>;
  refreshPendingCounts: () => Promise<void>;
}

export const useOffline = (): UseOfflineReturn => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [pendingMortality, setPendingMortality] = useState(0);
  const [pendingIssues, setPendingIssues] = useState(0);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  // Update online status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Refresh pending counts
  const refreshPendingCounts = useCallback(async () => {
    try {
      const counts = await getPendingCounts();
      setPendingMortality(counts.mortality);
      setPendingIssues(counts.issues);
    } catch (error) {
      console.error('Failed to get pending counts:', error);
    }
  }, []);

  // Initial load and periodic refresh
  useEffect(() => {
    refreshPendingCounts();
    
    const interval = setInterval(refreshPendingCounts, 30000); // Every 30 seconds
    
    return () => clearInterval(interval);
  }, [refreshPendingCounts]);

  // Auto-sync when coming back online
  useEffect(() => {
    if (isOnline && (pendingMortality > 0 || pendingIssues > 0)) {
      sync();
    }
  }, [isOnline]);

  // Sync pending items
  const sync = useCallback(async () => {
    if (!isOnline || isSyncing) return;

    setIsSyncing(true);

    try {
      // Request background sync if available
      if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        if (pendingMortality > 0) {
          await offlineStorage.requestSync('sync-mortality');
        }
        if (pendingIssues > 0) {
          await offlineStorage.requestSync('sync-issues');
        }
      }

      setLastSyncTime(new Date());
      await refreshPendingCounts();
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setIsSyncing(false);
    }
  }, [isOnline, isSyncing, pendingMortality, pendingIssues, refreshPendingCounts]);

  return {
    isOnline,
    pendingMortality,
    pendingIssues,
    totalPending: pendingMortality + pendingIssues,
    lastSyncTime,
    isSyncing,
    sync,
    refreshPendingCounts,
  };
};

export default useOffline;

