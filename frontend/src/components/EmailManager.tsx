import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Snackbar,
} from '@mui/material';
import {
  Email as EmailIcon,
  Send as SendIcon,
  History as HistoryIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import api from '../services/api';

interface EmailHistory {
  id: number;
  farm_name: string;
  sent_date: string;
  tasks_count: number;
  status: string;
}

interface EmailManagerProps {
  farmId?: number;
  farmName?: string;
}

const EmailManager: React.FC<EmailManagerProps> = ({ farmId, farmName }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [testEmailDialog, setTestEmailDialog] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [emailHistory, setEmailHistory] = useState<EmailHistory[]>([]);
  const [historyDialog, setHistoryDialog] = useState(false);

  const sendDailyTasks = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const requestData = farmId ? { farm_id: farmId } : {};
      const response = await api.post('/tasks/send-daily-tasks/', requestData);
      setSuccess(response.data.message);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to send daily tasks');
    } finally {
      setLoading(false);
    }
  };

  const sendTestEmail = async () => {
    if (!testEmail.trim()) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.post('/tasks/send-test-email/', {
        farm_id: farmId || 1,
        test_email: testEmail.trim(),
      });
      setSuccess(response.data.message);
      setTestEmailDialog(false);
      setTestEmail('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to send test email');
    } finally {
      setLoading(false);
    }
  };

  const fetchEmailHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = farmId ? `?farm_id=${farmId}` : '';
      const response = await api.get(`/tasks/email-history/${params}`);
      setEmailHistory(response.data);
      setHistoryDialog(true);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch email history');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📧 Email Management
            {farmName && ` - ${farmName}`}
          </Typography>
          
          <Typography variant="body2" color="textSecondary" paragraph>
            {farmId 
              ? `Send daily task reminders and test emails to workers for ${farmName || 'this farm'}.`
              : 'Send daily task reminders and test emails to workers for all farms.'
            }
          </Typography>

          <Box display="flex" gap={2} flexWrap="wrap" mb={2}>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              onClick={sendDailyTasks}
              disabled={loading}
              color="primary"
            >
              {farmId ? 'Send Farm Tasks' : 'Send All Farm Tasks'}
            </Button>

            <Button
              variant="outlined"
              startIcon={<EmailIcon />}
              onClick={() => setTestEmailDialog(true)}
              disabled={loading}
            >
              Send Test Email
            </Button>

            <Button
              variant="outlined"
              startIcon={<HistoryIcon />}
              onClick={fetchEmailHistory}
              disabled={loading}
            >
              View History
            </Button>
          </Box>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Daily Tasks:</strong> {farmId 
                ? `Sends today's and tomorrow's tasks for all houses in ${farmName || 'this farm'} to active workers.`
                : 'Sends today\'s and tomorrow\'s tasks for all farms to their respective active workers.'
              }
              <br />
              <strong>Test Email:</strong> Sends a test email to verify email configuration.
              <br />
              <strong>History:</strong> View previously sent emails and their status.
            </Typography>
          </Alert>
        </CardContent>
      </Card>

      {/* Test Email Dialog */}
      <Dialog open={testEmailDialog} onClose={() => setTestEmailDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send Test Email</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Email Address"
            fullWidth
            variant="outlined"
            type="email"
            value={testEmail}
            onChange={(e) => setTestEmail(e.target.value)}
            placeholder="worker@example.com"
            helperText="Enter the email address to send the test email to"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestEmailDialog(false)}>Cancel</Button>
          <Button
            onClick={sendTestEmail}
            variant="contained"
            disabled={loading || !testEmail.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
          >
            Send Test Email
          </Button>
        </DialogActions>
      </Dialog>

      {/* Email History Dialog */}
      <Dialog open={historyDialog} onClose={() => setHistoryDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Email History
          <IconButton
            onClick={() => setHistoryDialog(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {emailHistory.length > 0 ? (
            <List>
              {emailHistory.map((email) => (
                <ListItem key={email.id} divider>
                  <ListItemText
                    primary={email.farm_name}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Sent: {new Date(email.sent_date).toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Tasks: {email.tasks_count}
                        </Typography>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Chip
                      label={email.status}
                      color={email.status === 'sent' ? 'success' : 'default'}
                      size="small"
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography color="textSecondary" align="center" sx={{ py: 4 }}>
              No email history found
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbar */}
      <Snackbar
        open={!!success || !!error}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={success ? 'success' : 'error'}
          sx={{ width: '100%' }}
        >
          {success || error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default EmailManager;
