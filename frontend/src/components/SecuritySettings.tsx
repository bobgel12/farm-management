import React, { useEffect, useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Security,
  Password,
  Shield,
  Warning,
  CheckCircle,
  Info,
  Refresh,
} from '@mui/icons-material';
import PasswordChange from './PasswordChange';
import { hardRefreshApp } from '../serviceWorkerRegistration';

const SecuritySettings: React.FC = () => {
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [passwordChangeSuccess, setPasswordChangeSuccess] = useState(false);
  const [isStandalonePwa, setIsStandalonePwa] = useState(false);
  const [showHardRefreshConfirm, setShowHardRefreshConfirm] = useState(false);
  const [hardRefreshLoading, setHardRefreshLoading] = useState(false);
  const [hardRefreshError, setHardRefreshError] = useState<string | null>(null);

  const handlePasswordChangeSuccess = () => {
    setPasswordChangeSuccess(true);
    setShowPasswordChange(false);
    setTimeout(() => setPasswordChangeSuccess(false), 5000);
  };

  useEffect(() => {
    const isStandaloneDisplayMode = window.matchMedia('(display-mode: standalone)').matches;
    const isIosStandalone = Boolean((window.navigator as Navigator & { standalone?: boolean }).standalone);
    setIsStandalonePwa(isStandaloneDisplayMode || isIosStandalone);
  }, []);

  const handleHardRefreshConfirm = async () => {
    setHardRefreshLoading(true);
    setHardRefreshError(null);
    try {
      await hardRefreshApp();
    } catch (error) {
      console.error('Hard refresh failed:', error);
      setHardRefreshError('Unable to start hard refresh. Please try again.');
      setHardRefreshLoading(false);
      setShowHardRefreshConfirm(false);
    }
  };

  const securityFeatures = [
    {
      icon: <Shield />,
      title: 'Rate Limiting',
      description: 'Login attempts are limited to prevent brute force attacks',
      status: 'active',
      color: 'success' as const,
    },
    {
      icon: <Password />,
      title: 'Password Strength',
      description: 'Strong password requirements enforced',
      status: 'active',
      color: 'success' as const,
    },
    {
      icon: <Security />,
      title: 'Token-based Authentication',
      description: 'Secure API authentication with tokens',
      status: 'active',
      color: 'success' as const,
    },
    {
      icon: <Warning />,
      title: 'Security Monitoring',
      description: 'All login attempts and security events are logged',
      status: 'active',
      color: 'success' as const,
    },
  ];

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" sx={{ mb: 3, color: '#2c5aa0' }}>
        🔒 Security Settings
      </Typography>

      {passwordChangeSuccess && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Password changed successfully!
        </Alert>
      )}

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Password />
          Password Management
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Keep your account secure by regularly updating your password.
        </Typography>
        <Button
          variant="contained"
          onClick={() => setShowPasswordChange(true)}
          sx={{ bgcolor: '#2c5aa0' }}
        >
          Change Password
        </Button>
      </Paper>

      {isStandalonePwa && (
        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Refresh />
            App Update Recovery
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            If the installed app appears outdated, use hard refresh to clear local app cache and fetch the latest version.
          </Typography>
          {hardRefreshError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {hardRefreshError}
            </Alert>
          )}
          <Button
            variant="outlined"
            color="warning"
            startIcon={hardRefreshLoading ? <CircularProgress size={16} /> : <Refresh />}
            onClick={() => setShowHardRefreshConfirm(true)}
            disabled={hardRefreshLoading}
          >
            Hard Refresh App
          </Button>
        </Paper>
      )}

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Security />
          Security Features
        </Typography>
        <List>
          {securityFeatures.map((feature, index) => (
            <React.Fragment key={index}>
              <ListItem>
                <ListItemIcon sx={{ color: '#2c5aa0' }}>
                  {feature.icon}
                </ListItemIcon>
                <ListItemText
                  primary={feature.title}
                  secondary={feature.description}
                />
                <Chip
                  label={feature.status}
                  color={feature.color}
                  size="small"
                  icon={<CheckCircle />}
                />
              </ListItem>
              {index < securityFeatures.length - 1 && <Divider />}
            </React.Fragment>
          ))}
        </List>
      </Paper>

      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <Info />
          Security Tips
        </Typography>
        <Box component="ul" sx={{ pl: 2, m: 0 }}>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Use a strong, unique password with at least 8 characters
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Include both letters and numbers in your password
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Avoid using common passwords or personal information
          </Typography>
          <Typography component="li" variant="body2" sx={{ mb: 1 }}>
            Log out when using shared computers
          </Typography>
          <Typography component="li" variant="body2">
            Report any suspicious activity immediately
          </Typography>
        </Box>
      </Paper>

      <Dialog
        open={showPasswordChange}
        onClose={() => setShowPasswordChange(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <PasswordChange
            onSuccess={handlePasswordChangeSuccess}
            onCancel={() => setShowPasswordChange(false)}
          />
        </DialogContent>
      </Dialog>

      <Dialog
        open={showHardRefreshConfirm}
        onClose={() => !hardRefreshLoading && setShowHardRefreshConfirm(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Hard Refresh App?</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will clear service worker and cached app files, then reload the app.
          </Alert>
          <Typography variant="body2" color="text.secondary">
            Use this when your installed PWA appears stuck on an old version.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowHardRefreshConfirm(false)} disabled={hardRefreshLoading}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="warning"
            onClick={handleHardRefreshConfirm}
            disabled={hardRefreshLoading}
            startIcon={hardRefreshLoading ? <CircularProgress size={16} /> : <Refresh />}
          >
            {hardRefreshLoading ? 'Refreshing...' : 'Confirm Hard Refresh'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SecuritySettings;
