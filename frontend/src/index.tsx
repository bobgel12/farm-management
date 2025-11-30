import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Register service worker for PWA functionality
serviceWorkerRegistration.register({
  onUpdate: (registration) => {
    console.log('New version available! Refresh to update.');
    // Optionally show a notification to the user
    if (window.confirm('A new version is available. Refresh to update?')) {
      registration.waiting?.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  },
  onSuccess: () => {
    console.log('App is ready for offline use.');
  },
});
