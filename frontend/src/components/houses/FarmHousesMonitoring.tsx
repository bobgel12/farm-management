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
  IconButton,
  Tooltip,
  Button,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import {
  Refresh,
  Visibility,
  CheckCircle,
  Error,
  Warning,
  Thermostat,
  WaterDrop,
  Air,
} from '@mui/icons-material';
import monitoringApi from '../../services/monitoringApi';
import {
  FarmHousesMonitoringResponse,
  FarmMonitoringCacheStatus,
  HouseMonitoringSummary,
  MonitoringCacheRefreshRun,
  MonitoringDataMode,
} from '../../types/monitoring';

const FarmHousesMonitoring: React.FC = () => {
  const { farmId } = useParams<{ farmId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<FarmHousesMonitoringResponse | null>(null);
  const [cacheStatus, setCacheStatus] = useState<FarmMonitoringCacheStatus | null>(null);
  const [dataMode, setDataMode] = useState<MonitoringDataMode>(() => monitoringApi.getMonitoringDataMode());
  const [activeRun, setActiveRun] = useState<MonitoringCacheRefreshRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningNow, setRunningNow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const fetchMonitoringData = async () => {
    if (!farmId) return;
    
    setLoading(true);
    setError(null);
    try {
      const farmIdNumber = parseInt(farmId);
      const [response, statusResponse] = await Promise.all([
        monitoringApi.getFarmHousesMonitoring(farmIdNumber, dataMode),
        monitoringApi.getFarmMonitoringCacheStatus(farmIdNumber),
      ]);
      setData(response);
      setCacheStatus(statusResponse);
      setActiveRun(statusResponse.latest_runs.manual?.status === 'queued' || statusResponse.latest_runs.manual?.status === 'running'
        ? statusResponse.latest_runs.manual
        : null);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchMonitoringData, 30000);
    return () => clearInterval(interval);
  }, [farmId, dataMode]);

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!activeRun || !['queued', 'running'].includes(activeRun.status)) return undefined;
    const interval = setInterval(async () => {
      try {
        const run = await monitoringApi.getMonitoringCacheRefreshRun(activeRun.run_id);
        setActiveRun(run);
        if (!['queued', 'running'].includes(run.status)) {
          fetchMonitoringData();
        }
      } catch (err) {
        console.error('Failed to poll monitoring cache refresh run:', err);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [activeRun?.run_id, activeRun?.status]);

  const handleDataModeChange = (_event: React.MouseEvent<HTMLElement>, value: MonitoringDataMode | null) => {
    if (!value) return;
    monitoringApi.setMonitoringDataMode(value);
    setDataMode(value);
  };

  const handleRunNow = async () => {
    setRunningNow(true);
    setError(null);
    try {
      const run = await monitoringApi.queueMonitoringCacheRefresh();
      setActiveRun(run);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to queue monitoring cache refresh');
    } finally {
      setRunningNow(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!data) {
    return (
      <Box p={3}>
        <Alert severity="info">No monitoring data available for houses in this farm</Alert>
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

  const formatValue = (value: number | null, unit: string = '') => {
    if (value === null || value === undefined) return 'N/A';
    return `${value.toFixed(1)} ${unit}`;
  };

  const formatDateTime = (value?: string | null) => {
    if (!value) return 'Never';
    return new Date(value).toLocaleString();
  };

  const formatAge = (value?: string | null) => {
    if (!value) return 'Unknown';
    const seconds = Math.max(0, Math.floor((now - new Date(value).getTime()) / 1000));
    if (seconds < 60) return `${seconds} sec ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} min ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hr ago`;
    return `${Math.floor(hours / 24)} days ago`;
  };

  const getHouseStatus = (house: HouseMonitoringSummary | any) => {
    if (house.status === 'no_data') return 'no_data';
    if (!house.is_connected) return 'disconnected';
    if (house.alarm_status === 'critical') return 'critical';
    if (house.alarm_status === 'warning') return 'warning';
    return 'normal';
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          {data.farm_name} - Houses Monitoring ({data.houses_count} houses)
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <ToggleButtonGroup
            size="small"
            exclusive
            value={dataMode}
            onChange={handleDataModeChange}
          >
            <ToggleButton value="cache_only">Job cache</ToggleButton>
            <ToggleButton value="cached_then_live">Current</ToggleButton>
          </ToggleButtonGroup>
          <Button
            size="small"
            variant="contained"
            startIcon={runningNow || activeRun?.status === 'queued' || activeRun?.status === 'running' ? <CircularProgress size={16} color="inherit" /> : <Refresh />}
            onClick={handleRunNow}
            disabled={runningNow || activeRun?.status === 'queued' || activeRun?.status === 'running'}
          >
            Run now
          </Button>
          <Tooltip title="Reload displayed data">
            <IconButton onClick={fetchMonitoringData}>
              <Refresh />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {cacheStatus && (
        <Alert
          severity={cacheStatus.cache.is_stale ? 'warning' : 'success'}
          sx={{ mb: 2 }}
          action={
            <Chip
              size="small"
              color={cacheStatus.cache.is_stale ? 'warning' : 'success'}
              label={cacheStatus.cache.refresh_state}
            />
          }
        >
          Last fetched: {formatDateTime(cacheStatus.cache.fetched_at)} · Data age: {formatAge(cacheStatus.cache.fetched_at)}
          {cacheStatus.latest_runs.scheduled && (
            <> · Last scheduled run: {cacheStatus.latest_runs.scheduled.status}</>
          )}
          {cacheStatus.latest_runs.manual && (
            <> · Last manual run: {cacheStatus.latest_runs.manual.status}</>
          )}
        </Alert>
      )}

      {activeRun && (
        <Alert severity={activeRun.status === 'failed' ? 'error' : activeRun.status === 'partial' ? 'warning' : 'info'} sx={{ mb: 2 }}>
          Manual refresh {activeRun.status}
          {activeRun.farms_processed || activeRun.houses_processed
            ? ` · farms ${activeRun.farms_processed} · houses ${activeRun.houses_processed}`
            : ''}
          {activeRun.error_summary ? ` · ${activeRun.error_summary}` : ''}
        </Alert>
      )}

      {data.houses.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No cached monitoring data is available yet. Use Run now to queue a refresh.
        </Alert>
      )}

      <Grid container spacing={2}>
        {data.houses.map((house: any) => {
          const houseStatus = getHouseStatus(house);
          const hasData = house.status !== 'no_data';
          const houseData = hasData ? house as HouseMonitoringSummary : null;

          return (
            <Grid item xs={12} sm={6} md={4} lg={3} key={house.house_id || house.id}>
              <Card
                sx={{
                  height: '100%',
                  border: houseStatus === 'critical' ? '2px solid' : 'none',
                  borderColor: houseStatus === 'critical' ? 'error.main' : 'transparent',
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 4,
                  },
                }}
                onClick={() => {
                  if (house.house_id || house.id) {
                    navigate(`/houses/${house.house_id || house.id}/monitoring`);
                  }
                }}
              >
                <CardContent>
                  {/* Header */}
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">
                      House {house.house_number}
                    </Typography>
                    <Box display="flex" gap={1}>
                      {houseStatus === 'normal' && hasData && (
                        <CheckCircle color="success" fontSize="small" />
                      )}
                      {houseStatus === 'warning' && (
                        <Warning color="warning" fontSize="small" />
                      )}
                      {(houseStatus === 'critical' || houseStatus === 'disconnected') && (
                        <Error color="error" fontSize="small" />
                      )}
                      {!hasData && (
                        <Chip label="No Data" size="small" variant="outlined" />
                      )}
                    </Box>
                  </Box>

                  {hasData && houseData ? (
                    <>
                      {/* Status Indicators */}
                      <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                        <Chip
                          label={houseData.alarm_status}
                          size="small"
                          color={getStatusColor(houseData.alarm_status) as any}
                        />
                        <Chip
                          label={houseData.is_connected ? 'Connected' : 'Disconnected'}
                          size="small"
                          color={houseData.is_connected ? 'success' : 'error'}
                          variant="outlined"
                        />
                      </Box>

                      {/* Key Metrics */}
                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <Thermostat fontSize="small" color="primary" />
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Temp
                              </Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {formatValue(houseData.average_temperature, '°C')}
                              </Typography>
                            </Box>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <WaterDrop fontSize="small" color="primary" />
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Humidity
                              </Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {formatValue(houseData.humidity, '%')}
                              </Typography>
                            </Box>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <Air fontSize="small" color="primary" />
                            <Box>
                              <Typography variant="caption" color="text.secondary">
                                Pressure
                              </Typography>
                              <Typography variant="body2" fontWeight="bold">
                                {formatValue(houseData.static_pressure, 'hPa')}
                              </Typography>
                            </Box>
                          </Box>
                        </Grid>
                        <Grid item xs={6}>
                          <Box>
                            <Typography variant="caption" color="text.secondary">
                              Growth Day
                            </Typography>
                            <Typography variant="body2" fontWeight="bold">
                              {houseData.growth_day ?? 'N/A'}
                            </Typography>
                          </Box>
                        </Grid>
                      </Grid>

                      {/* Footer */}
                      <Box mt={2} pt={2} borderTop="1px solid" borderColor="divider">
                        <Typography variant="caption" color="text.secondary">
                          Updated: {new Date(houseData.timestamp).toLocaleTimeString()}
                        </Typography>
                      </Box>
                    </>
                  ) : (
                    <Box textAlign="center" py={2}>
                      <Typography variant="body2" color="text.secondary">
                        No monitoring data available
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>
    </Box>
  );
};

export default FarmHousesMonitoring;
