import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams } from 'react-router-dom';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
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
  Visibility,
  Assessment,
  Timeline,
  Restaurant,
  WaterDrop,
  Air,
  ExpandMore as ExpandMoreIcon,
  Schedule as ScheduleIcon,
  Today as TodayIcon,
  TouchApp as ClickIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import EmailManager from '../EmailManager';
import WorkerList from '../WorkerList';
import FarmHousesMonitoring from '../houses/FarmHousesMonitoring';
import monitoringApi from '../../services/monitoringApi';
import logger from '../../utils/logger';

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

interface HouseSensorData {
  status: string;
  sensors: {
    temperature?: {
      current: number;
      unit: string;
    };
    humidity?: {
      current: number;
      unit: string;
    };
    water?: {
      current: number;
      unit: string;
    };
    feed_consumption?: {
      current: number;
      unit: string;
    };
    avg_weight?: {
      current: number;
      unit: string;
    };
    static_pressure?: {
      current: number;
      unit: string;
    };
    individual_temperatures?: Record<string, { value: number; unit: string }>;
    system_components?: Record<string, { status: string }>;
    control_settings?: Record<string, { current: number; unit: string }>;
  };
  last_updated: string;
}

interface MLPrediction {
  id: number;
  farm_name: string;
  prediction_date: string;
  prediction_type: string;
  value: number;
  confidence: number;
}

interface MonitoringHouse {
  id: number;
  house_number: number;
  status: string;
  alerts_count: number;
  last_update: string;
}

interface MonitoringDashboard {
  total_houses: number;
  alerts_summary: {
    total_active: number;
    critical: number;
    warning: number;
    info: number;
  };
  connection_summary: {
    connected: number;
    disconnected: number;
  };
  houses: MonitoringHouse[];
}

interface UnifiedFarmDashboardProps {
  farm?: Farm;
  onRefresh?: () => void;
  onConfigureIntegration?: (farmId: number) => void;
  onSyncData?: (farmId: number) => void;
}

