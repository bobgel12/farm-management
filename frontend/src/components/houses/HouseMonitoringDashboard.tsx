import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Button,
  Paper,
  Divider,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  ArrowBack,
  Refresh,
  Thermostat,
  WaterDrop,
  Air,
  Restaurant,
  CheckCircle,
  Error,
  Warning,
  Timeline,
  Visibility,
} from '@mui/icons-material';
import monitoringApi from '../../services/monitoringApi';
import { HouseMonitoringSnapshot } from '../../types/monitoring';
import HouseMonitoringCharts from './HouseMonitoringCharts';
import HouseAlertsPanel from './HouseAlertsPanel';

const HouseMonitoringDashboard: React.FC = () => {
  const { houseId } = useParams<{ houseId: string }>();
  const navigate = useNavigate();
  const [snapshot, setSnapshot] = useState<HouseMonitoringSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchLatestMonitoring = async () => {
    if (!houseId) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await monitoringApi.getHouseLatestMonitoring(parseInt(houseId));
      setSnapshot(data);
      setLastUpdate(new Date());
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatestMonitoring();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchLatestMonitoring, 30000);
    return () => clearInterval(interval);
  }, [houseId]);

  if (loading && !snapshot) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error && !snapshot) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!snapshot) {
    return (
      <Box p={3}>
        <Alert severity="info">No monitoring data available for this house</Alert>
      </Box>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'success';
    }
  };

  const formatValue = (value: number | null, unit: string = '', decimals: number = 1) => {
    if (value === null || value === undefined) return 'N/A';
    return `${value.toFixed(decimals)} ${unit}`;
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate(-1)}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h4">
            House {snapshot.house_number} Monitoring
          </Typography>
          <Chip
            label={snapshot.farm_name}
            size="small"
            variant="outlined"
          />
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <Typography variant="caption" color="text.secondary">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </Typography>
          <Tooltip title="Refresh">
            <IconButton onClick={fetchLatestMonitoring}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Status Overview */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Connection Status
                  </Typography>
                  <Typography variant="h6">
                    {snapshot.is_connected ? 'Connected' : 'Disconnected'}
                  </Typography>
                </Box>
                {snapshot.is_connected ? (
                  <CheckCircle color="success" />
                ) : (
                  <Error color="error" />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Alarm Status
                  </Typography>
                  <Typography variant="h6">
                    {snapshot.alarm_status.charAt(0).toUpperCase() + snapshot.alarm_status.slice(1)}
                  </Typography>
                </Box>
                <Chip
                  label={snapshot.alarm_status}
                  color={getStatusColor(snapshot.alarm_status) as any}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Growth Day
                </Typography>
                <Typography variant="h6">
                  {snapshot.growth_day ?? 'N/A'} days
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  Bird Count
                </Typography>
                <Typography variant="h6">
                  {snapshot.bird_count?.toLocaleString() ?? 'N/A'}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Key Metrics */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={1}>
                <Thermostat color="primary" />
                <Typography variant="subtitle2">Temperature</Typography>
              </Box>
              <Typography variant="h5">
                {formatValue(snapshot.average_temperature, '°C')}
              </Typography>
              {snapshot.target_temperature && (
                <Typography variant="caption" color="text.secondary">
                  Target: {formatValue(snapshot.target_temperature, '°C')}
                </Typography>
              )}
              {snapshot.outside_temperature !== null && (
                <Typography variant="caption" color="text.secondary" display="block">
                  Outside: {formatValue(snapshot.outside_temperature, '°C')}
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={1}>
                <WaterDrop color="primary" />
                <Typography variant="subtitle2">Humidity</Typography>
              </Box>
              <Typography variant="h5">
                {formatValue(snapshot.humidity, '%')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={1}>
                <Air color="primary" />
                <Typography variant="subtitle2">Pressure</Typography>
              </Box>
              <Typography variant="h5">
                {formatValue(snapshot.static_pressure, 'hPa')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={1}>
                <Visibility color="primary" />
                <Typography variant="subtitle2">Ventilation</Typography>
              </Box>
              <Typography variant="h5">
                {formatValue(snapshot.ventilation_level, '%')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Consumption Metrics */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={1}>
                <WaterDrop color="primary" />
                <Typography variant="subtitle2">Water Consumption</Typography>
              </Box>
              <Typography variant="h5">
                {formatValue(snapshot.water_consumption, 'L/day')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={1}>
                <Restaurant color="primary" />
                <Typography variant="subtitle2">Feed Consumption</Typography>
              </Box>
              <Typography variant="h5">
                {formatValue(snapshot.feed_consumption, 'kg/day')}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Temperature Sensors Grid */}
      {snapshot.sensor_data?.temperature_sensors && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Temperature Sensors
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(snapshot.sensor_data.temperature_sensors).map(([key, sensor]) => (
                <Grid item xs={6} sm={4} md={3} key={key}>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      {sensor.display_name || sensor.name}
                    </Typography>
                    <Typography variant="h6">
                      {formatValue(sensor.value, '°C')}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Alarms Panel */}
      {snapshot.has_alarms && snapshot.alarms && snapshot.alarms.length > 0 && houseId && (
        <Box mb={3}>
          <HouseAlertsPanel houseId={parseInt(houseId)} alarms={snapshot.alarms} />
        </Box>
      )}

      {/* Historical Charts */}
      {houseId && <HouseMonitoringCharts houseId={parseInt(houseId)} />}
    </Box>
  );
};

export default HouseMonitoringDashboard;

