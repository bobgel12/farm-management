import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Card,
  CardContent,
  Typography,
  Box,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore,
  Settings,
  IntegrationInstructions,
  CheckCircle,
  Error as ErrorIcon,
  Warning,
  Refresh,
  Sync,
  Visibility,
  VisibilityOff,
  History,
  HealthAndSafety,
} from '@mui/icons-material';

interface IntegrationManagementProps {
  open: boolean;
  onClose: () => void;
  farm: {
    id: number;
    name: string;
    integration_type: 'none' | 'rotem' | 'future_system';
    integration_status: 'active' | 'inactive' | 'error' | 'not_configured';
    has_system_integration: boolean;
    last_sync?: string;
    rotem_username?: string;
    rotem_password?: string;
  };
  onUpdateIntegration: (farmId: number, integrationData: any) => Promise<void>;
  onTestConnection: (farmId: number) => Promise<boolean>;
  onSyncData: (farmId: number) => Promise<void>;
}

interface IntegrationLog {
  id: number;
  action: string;
  status: string;
  message: string;
  timestamp: string;
  execution_time?: number;
  data_points_processed: number;
}

interface IntegrationError {
  id: number;
  error_type: string;
  error_message: string;
  created_at: string;
  resolved: boolean;
  resolved_at?: string;
}

