import React, { useState, useEffect } from 'react';
import {
  Snackbar,
  Button,
  Box,
  Typography,
  IconButton,
  Paper,
  Slide,
} from '@mui/material';
import {
  GetApp as InstallIcon,
  Close as CloseIcon,
  PhoneAndroid as MobileIcon,
} from '@mui/icons-material';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

export const InstallPrompt: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);

  useEffect(() => {
    // Check if already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
      return;
    }

    // Check if previously dismissed
    const dismissed = localStorage.getItem('pwa-install-dismissed');
    if (dismissed) {
      const dismissedTime = parseInt(dismissed, 10);
      // Don't show again for 7 days
      if (Date.now() - dismissedTime < 7 * 24 * 60 * 60 * 1000) {
        return;
      }
    }

    // Listen for the beforeinstallprompt event
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      
      // Show prompt after a delay
      setTimeout(() => {
        setShowPrompt(true);
      }, 5000);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);

    // Check if app was installed
    window.addEventListener('appinstalled', () => {
      setIsInstalled(true);
      setShowPrompt(false);
      setDeferredPrompt(null);
    });

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('PWA installed');
      setIsInstalled(true);
    }

    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-install-dismissed', Date.now().toString());
  };

  if (isInstalled || !showPrompt) {
    return null;
  }

  return (
    <Snackbar
      open={showPrompt}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      TransitionComponent={(props) => <Slide {...props} direction="up" />}
    >
      <Paper
        elevation={6}
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          maxWidth: 400,
          borderRadius: 2,
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
        }}
      >
        <MobileIcon sx={{ fontSize: 40 }} />
        
        <Box sx={{ flex: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            Install Farm Manager
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.9 }}>
            Add to your home screen for quick access and offline use
          </Typography>
        </Box>

        <Button
          variant="contained"
          size="small"
          onClick={handleInstall}
          startIcon={<InstallIcon />}
          sx={{
            bgcolor: 'white',
            color: 'primary.main',
            '&:hover': { bgcolor: 'grey.100' },
          }}
        >
          Install
        </Button>

        <IconButton
          size="small"
          onClick={handleDismiss}
          sx={{ color: 'inherit' }}
        >
          <CloseIcon />
        </IconButton>
      </Paper>
    </Snackbar>
  );
};

export default InstallPrompt;

