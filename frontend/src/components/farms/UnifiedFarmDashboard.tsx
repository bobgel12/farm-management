import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
  IconButton,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import {
  Settings,
  IntegrationInstructions,
  Sync,
  Refresh,
  CheckCircle,
  Error,
  Warning,
  Home,
  TrendingUp,
  Water,
  Thermostat,
  Speed,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface Farm {
  id: number;
  name: string;
  location: string;
  description?: string;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  integration_type: 'none' | 'rotem' | 'future_system';
  integration_status: 'active' | 'inactive' | 'error' | 'not_configured';
  has_system_integration: boolean;
  last_sync?: string;
  houses: House[];
  workers: Worker[];
}

interface House {
  id: number;
  house_number: number;
  capacity: number;
  is_integrated: boolean;
  current_age_days: number;
  batch_start_date?: string;
  expected_harvest_date?: string;
  is_active: boolean;
  last_system_sync?: string;
}

interface Worker {
  id: number;
  name: string;
  email: string;
  phone: string;
  role: string;
  is_active: boolean;
}

interface IntegrationHealth {
  is_healthy: boolean;
  success_rate_24h: number;
  consecutive_failures: number;
  average_response_time?: number;
  last_successful_sync?: string;
  last_attempted_sync?: string;
}

interface UnifiedFarmDashboardProps {
  farm: Farm;
  onRefresh?: () => void;
  onConfigureIntegration?: (farmId: number) => void;
  onSyncData?: (farmId: number) => void;
}

const UnifiedFarmDashboard: React.FC<UnifiedFarmDashboardProps> = ({
  farm,
  onRefresh,
  onConfigureIntegration,
  onSyncData,
}) => {
  const navigate = useNavigate();
  const [integrationHealth, setIntegrationHealth] = useState<IntegrationHealth | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);

  useEffect(() => {
    if (farm.has_system_integration) {
      fetchIntegrationHealth();
    }
  }, [farm.id, farm.has_system_integration]);

  const fetchIntegrationHealth = async () => {
    setLoadingHealth(true);
    try {
      const response = await fetch(`/api/farms/${farm.id}/integration_status/`, {
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setIntegrationHealth(data.health_details);
      }
    } catch (error) {
      console.error('Failed to fetch integration health:', error);
    } finally {
      setLoadingHealth(false);
    }
  };

  const handleSyncData = async () => {
    if (!onSyncData) return;
    
    setSyncing(true);
    try {
      await onSyncData(farm.id);
      setSyncDialogOpen(false);
      if (onRefresh) onRefresh();
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(false);
    }
  };

  const getIntegrationStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'error': return 'error';
      case 'inactive': return 'warning';
      default: return 'default';
    }
  };

  const getIntegrationStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle />;
      case 'error': return <Error />;
      case 'inactive': return <Warning />;
      default: return <Settings />;
    }
  };

  const formatLastSync = (lastSync?: string) => {
    if (!lastSync) return 'Never';
    const date = new Date(lastSync);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const getHouseStatusColor = (house: House) => {
    if (!house.is_active) return 'default';
    if (house.is_integrated && !house.last_system_sync) return 'warning';
    if (house.is_integrated) return 'primary';
    return 'default';
  };

  return (
    <Box>
      {/* Farm Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box>
              <Typography variant="h4" gutterBottom>
                {farm.name}
              </Typography>
              <Typography color="textSecondary" variant="h6" gutterBottom>
                {farm.location}
              </Typography>
              {farm.description && (
                <Typography color="textSecondary" sx={{ mt: 1 }}>
                  {farm.description}
                </Typography>
              )}
            </Box>
            <Box display="flex" gap={1}>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={onRefresh}
                size="small"
              >
                Refresh
              </Button>
              {farm.has_system_integration && (
                <Button
                  variant="outlined"
                  startIcon={<Sync />}
                  onClick={() => setSyncDialogOpen(true)}
                  size="small"
                >
                  Sync Data
                </Button>
              )}
              <Button
                variant="outlined"
                startIcon={<Settings />}
                onClick={() => onConfigureIntegration?.(farm.id)}
                size="small"
              >
                Configure
              </Button>
            </Box>
          </Box>

          {/* Integration Status */}
          <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
            <Chip
              label={farm.integration_type === 'none' ? 'Manual Management' : 'System Integrated'}
              color={farm.integration_type === 'none' ? 'default' : 'primary'}
              icon={farm.integration_type === 'none' ? <Settings /> : <IntegrationInstructions />}
            />
            {farm.has_system_integration && (
              <Chip
                label={`Status: ${farm.integration_status}`}
                color={getIntegrationStatusColor(farm.integration_status)}
                icon={getIntegrationStatusIcon(farm.integration_status)}
              />
            )}
            {farm.last_sync && (
              <Chip
                label={`Last Sync: ${formatLastSync(farm.last_sync)}`}
                color="info"
                variant="outlined"
              />
            )}
          </Box>

          {/* Integration Health (for integrated farms) */}
          {farm.has_system_integration && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Integration Health
              </Typography>
              {loadingHealth ? (
                <CircularProgress size={20} />
              ) : integrationHealth ? (
                <Box display="flex" gap={2} flexWrap="wrap">
                  <Chip
                    label={`Success Rate: ${integrationHealth.success_rate_24h.toFixed(1)}%`}
                    color={integrationHealth.success_rate_24h > 90 ? 'success' : 'warning'}
                    size="small"
                  />
                  <Chip
                    label={`Failures: ${integrationHealth.consecutive_failures}`}
                    color={integrationHealth.consecutive_failures > 3 ? 'error' : 'default'}
                    size="small"
                  />
                  {integrationHealth.average_response_time && (
                    <Chip
                      label={`Avg Response: ${integrationHealth.average_response_time.toFixed(2)}s`}
                      color="info"
                      size="small"
                    />
                  )}
                </Box>
              ) : (
                <Alert severity="warning" sx={{ mt: 1 }}>
                  Unable to load integration health data
                </Alert>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Houses Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Houses ({farm.houses.length})
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Home />}
              onClick={() => navigate(`/farms/${farm.id}/houses`)}
              size="small"
            >
              Manage Houses
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            {farm.houses.map((house) => (
              <Grid item xs={12} sm={6} md={4} key={house.id}>
                <Card 
                  variant="outlined" 
                  sx={{ 
                    height: '100%',
                    cursor: 'pointer',
                    '&:hover': { boxShadow: 2 }
                  }}
                  onClick={() => navigate(`/farms/${farm.id}/houses/${house.id}`)}
                >
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="h6">
                        House {house.house_number}
                      </Typography>
                      <Chip
                        label={house.is_integrated ? 'Integrated' : 'Manual'}
                        color={getHouseStatusColor(house)}
                        size="small"
                      />
                    </Box>
                    
                    <Typography color="textSecondary" variant="body2" gutterBottom>
                      Capacity: {house.capacity.toLocaleString()}
                    </Typography>
                    
                    <Typography color="textSecondary" variant="body2" gutterBottom>
                      Age: {house.current_age_days} days
                    </Typography>
                    
                    {house.batch_start_date && (
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Started: {new Date(house.batch_start_date).toLocaleDateString()}
                      </Typography>
                    )}
                    
                    {house.expected_harvest_date && (
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Harvest: {new Date(house.expected_harvest_date).toLocaleDateString()}
                      </Typography>
                    )}
                    
                    {house.is_integrated && house.last_system_sync && (
                      <Typography color="textSecondary" variant="body2">
                        Last Sync: {formatLastSync(house.last_system_sync)}
                      </Typography>
                    )}
                    
                    {!house.is_active && (
                      <Chip
                        label="Inactive"
                        color="default"
                        size="small"
                        sx={{ mt: 1 }}
                      />
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Workers Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Workers ({farm.workers.length})
            </Typography>
            <Button
              variant="outlined"
              onClick={() => navigate(`/farms/${farm.id}/workers`)}
              size="small"
            >
              Manage Workers
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            {farm.workers.map((worker) => (
              <Grid item xs={12} sm={6} md={4} key={worker.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      {worker.name}
                    </Typography>
                    <Typography color="textSecondary" variant="body2" gutterBottom>
                      {worker.role}
                    </Typography>
                    <Typography color="textSecondary" variant="body2" gutterBottom>
                      {worker.email}
                    </Typography>
                    {worker.phone && (
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        {worker.phone}
                      </Typography>
                    )}
                    <Chip
                      label={worker.is_active ? 'Active' : 'Inactive'}
                      color={worker.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Integration-specific content */}
      {farm.integration_type === 'rotem' && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Rotem Integration
            </Typography>
            <Typography color="textSecondary" gutterBottom>
              This farm is connected to the Rotem monitoring system for automated data collection.
            </Typography>
            <Box display="flex" gap={1} mt={2}>
              <Button
                variant="contained"
                startIcon={<TrendingUp />}
                onClick={() => navigate(`/rotem/farms/farm_${farm.contact_email}`)}
                size="small"
              >
                View Rotem Dashboard
              </Button>
              <Button
                variant="outlined"
                startIcon={<Water />}
                onClick={() => navigate(`/rotem/farms/farm_${farm.contact_email}/sensors`)}
                size="small"
              >
                Sensor Data
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Sync Dialog */}
      <Dialog open={syncDialogOpen} onClose={() => setSyncDialogOpen(false)}>
        <DialogTitle>Sync Data</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            This will sync the latest data from the integrated system. This may take a few moments.
          </Typography>
          {syncing && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Syncing data...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSyncDialogOpen(false)} disabled={syncing}>
            Cancel
          </Button>
          <Button onClick={handleSyncData} variant="contained" disabled={syncing}>
            {syncing ? 'Syncing...' : 'Sync Now'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UnifiedFarmDashboard;