const IntegrationManagement: React.FC<IntegrationManagementProps> = ({
  open,
  onClose,
  farm,
  onUpdateIntegration,
  onTestConnection,
  onSyncData,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [integrationType, setIntegrationType] = useState(farm.integration_type);
  const [rotemCredentials, setRotemCredentials] = useState({
    username: farm.rotem_username || '',
    password: farm.rotem_password || '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [connectionError, setConnectionError] = useState('');
  const [syncing, setSyncing] = useState(false);
  const [integrationHealth, setIntegrationHealth] = useState<any>(null);
  const [integrationLogs, setIntegrationLogs] = useState<IntegrationLog[]>([]);
  const [integrationErrors, setIntegrationErrors] = useState<IntegrationError[]>([]);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [loadingLogs, setLoadingLogs] = useState(false);

  useEffect(() => {
    if (open) {
      setIntegrationType(farm.integration_type);
      setRotemCredentials({
        username: farm.rotem_username || '',
        password: farm.rotem_password || '',
      });
      setConnectionStatus('idle');
      setConnectionError('');
      
      if (farm.has_system_integration) {
        fetchIntegrationData();
      }
    }
  }, [open, farm]);

  const fetchIntegrationData = async () => {
    setLoadingHealth(true);
    setLoadingLogs(true);
    
    try {
      // Fetch integration health
      const healthResponse = await fetch(`/api/farms/${farm.id}/integration_status/`, {
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setIntegrationHealth(healthData.health_details);
      }

      // Fetch integration logs
      const logsResponse = await fetch(`/api/integrations/logs/?farm_id=${farm.id}`, {
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });
      if (logsResponse.ok) {
        const logsData = await logsResponse.json();
        setIntegrationLogs(logsData.results || []);
      }

      // Fetch integration errors
      const errorsResponse = await fetch(`/api/integrations/errors/?farm_id=${farm.id}`, {
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });
      if (errorsResponse.ok) {
        const errorsData = await errorsResponse.json();
        setIntegrationErrors(errorsData.results || []);
      }
    } catch (error) {
      console.error('Failed to fetch integration data:', error);
    } finally {
      setLoadingHealth(false);
      setLoadingLogs(false);
    }
  };

  const handleTestConnection = async () => {
    if (integrationType !== 'rotem') return;
    
    setTestingConnection(true);
    setConnectionStatus('testing');
    setConnectionError('');

    try {
      const success = await onTestConnection(farm.id);
      if (success) {
        setConnectionStatus('success');
        setConnectionError('');
      } else {
        setConnectionStatus('error');
        setConnectionError('Connection test failed');
      }
    } catch (error) {
      setConnectionStatus('error');
      setConnectionError('Connection test failed');
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSaveConfiguration = async () => {
    setTestingConnection(true);
    setConnectionStatus('testing');
    setConnectionError('');
    
    try {
      const integrationData = {
        integration_type: integrationType,
        ...(integrationType === 'rotem' && {
          username: rotemCredentials.username,
          password: rotemCredentials.password,
        }),
      };
      
      await onUpdateIntegration(farm.id, integrationData);
      setConnectionStatus('success');
      setConnectionError('');
      onClose();
    } catch (error) {
      setConnectionStatus('error');
      setConnectionError(error instanceof Error ? error.message : 'Failed to save configuration');
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSyncData = async () => {
    setSyncing(true);
    try {
      await onSyncData(farm.id);
      await fetchIntegrationData(); // Refresh data after sync
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return 'success';
      case 'failed': return 'error';
      case 'partial': return 'warning';
      case 'in_progress': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle />;
      case 'failed': return <ErrorIcon />;
      case 'partial': return <Warning />;
      case 'in_progress': return <CircularProgress size={16} />;
      default: return <Settings />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const tabs = [
    { label: 'Configuration', icon: <Settings /> },
    { label: 'Health & Status', icon: <HealthAndSafety /> },
    { label: 'Activity Logs', icon: <History /> },
  ];

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: '90vh',
          minHeight: '70vh'
        }
      }}
    >
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            Integration Management - {farm.name}
          </Typography>
          <Box display="flex" gap={1}>
            {farm.has_system_integration && (
              <Button
                variant="outlined"
                startIcon={<Sync />}
                onClick={handleSyncData}
                disabled={syncing}
                size="small"
              >
                {syncing ? 'Syncing...' : 'Sync Now'}
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchIntegrationData}
              size="small"
            >
              Refresh
            </Button>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        {/* Tab Navigation */}
        <Box display="flex" gap={1} mb={3} borderBottom={1} borderColor="divider">
          {tabs.map((tab, index) => (
            <Button
              key={index}
              onClick={() => setActiveTab(index)}
              variant={activeTab === index ? 'contained' : 'text'}
              startIcon={tab.icon}
              sx={{ mb: -1 }}
            >
              {tab.label}
            </Button>
          ))}
        </Box>

        {/* Configuration Tab */}
        {activeTab === 0 && (
          <Box>
            <FormControl component="fieldset" sx={{ mb: 3 }}>
              <FormLabel component="legend" sx={{ fontSize: '1.1rem', fontWeight: 600, mb: 2 }}>
                System Integration Type
              </FormLabel>
              <RadioGroup
                value={integrationType}
                onChange={(e) => setIntegrationType(e.target.value as any)}
              >
                <FormControlLabel
                  value="none"
                  control={<Radio />}
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Settings color="action" />
                      <Box>
                        <Typography variant="body1" fontWeight={500}>
                          No Integration (Manual Management)
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Manage your farm manually without external system integration
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
                <FormControlLabel
                  value="rotem"
                  control={<Radio />}
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <IntegrationInstructions color="primary" />
                      <Box>
                        <Typography variant="body1" fontWeight={500}>
                          Rotem System Integration
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Connect to Rotem monitoring system for automated data collection
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            {integrationType === 'rotem' && (
              <Card sx={{ p: 2, border: '1px solid', borderColor: 'primary.main' }}>
                <Typography variant="h6" gutterBottom>
                  Rotem System Configuration
                </Typography>
                <Box display="flex" flexDirection="column" gap={2}>
                  <TextField
                    label="Rotem Username"
                    fullWidth
                    value={rotemCredentials.username}
                    onChange={(e) => setRotemCredentials(prev => ({ ...prev, username: e.target.value }))}
                  />
                  <TextField
                    label="Rotem Password"
                    fullWidth
                    type={showPassword ? 'text' : 'password'}
                    value={rotemCredentials.password}
                    onChange={(e) => setRotemCredentials(prev => ({ ...prev, password: e.target.value }))}
                    InputProps={{
                      endAdornment: (
                        <IconButton
                          onClick={() => setShowPassword(!showPassword)}
                          edge="end"
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      ),
                    }}
                  />
                  <Box display="flex" gap={1}>
                    {connectionStatus === 'success' && (
                      <Chip
                        label="Connection Verified"
                        color="success"
                        icon={<CheckCircle />}
                      />
                    )}
                    {connectionStatus === 'error' && (
                      <Chip
                        label="Connection Failed"
                        color="error"
                        icon={<ErrorIcon />}
                      />
                    )}
                    {connectionStatus === 'testing' && (
                      <Chip
                        label="Testing Connection..."
                        color="info"
                        icon={<CircularProgress size={16} />}
                      />
                    )}
                  </Box>
                  {connectionError && (
                    <Alert severity="error">
                      {connectionError}
                    </Alert>
                  )}
                </Box>
              </Card>
            )}
          </Box>
        )}

        {/* Health & Status Tab */}
        {activeTab === 1 && (
          <Box>
            {loadingHealth ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : (
              <Box display="flex" flexDirection="column" gap={2}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Current Status
                    </Typography>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      <Chip
                        label={`Type: ${integrationType === 'none' ? 'Manual' : 'Rotem'}`}
                        color={integrationType === 'none' ? 'default' : 'primary'}
                        icon={integrationType === 'none' ? <Settings /> : <IntegrationInstructions />}
                      />
                      <Chip
                        label={`Status: ${farm.integration_status}`}
                        color={
                          farm.integration_status === 'active' ? 'success' :
                          farm.integration_status === 'error' ? 'error' :
                          farm.integration_status === 'inactive' ? 'warning' : 'default'
                        }
                        icon={
                          farm.integration_status === 'active' ? <CheckCircle /> :
                          farm.integration_status === 'error' ? <ErrorIcon /> :
                          farm.integration_status === 'inactive' ? <Warning /> : <Settings />
                        }
                      />
                      {farm.last_sync && (
                        <Chip
                          label={`Last Sync: ${formatTimestamp(farm.last_sync)}`}
                          color="info"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  </CardContent>
                </Card>

                {integrationHealth && (
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Health Metrics
                      </Typography>
                      <Box display="flex" gap={2} flexWrap="wrap">
                        <Chip
                          label={`Success Rate: ${integrationHealth.success_rate_24h?.toFixed(1) || 0}%`}
                          color={integrationHealth.success_rate_24h > 90 ? 'success' : 'warning'}
                        />
                        <Chip
                          label={`Consecutive Failures: ${integrationHealth.consecutive_failures || 0}`}
                          color={integrationHealth.consecutive_failures > 3 ? 'error' : 'default'}
                        />
                        {integrationHealth.average_response_time && (
                          <Chip
                            label={`Avg Response: ${integrationHealth.average_response_time.toFixed(2)}s`}
                            color="info"
                          />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                )}

                {integrationErrors.length > 0 && (
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Recent Errors ({integrationErrors.length})
                      </Typography>
                      <Box display="flex" flexDirection="column" gap={1}>
                        {integrationErrors.slice(0, 3).map((error) => (
                          <Alert
                            key={error.id}
                            severity="error"
                            variant="outlined"
                          >
                            <Typography variant="body2">
                              <strong>{error.error_type}:</strong> {error.error_message}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {formatTimestamp(error.created_at)}
                            </Typography>
                          </Alert>
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                )}
              </Box>
            )}
          </Box>
        )}

        {/* Activity Logs Tab */}
        {activeTab === 2 && (
          <Box>
            {loadingLogs ? (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            ) : (
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Action</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Message</TableCell>
                      <TableCell>Data Points</TableCell>
                      <TableCell>Execution Time</TableCell>
                      <TableCell>Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {integrationLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell>{log.action}</TableCell>
                        <TableCell>
                          <Chip
                            label={log.status}
                            color={getStatusColor(log.status)}
                            icon={getStatusIcon(log.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{log.message}</TableCell>
                        <TableCell>{log.data_points_processed}</TableCell>
                        <TableCell>
                          {log.execution_time ? `${log.execution_time.toFixed(2)}s` : '-'}
                        </TableCell>
                        <TableCell>{formatTimestamp(log.timestamp)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Close
        </Button>
        {activeTab === 0 && (
          <Button
            onClick={handleSaveConfiguration}
            variant="contained"
            disabled={testingConnection || (integrationType === 'rotem' && (!rotemCredentials.username || !rotemCredentials.password))}
            startIcon={testingConnection ? <CircularProgress size={20} /> : undefined}
          >
            {testingConnection ? 'Testing & Saving...' : 'Save Configuration'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default IntegrationManagement;
