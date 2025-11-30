import React from 'react';
import {
  Box,
  Chip,
  Badge,
  Tooltip,
  IconButton,
  Popover,
} from '@mui/material';
import {
  CloudOff as OfflineIcon,
  CloudDone as OnlineIcon,
  Sync as PendingIcon,
} from '@mui/icons-material';
import { useOffline } from '../../hooks/useOffline';
import { OfflineQueue } from './OfflineQueue';

export const OfflineIndicator: React.FC = () => {
  const { isOnline, totalPending, isSyncing } = useOffline();
  const [anchorEl, setAnchorEl] = React.useState<HTMLButtonElement | null>(null);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  // Don't show when online and no pending items
  if (isOnline && totalPending === 0) {
    return null;
  }

  return (
    <>
      <Tooltip title={isOnline ? `${totalPending} pending` : 'Offline'}>
        <IconButton
          onClick={handleClick}
          sx={{
            color: isOnline ? 'warning.main' : 'error.main',
          }}
        >
          <Badge
            badgeContent={totalPending}
            color="error"
            invisible={totalPending === 0}
          >
            {isSyncing ? (
              <PendingIcon sx={{ animation: 'spin 1s linear infinite' }} />
            ) : isOnline ? (
              <PendingIcon />
            ) : (
              <OfflineIcon />
            )}
          </Badge>
        </IconButton>
      </Tooltip>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        PaperProps={{
          sx: { width: 320 },
        }}
      >
        <OfflineQueue onClose={handleClose} />
      </Popover>

      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}
      </style>
    </>
  );
};

export default OfflineIndicator;

