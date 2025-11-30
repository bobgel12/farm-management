import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Button,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  Sync as SyncIcon,
  Delete as DeleteIcon,
  CloudOff as OfflineIcon,
  CloudDone as OnlineIcon,
} from '@mui/icons-material';
import { useOffline } from '../../hooks/useOffline';

interface OfflineQueueProps {
  onClose?: () => void;
}

export const OfflineQueue: React.FC<OfflineQueueProps> = ({ onClose }) => {
  const {
    isOnline,
    pendingMortality,
    pendingIssues,
    totalPending,
    lastSyncTime,
    isSyncing,
    sync,
  } = useOffline();

  const formatTime = (date: Date | null) => {
    if (!date) return 'Never';
    return date.toLocaleString();
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isOnline ? (
              <OnlineIcon color="success" />
            ) : (
              <OfflineIcon color="error" />
            )}
            Sync Status
          </Typography>
          
          <Chip
            label={isOnline ? 'Online' : 'Offline'}
            color={isOnline ? 'success' : 'error'}
            size="small"
          />
        </Box>

        {!isOnline && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            You are currently offline. Data will be synced when you reconnect.
          </Alert>
        )}

        {totalPending > 0 ? (
          <>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Pending Items ({totalPending})
            </Typography>
            
            <List dense>
              {pendingMortality > 0 && (
                <ListItem>
                  <ListItemText
                    primary="Mortality Records"
                    secondary={`${pendingMortality} record${pendingMortality > 1 ? 's' : ''} waiting to sync`}
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={pendingMortality}
                      size="small"
                      color="error"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              )}
              
              {pendingIssues > 0 && (
                <ListItem>
                  <ListItemText
                    primary="Issue Reports"
                    secondary={`${pendingIssues} issue${pendingIssues > 1 ? 's' : ''} waiting to sync`}
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={pendingIssues}
                      size="small"
                      color="warning"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              )}
            </List>

            <Divider sx={{ my: 2 }} />

            <Button
              fullWidth
              variant="contained"
              startIcon={isSyncing ? <CircularProgress size={20} color="inherit" /> : <SyncIcon />}
              onClick={sync}
              disabled={!isOnline || isSyncing}
            >
              {isSyncing ? 'Syncing...' : 'Sync Now'}
            </Button>
          </>
        ) : (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <OnlineIcon sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
            <Typography color="text.secondary">
              All data is synced
            </Typography>
          </Box>
        )}

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
          Last sync: {formatTime(lastSyncTime)}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default OfflineQueue;

