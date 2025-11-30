/**
 * IndexedDB wrapper for offline data storage
 * Manages pending submissions for mortality records and issues
 */

const DB_NAME = 'farm-manager-offline';
const DB_VERSION = 1;

interface PendingRecord<T> {
  id?: number;
  data: T;
  timestamp: number;
  retries: number;
}

type StoreName = 'pendingMortality' | 'pendingIssues' | 'cachedData';

class OfflineStorage {
  private db: IDBDatabase | null = null;
  private dbPromise: Promise<IDBDatabase> | null = null;

  async init(): Promise<IDBDatabase> {
    if (this.db) return this.db;
    if (this.dbPromise) return this.dbPromise;

    this.dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => {
        console.error('Failed to open IndexedDB:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve(request.result);
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object stores
        if (!db.objectStoreNames.contains('pendingMortality')) {
          const store = db.createObjectStore('pendingMortality', {
            keyPath: 'id',
            autoIncrement: true,
          });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains('pendingIssues')) {
          const store = db.createObjectStore('pendingIssues', {
            keyPath: 'id',
            autoIncrement: true,
          });
          store.createIndex('timestamp', 'timestamp', { unique: false });
        }

        if (!db.objectStoreNames.contains('cachedData')) {
          const store = db.createObjectStore('cachedData', { keyPath: 'key' });
          store.createIndex('expiry', 'expiry', { unique: false });
        }
      };
    });

    return this.dbPromise;
  }

  async add<T>(storeName: StoreName, data: T): Promise<number> {
    const db = await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      
      const record: PendingRecord<T> = {
        data,
        timestamp: Date.now(),
        retries: 0,
      };
      
      const request = store.add(record);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result as number);
    });
  }

  async getAll<T>(storeName: StoreName): Promise<PendingRecord<T>[]> {
    const db = await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.getAll();
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  async remove(storeName: StoreName, id: number): Promise<void> {
    const db = await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.delete(id);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async update<T>(storeName: StoreName, id: number, updates: Partial<PendingRecord<T>>): Promise<void> {
    const db = await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      
      const getRequest = store.get(id);
      
      getRequest.onsuccess = () => {
        const record = getRequest.result;
        if (record) {
          const updated = { ...record, ...updates };
          const putRequest = store.put(updated);
          putRequest.onerror = () => reject(putRequest.error);
          putRequest.onsuccess = () => resolve();
        } else {
          reject(new Error('Record not found'));
        }
      };
      
      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  async count(storeName: StoreName): Promise<number> {
    const db = await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readonly');
      const store = transaction.objectStore(storeName);
      const request = store.count();
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);
    });
  }

  async clear(storeName: StoreName): Promise<void> {
    const db = await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction(storeName, 'readwrite');
      const store = transaction.objectStore(storeName);
      const request = store.clear();
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  // Cache management for read data
  async cacheData(key: string, data: any, expiryMs: number = 3600000): Promise<void> {
    const db = await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('cachedData', 'readwrite');
      const store = transaction.objectStore('cachedData');
      
      const record = {
        key,
        data,
        expiry: Date.now() + expiryMs,
      };
      
      const request = store.put(record);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  }

  async getCachedData<T>(key: string): Promise<T | null> {
    const db = await this.init();
    
    return new Promise((resolve, reject) => {
      const transaction = db.transaction('cachedData', 'readonly');
      const store = transaction.objectStore('cachedData');
      const request = store.get(key);
      
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const record = request.result;
        if (record && record.expiry > Date.now()) {
          resolve(record.data);
        } else {
          resolve(null);
        }
      };
    });
  }

  // Request background sync
  async requestSync(tag: string): Promise<void> {
    if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
      const registration = await navigator.serviceWorker.ready;
      await (registration as any).sync.register(tag);
    }
  }
}

export const offlineStorage = new OfflineStorage();

// Convenience functions
export const addPendingMortality = (data: any) => 
  offlineStorage.add('pendingMortality', data);

export const addPendingIssue = (data: any) => 
  offlineStorage.add('pendingIssues', data);

export const getPendingMortality = () => 
  offlineStorage.getAll('pendingMortality');

export const getPendingIssues = () => 
  offlineStorage.getAll('pendingIssues');

export const removePendingMortality = (id: number) => 
  offlineStorage.remove('pendingMortality', id);

export const removePendingIssue = (id: number) => 
  offlineStorage.remove('pendingIssues', id);

export const getPendingCounts = async () => ({
  mortality: await offlineStorage.count('pendingMortality'),
  issues: await offlineStorage.count('pendingIssues'),
});

export default offlineStorage;