const UnifiedFarmDashboard: React.FC<UnifiedFarmDashboardProps> = ({
  farm: propFarm,
  onRefresh,
  onConfigureIntegration,
  onSyncData,
}) => {
  const { farmId } = useParams<{ farmId: string }>();
  const navigate = useNavigate();
  const [farm, setFarm] = useState<Farm | null>(propFarm || null);
  const [loading, setLoading] = useState(!propFarm);
  const [error, setError] = useState<string | null>(null);
  const [integrationHealth, setIntegrationHealth] = useState<IntegrationHealth | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncDialogOpen, setSyncDialogOpen] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generateMessage, setGenerateMessage] = useState<string | null>(null);
  const [houseSensorData, setHouseSensorData] = useState<{[key: string]: HouseSensorData}>({});
  const [mlPredictions, setMlPredictions] = useState<MLPrediction[]>([]);
  const [loadingData, setLoadingData] = useState(false);
  const [monitoringDashboard, setMonitoringDashboard] = useState<MonitoringDashboard | null>(null);
  const [loadingMonitoring, setLoadingMonitoring] = useState(false);

  useEffect(() => {
    if (farmId && !propFarm) {
      fetchFarmData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [farmId, propFarm]);

  useEffect(() => {
    if (farm?.has_system_integration) {
      fetchIntegrationHealth();
    }
  }, [farm?.id, farm?.has_system_integration]);

  useEffect(() => {
    if (farm?.integration_type === 'rotem') {
      fetchHouseSensorData();
      fetchMlPredictions();
      fetchMonitoringDashboard();
    }
  }, [farm?.id, farm?.integration_type]);

  const fetchMonitoringDashboard = async () => {
    if (!farm) return;
    
    setLoadingMonitoring(true);
    try {
      const data = await monitoringApi.getFarmMonitoringDashboard(farm.id);
      setMonitoringDashboard(data);
    } catch (error) {
      logger.error('Error fetching monitoring dashboard:', error);
    } finally {
      setLoadingMonitoring(false);
    }
  };

  const fetchFarmData = async () => {
    if (!farmId) return;
    
    setLoading(true);
    setError(null);
    try {
      logger.debug('Fetching farm data for ID:', farmId);
      const response = await api.get(`/farms/${farmId}/`);
      logger.debug('Farm data received:', response.data);
      setFarm(response.data);
    } catch (error: unknown) {
      logger.error('Error fetching farm data:', error);
      const errorMessage = (error as { response?: { data?: { detail?: string; error?: string } }; message?: string })?.response?.data?.detail || 
                          (error as { response?: { data?: { detail?: string; error?: string } }; message?: string })?.response?.data?.error || 
                          (error as { message?: string })?.message || 
                          'Failed to load farm data';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchIntegrationHealth = async () => {
    if (!farm) return;
    
    setLoadingHealth(true);
    try {
      const response = await api.get(`/farms/${farm.id}/integration_status/`);
      setIntegrationHealth(response.data.health_details);
    } catch (error) {
      logger.error('Failed to fetch integration health:', error);
    } finally {
      setLoadingHealth(false);
    }
  };

  const fetchHouseSensorData = async () => {
    if (!farm) return;
    
    setLoadingData(true);
    try {
      const response = await api.get(`/farms/${farm.id}/house-sensor-data/`);
      setHouseSensorData(response.data.houses || {});
    } catch (error) {
      logger.error('Error fetching house sensor data:', error);
    } finally {
      setLoadingData(false);
    }
  };

  const fetchMlPredictions = async () => {
    if (!farm) return;
    
    try {
      const response = await api.get(`/rotem/predictions/?farm_name=${encodeURIComponent(farm.name)}&limit=10`);
      setMlPredictions(response.data.results || []);
    } catch (error) {
      logger.error('Error fetching ML predictions:', error);
    }
  };

  const handleSyncData = async () => {
    if (!farm) return;
    
    setSyncing(true);
    try {
      // If onSyncData prop is provided, use it (for embedded usage)
      if (onSyncData) {
        await onSyncData(farm.id);
      } else {
        // Otherwise, call the backend API directly (for standalone usage)
        const token = localStorage.getItem('authToken');
        if (!token) {
          throw new Error('No authentication token found');
        }
        
        const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8002/api'}/farms/${farm.id}/sync_data/`, {
          method: 'POST',
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Sync failed');
        }
        
        const result = await response.json();
        setSyncMessage(result.message || 'Data synced successfully');
      }
      
      setSyncDialogOpen(false);
      if (onRefresh) onRefresh();
      
      // Refresh house sensor data after sync
      if (farm.integration_type === 'rotem') {
        await fetchHouseSensorData();
        await fetchMlPredictions();
      }
    } catch (error) {
      logger.error('Sync failed:', error);
      const errorMessage = (error as Error)?.message || 'Unknown error';
      setSyncMessage(`Sync failed: ${errorMessage}`);
    } finally {
      setSyncing(false);
    }
  };

  const handleGenerateHousesAndTasks = async () => {
    if (!farm) return;
    
    setGenerating(true);
    try {
      const token = localStorage.getItem('authToken');
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8002/api'}/farms/${farm.id}/sync_data/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'House generation failed');
      }
      
      const result = await response.json();
      setGenerateMessage(result.message || 'Houses and tasks generated successfully');
      
      setGenerateDialogOpen(false);
      if (onRefresh) onRefresh();
      
      // Refresh farm data to show the new houses
      await fetchFarmData();
      
    } catch (error) {
      logger.error('House generation failed:', error);
      const errorMessage = (error as Error)?.message || 'Unknown error';
      setGenerateMessage(`House generation failed: ${errorMessage}`);
    } finally {
      setGenerating(false);
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

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !farm) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || 'Farm not found'}
        </Alert>
        <Button
          variant="contained"
          onClick={() => navigate('/farms')}
        >
          Back to Farms
        </Button>
      </Box>
    );
  }

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
                onClick={() => {
                  if (onRefresh) {
                    onRefresh();
                  } else {
                    // Refresh farm data directly when used standalone
                    fetchFarmData();
                    fetchIntegrationHealth();
                    if (farm?.integration_type === 'rotem') {
                      fetchHouseSensorData();
                      fetchMlPredictions();
                    }
                  }
                }}
                size="small"
              >
                Refresh
              </Button>
              {farm.has_system_integration && (
                <>
                  <Button
                    variant="outlined"
                    startIcon={<Sync />}
                    onClick={() => setSyncDialogOpen(true)}
                    size="small"
                  >
                    Sync Data
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<Home />}
                    onClick={() => setGenerateDialogOpen(true)}
                    size="small"
                    color="primary"
                  >
                    Generate Houses & Tasks
                  </Button>
                </>
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
              Houses ({farm.houses?.length || 0})
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Home />}
              onClick={() => {
                if (farm.houses && farm.houses.length > 0) {
                  navigate(`/farms/${farm.id}/houses/${farm.houses[0].id}`);
                }
              }}
              size="small"
              disabled={!farm.houses || farm.houses.length === 0}
            >
              View Houses
            </Button>
          </Box>
          
          <Grid container spacing={2}>
            {(farm.houses || []).map((house) => (
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
                    
                    {/* Show real-time sensor data if available */}
                    {houseSensorData[house.house_number.toString()]?.sensors ? (
                      <>
                        <Typography color="textSecondary" variant="body2" gutterBottom>
                          Age: {houseSensorData[house.house_number.toString()].sensors.growth_day?.current || house.current_age_days} days
                        </Typography>
                        <Typography color="textSecondary" variant="body2" gutterBottom>
                          Temperature: {houseSensorData[house.house_number.toString()].sensors.temperature?.current || 'N/A'}°C
                        </Typography>
                        <Typography color="textSecondary" variant="body2" gutterBottom>
                          Water: {houseSensorData[house.house_number.toString()].sensors.water?.current || 'N/A'}L
                        </Typography>
                        <Typography color="textSecondary" variant="body2" gutterBottom>
                          Feed: {houseSensorData[house.house_number.toString()].sensors.feed_consumption?.current || 'N/A'}LB
                        </Typography>
                      </>
                    ) : (
                      <>
                        <Typography color="textSecondary" variant="body2" gutterBottom>
                          Age: {house.current_age_days} days
                        </Typography>
                        <Typography color="textSecondary" variant="body2" gutterBottom>
                          Temperature: Loading...
                        </Typography>
                        <Typography color="textSecondary" variant="body2" gutterBottom>
                          Water: Loading...
                        </Typography>
                        <Typography color="textSecondary" variant="body2" gutterBottom>
                          Feed: Loading...
                        </Typography>
                      </>
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
              Workers ({farm.workers?.length || 0})
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
            {(farm.workers || []).map((worker) => (
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

      {/* Rotem Integration Data */}
      {farm.integration_type === 'rotem' && (
        <>
          {/* Real-time Sensor Data */}
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Real-time Sensor Data
                </Typography>
                <Box display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Refresh />}
                    onClick={() => {
                      fetchHouseSensorData();
                      fetchMlPredictions();
                    }}
                    disabled={loadingData}
                  >
                    Refresh
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={<Sync />}
                    onClick={() => setSyncDialogOpen(true)}
                  >
                    Sync Data
                  </Button>
                </Box>
              </Box>
              
              {loadingData ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : Object.keys(houseSensorData).length > 0 ? (
                <Grid container spacing={2}>
                  {Object.entries(houseSensorData).map(([houseNumber, houseData]) => (
                    <Grid item xs={12} sm={6} md={4} key={houseNumber}>
                      <Card variant="outlined" sx={{ height: '100%' }}>
                        <CardContent>
                          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                            <Typography variant="h6">House {houseNumber}</Typography>
                            <Chip 
                              label={houseData.status} 
                              color={houseData.status === 'active' ? 'success' : 'default'}
                              size="small"
                            />
                          </Box>
                          
                          {/* Environmental Data */}
                          <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                            Environmental
                          </Typography>
                          <Grid container spacing={1} sx={{ mb: 2 }}>
                            {/* Main Temperature */}
                            {houseData.sensors?.temperature && (
                              <Grid item xs={6}>
                                <Box display="flex" alignItems="center" mb={1}>
                                  <Thermostat color="primary" sx={{ mr: 0.5, fontSize: 16 }} />
                                  <Typography variant="caption">Tunnel</Typography>
                                </Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {houseData.sensors.temperature.current?.toFixed(1) || 'N/A'}{houseData.sensors.temperature.unit}
                                </Typography>
                              </Grid>
                            )}
                            
                            {/* Wind Chill */}
                            {houseData.sensors?.individual_temperatures?.['Wind_Chill_Temperature'] && (
                              <Grid item xs={6}>
                                <Box display="flex" alignItems="center" mb={1}>
                                  <Air color="primary" sx={{ mr: 0.5, fontSize: 16 }} />
                                  <Typography variant="caption">Wind Chill</Typography>
                                </Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {houseData.sensors.individual_temperatures['Wind_Chill_Temperature'].value?.toFixed(1) || 'N/A'}°C
                                </Typography>
                              </Grid>
                            )}
                            
                            {/* Humidity */}
                            {houseData.sensors?.humidity && houseData.sensors.humidity.current > 0 && (
                              <Grid item xs={6}>
                                <Box display="flex" alignItems="center" mb={1}>
                                  <Water color="primary" sx={{ mr: 0.5, fontSize: 16 }} />
                                  <Typography variant="caption">Humidity</Typography>
                                </Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {houseData.sensors.humidity.current?.toFixed(1) || 'N/A'}{houseData.sensors.humidity.unit}
                                </Typography>
                              </Grid>
                            )}
                            
                            {/* Static Pressure */}
                            {houseData.sensors?.static_pressure && houseData.sensors.static_pressure.current > 0 && (
                              <Grid item xs={6}>
                                <Box display="flex" alignItems="center" mb={1}>
                                  <Air color="primary" sx={{ mr: 0.5, fontSize: 16 }} />
                                  <Typography variant="caption">Pressure</Typography>
                                </Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {houseData.sensors.static_pressure.current?.toFixed(3) || 'N/A'}{houseData.sensors.static_pressure.unit}
                                </Typography>
                              </Grid>
                            )}
                          </Grid>

                          {/* Consumption Data */}
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            Consumption
                          </Typography>
                          <Grid container spacing={1} sx={{ mb: 2 }}>
                            {/* Feed Consumption */}
                            {houseData.sensors?.feed_consumption && houseData.sensors.feed_consumption.current > 0 && (
                              <Grid item xs={6}>
                                <Box display="flex" alignItems="center" mb={1}>
                                  <Restaurant color="primary" sx={{ mr: 0.5, fontSize: 16 }} />
                                  <Typography variant="caption">Feed</Typography>
                                </Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {houseData.sensors.feed_consumption.current?.toFixed(0) || 'N/A'}{houseData.sensors.feed_consumption.unit}
                                </Typography>
                              </Grid>
                            )}
                            
                            {/* Water Consumption */}
                            {houseData.sensors?.water && houseData.sensors.water.current > 0 && (
                              <Grid item xs={6}>
                                <Box display="flex" alignItems="center" mb={1}>
                                  <WaterDrop color="primary" sx={{ mr: 0.5, fontSize: 16 }} />
                                  <Typography variant="caption">Water</Typography>
                                </Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {houseData.sensors.water.current?.toFixed(0) || 'N/A'}{houseData.sensors.water.unit}
                                </Typography>
                              </Grid>
                            )}
                            
                            {/* Average Weight */}
                            {houseData.sensors?.avg_weight && houseData.sensors.avg_weight.current > 0 && (
                              <Grid item xs={6}>
                                <Box display="flex" alignItems="center" mb={1}>
                                  <Restaurant color="primary" sx={{ mr: 0.5, fontSize: 16 }} />
                                  <Typography variant="caption">Avg Weight</Typography>
                                </Box>
                                <Typography variant="body2" fontWeight="bold">
                                  {houseData.sensors.avg_weight.current?.toFixed(1) || 'N/A'}{houseData.sensors.avg_weight.unit}
                                </Typography>
                              </Grid>
                            )}
                          </Grid>

                          {/* System Components */}
                          {houseData.sensors?.system_components && Object.keys(houseData.sensors.system_components).length > 0 && (
                            <>
                              <Typography variant="subtitle2" color="primary" gutterBottom>
                                Equipment Status
                              </Typography>
                              <Grid container spacing={1} sx={{ mb: 2 }}>
                                {Object.entries(houseData.sensors.system_components).slice(0, 4).map(([component, data]) => (
                                  <Grid item xs={6} key={component}>
                                    <Box display="flex" alignItems="center" mb={1}>
                                      <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                        {component.replace(/_/g, ' ')}
                                      </Typography>
                                    </Box>
                                    <Chip
                                      label={(data as { status: string }).status}
                                      color={(data as { status: string }).status === 'On' ? 'success' : 'default'}
                                      size="small"
                                      sx={{ fontSize: '0.7rem', height: 20 }}
                                    />
                                  </Grid>
                                ))}
                              </Grid>
                            </>
                          )}

                          {/* Control Settings */}
                          {houseData.sensors?.control_settings && Object.keys(houseData.sensors.control_settings).length > 0 && (
                            <>
                              <Typography variant="subtitle2" color="primary" gutterBottom>
                                Controls
                              </Typography>
                              <Grid container spacing={1}>
                                {Object.entries(houseData.sensors.control_settings).slice(0, 3).map(([control, data]) => (
                                  <Grid item xs={4} key={control}>
                                    <Box display="flex" alignItems="center" mb={1}>
                                      <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                        {control.replace(/_/g, ' ').replace(/Position/g, '').trim()}
                                      </Typography>
                                    </Box>
                                    <Typography variant="body2" fontWeight="bold" sx={{ fontSize: '0.8rem' }}>
                                      {(data as { current?: number; unit?: string }).current?.toFixed(0) || '0'}{(data as { current?: number; unit?: string }).unit}
                                    </Typography>
                                  </Grid>
                                ))}
                              </Grid>
                            </>
                          )}
                          
                          <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
                            Last updated: {new Date(houseData.last_updated).toLocaleTimeString()}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Alert severity="warning">
                  <Typography variant="body2">
                    <strong>Sensor data not available</strong>
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    The Rotem system may not be properly authenticated or the houses may not have active sensor data.
                    Click &quot;Sync Data&quot; to attempt to refresh the connection and collect the latest information.
                  </Typography>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Monitoring Dashboard */}
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Monitoring Dashboard
                </Typography>
                <Box display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Refresh />}
                    onClick={fetchMonitoringDashboard}
                    disabled={loadingMonitoring}
                  >
                    Refresh
                  </Button>
                  <Button
                    variant="contained"
                    size="small"
                    startIcon={<Visibility />}
                    onClick={() => navigate(`/farms/${farm.id}/monitoring`)}
                  >
                    View All Houses
                  </Button>
                </Box>
              </Box>

              {loadingMonitoring ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : monitoringDashboard ? (
                <>
                  {/* Summary Cards */}
                  <Grid container spacing={2} mb={3}>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="text.secondary">
                            Total Houses
                          </Typography>
                          <Typography variant="h5">
                            {monitoringDashboard.total_houses}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="text.secondary">
                            Active Alarms
                          </Typography>
                          <Typography variant="h5" color={monitoringDashboard.alerts_summary.critical > 0 ? 'error' : 'text.primary'}>
                            {monitoringDashboard.alerts_summary.total_active}
                          </Typography>
                          {monitoringDashboard.alerts_summary.critical > 0 && (
                            <Typography variant="caption" color="error">
                              {monitoringDashboard.alerts_summary.critical} critical
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="text.secondary">
                            Connected
                          </Typography>
                          <Typography variant="h5" color="success.main">
                            {monitoringDashboard.connection_summary.connected}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="caption" color="text.secondary">
                            Disconnected
                          </Typography>
                          <Typography variant="h5" color="error.main">
                            {monitoringDashboard.connection_summary.disconnected}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>

                  {/* Houses Grid (limited to first 4) */}
                  <Grid container spacing={2}>
                    {monitoringDashboard.houses.slice(0, 4).map((house: MonitoringHouse) => (
                      <Grid item xs={12} sm={6} md={3} key={house.house_id}>
                        <Card
                          variant="outlined"
                          sx={{
                            cursor: 'pointer',
                            border: house.alarm_status === 'critical' ? '2px solid' : 'none',
                            borderColor: house.alarm_status === 'critical' ? 'error.main' : 'transparent',
                            '&:hover': { boxShadow: 2 },
                          }}
                          onClick={() => navigate(`/houses/${house.house_id}/monitoring`)}
                        >
                          <CardContent>
                            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                              <Typography variant="h6">House {house.house_number}</Typography>
                              <Chip
                                label={house.alarm_status}
                                size="small"
                                color={house.alarm_status === 'critical' ? 'error' : house.alarm_status === 'warning' ? 'warning' : 'success'}
                              />
                            </Box>
                            {house.average_temperature !== null && (
                              <Typography variant="body2">
                                Temp: {house.average_temperature?.toFixed(1)}°C
                              </Typography>
                            )}
                            {house.humidity !== null && (
                              <Typography variant="body2">
                                Humidity: {house.humidity?.toFixed(1)}%
                              </Typography>
                            )}
                            {house.active_alarms_count > 0 && (
                              <Chip
                                label={`${house.active_alarms_count} alarm${house.active_alarms_count > 1 ? 's' : ''}`}
                                size="small"
                                color="error"
                                sx={{ mt: 1 }}
                              />
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                  
                  {monitoringDashboard.houses.length > 4 && (
                    <Box mt={2} textAlign="center">
                      <Button
                        variant="outlined"
                        onClick={() => navigate(`/farms/${farm.id}/monitoring`)}
                      >
                        View All {monitoringDashboard.total_houses} Houses
                      </Button>
                    </Box>
                  )}
                </>
              ) : (
                <Alert severity="info">
                  No monitoring data available. Click &quot;Sync Data&quot; to collect monitoring snapshots.
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* ML Predictions */}
          {(mlPredictions || []).length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AI Insights & Predictions
                </Typography>
                <Grid container spacing={2}>
                  {mlPredictions.slice(0, 6).map((prediction, index) => (
                    <Grid item xs={12} sm={6} md={4} key={prediction.id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box display="flex" alignItems="center" mb={1}>
                            {prediction.prediction_type === 'anomaly' && <Warning color="error" sx={{ mr: 1 }} />}
                            {prediction.prediction_type === 'optimization' && <TrendingUp color="warning" sx={{ mr: 1 }} />}
                            {prediction.prediction_type === 'performance' && <Assessment color="success" sx={{ mr: 1 }} />}
                            <Typography variant="subtitle2" sx={{ textTransform: 'capitalize' }}>
                              {prediction.prediction_type}
                            </Typography>
                          </Box>
                          <Typography variant="body2" gutterBottom>
                            {prediction.prediction_data?.action || prediction.prediction_data?.recommendations?.[0] || 'Analysis available'}
                          </Typography>
                          <Chip
                            label={`${(prediction.confidence_score * 100).toFixed(0)}% confidence`}
                            size="small"
                            color={prediction.confidence_score > 0.8 ? 'success' : prediction.confidence_score > 0.6 ? 'warning' : 'default'}
                          />
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Sync Message */}
      {syncMessage && (
        <Alert 
          severity={syncMessage.includes('failed') ? 'error' : 'success'} 
          onClose={() => setSyncMessage(null)}
          sx={{ mb: 2 }}
        >
          {syncMessage}
        </Alert>
      )}

      {/* Email Management for this farm */}
      <Box mb={4}>
        <EmailManager farmId={farm?.id} farmName={farm?.name} />
      </Box>

      {/* Worker Management for this farm */}
      <Box mb={4}>
        <WorkerList farmId={farm?.id} farmName={farm?.name} />
      </Box>

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

      {/* Generate Houses & Tasks Dialog */}
      <Dialog open={generateDialogOpen} onClose={() => setGenerateDialogOpen(false)}>
        <DialogTitle>Generate Houses & Tasks</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            This will generate houses and tasks based on the current Rotem system data:
          </Typography>
          <Box sx={{ mt: 2, mb: 2 }}>
            <Typography variant="body2" color="textSecondary">
              • Get house count from Rotem API (typically 8 houses)
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Extract house ages from Growth_Day field
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Create/update House objects with correct data
            </Typography>
            <Typography variant="body2" color="textSecondary">
              • Generate tasks based on house age and assigned programs
            </Typography>
          </Box>
          {generating && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Generating houses and tasks...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateDialogOpen(false)} disabled={generating}>
            Cancel
          </Button>
          <Button onClick={handleGenerateHousesAndTasks} variant="contained" disabled={generating}>
            {generating ? 'Generating...' : 'Generate Now'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Generate Message */}
      {generateMessage && (
        <Alert 
          severity={generateMessage.includes('failed') ? 'error' : 'success'} 
          onClose={() => setGenerateMessage(null)}
          sx={{ mb: 2 }}
        >
          {generateMessage}
        </Alert>
      )}
    </Box>
  );
};

export default UnifiedFarmDashboard;
