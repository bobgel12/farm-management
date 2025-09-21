import React, { useState, useEffect } from 'react';
import {
  IconButton,
  Tooltip,
  Badge,
  Menu,
  MenuItem,
  Typography,
  Box,
  CircularProgress,
} from '@mui/material';
import {
  Email as EmailIcon,
  Send as SendIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import api from '../services/api';

interface EmailStatusProps {
  onSendEmail?: () => void;
  farmId?: number;
}

const EmailStatus: React.FC<EmailStatusProps> = ({ onSendEmail, farmId }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [loading, setLoading] = useState(false);
  const [lastEmailSent, setLastEmailSent] = useState<string | null>(null);
  const [emailCount, setEmailCount] = useState(0);

  useEffect(() => {
    fetchEmailStatus();
  }, []);

  const fetchEmailStatus = async () => {
    try {
      const response = await api.get('/tasks/email-history/');
      const emails = response.data;
      if (emails.length > 0) {
        const latestEmail = emails[0];
        setLastEmailSent(latestEmail.sent_date);
        setEmailCount(emails.length);
      }
    } catch (error) {
      console.error('Failed to fetch email status:', error);
    }
  };

  const handleSendDailyTasks = async () => {
    setLoading(true);
    try {
      const requestData = farmId ? { farm_id: farmId } : {};
      await api.post('/tasks/send-daily-tasks/', requestData);
      setLastEmailSent(new Date().toISOString());
      setEmailCount(prev => prev + 1);
      if (onSendEmail) {
        onSendEmail();
      }
    } catch (error) {
      console.error('Failed to send daily tasks:', error);
    } finally {
      setLoading(false);
      setAnchorEl(null);
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getStatusColor = () => {
    if (loading) return 'default';
    if (lastEmailSent) {
      const lastSent = new Date(lastEmailSent);
      const now = new Date();
      const hoursDiff = (now.getTime() - lastSent.getTime()) / (1000 * 60 * 60);
      
      if (hoursDiff < 24) return 'success';
      if (hoursDiff < 48) return 'warning';
      return 'error';
    }
    return 'default';
  };

  const getStatusText = () => {
    if (loading) return 'Sending...';
    if (lastEmailSent) {
      const lastSent = new Date(lastEmailSent);
      const now = new Date();
      const hoursDiff = (now.getTime() - lastSent.getTime()) / (1000 * 60 * 60);
      
      if (hoursDiff < 1) return 'Sent recently';
      if (hoursDiff < 24) return `Sent ${Math.floor(hoursDiff)}h ago`;
      return `Sent ${Math.floor(hoursDiff / 24)}d ago`;
    }
    return 'Never sent';
  };

  return (
    <>
      <Tooltip title="Email Status & Actions">
        <IconButton
          onClick={handleMenuOpen}
          color="inherit"
          sx={{ position: 'relative' }}
        >
          <Badge badgeContent={emailCount} color="primary">
            <EmailIcon />
          </Badge>
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={handleSendDailyTasks} disabled={loading}>
          <Box display="flex" alignItems="center" gap={1}>
            {loading ? (
              <CircularProgress size={20} />
            ) : (
              <SendIcon />
            )}
            <Typography>{farmId ? 'Send Farm Tasks' : 'Send All Farm Tasks'}</Typography>
          </Box>
        </MenuItem>

        <MenuItem onClick={handleMenuClose}>
          <Box display="flex" alignItems="center" gap={1}>
            <CheckCircleIcon color={getStatusColor() as any} />
            <Box>
              <Typography variant="body2">
                {getStatusText()}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {emailCount} emails sent
              </Typography>
            </Box>
          </Box>
        </MenuItem>
      </Menu>
    </>
  );
};

export default EmailStatus;
