import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Refresh,
  Thermostat,
  WaterDrop,
  Air,
  Speed,
  Warning,
  CheckCircle,
  Error,
  LocalFireDepartment,
  TrendingUp,
  TrendingFlat,
} from '@mui/icons-material';
import monitoringApi from '../../services/monitoringApi';
import { HouseMonitoringKpis } from '../../types/monitoring';
import HouseMonitoringCharts from './HouseMonitoringCharts';

/** Command 43 heater history daily row (API `heater_history.daily`). */
interface HeaterHistoryDailyRow {
  growth_day: number;
  date: string | null;
  total_hours: number;
  per_device: Record<string, { hours: number; minutes?: number; raw_value?: unknown }>;
}

function formatShortCalendarDate(isoDate: string): string {
  const parts = isoDate.split('-').map((s) => parseInt(s, 10));
  if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) return isoDate;
  const [y, m, d] = parts;
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: y !== new Date().getFullYear() ? 'numeric' : undefined,
  });
}

interface HouseOverviewTabProps {
  house: any;
  monitoring: any;
  alarms: any[];
  stats: any;
  onRefresh: () => void;
  /** Day-over-day reference date (YYYY-MM-DD), controlled from URL / storage */
  dodReferenceDate: string | null;
  onDodReferenceDateChange: (date: string | null) => void;
  /** Navigate to Water History tab; optional calendar day to highlight */
  onNavigateToWaterHistory?: (focusDate?: string | null) => void;
}

const HouseOverviewTab: React.FC<HouseOverviewTabProps> = ({
  house,
  monitoring,
  alarms,
  stats,
  onRefresh,
  dodReferenceDate,
  onDodReferenceDateChange,
  onNavigateToWaterHistory,
}) => {
  const [kpis, setKpis] = useState<HouseMonitoringKpis | null>(null);
  const [kpiLoading, setKpiLoading] = useState(false);
  const [heaterHistory, setHeaterHistory] = useState<any>(null);
  const [heaterRotemLoading, setHeaterRotemLoading] = useState(false);
  const [heaterCacheLoading, setHeaterCacheLoading] = useState(false);
  const [heaterError, setHeaterError] = useState<string | null>(null);
  const [selectedHeaterGrowthDay, setSelectedHeaterGrowthDay] = useState<number | null>(null);
  const [heaterDetailOpen, setHeaterDetailOpen] = useState(false);
  const [trendOpen, setTrendOpen] = useState(false);
  const [trendMetric, setTrendMetric] = useState<'water' | 'feed'>('water');
  const dodRef = useRef(dodReferenceDate);
  dodRef.current = dodReferenceDate;

  useEffect(() => {
    setSelectedHeaterGrowthDay(null);
    setHeaterHistory(null);
    setHeaterError(null);
  }, [house?.id]);

  useEffect(() => {
    const loadKpis = async () => {
      if (!house?.id) return;
      try {
        setKpiLoading(true);
        const result = await monitoringApi.getHouseMonitoringKpis(house.id, {
          dodReferenceDate: dodReferenceDate ?? undefined,
        });
        setKpis(result);
      } catch (error) {
        console.error('Failed to load house monitoring KPIs:', error);
        setKpis(null);
      } finally {
        setKpiLoading(false);
      }
    };
    loadKpis();
  }, [house?.id, monitoring?.timestamp, dodReferenceDate]);

  const applyHeaterHistoryPayload = useCallback(
    (hist: Record<string, unknown>, alignDod: string | null | undefined) => {
      setHeaterHistory(hist);
      const daily = hist?.daily as HeaterHistoryDailyRow[] | undefined;
      if (daily && daily.length > 0) {
        const match =
          alignDod != null && alignDod !== ''
            ? daily.find((r) => r.date === alignDod)
            : undefined;
        const pick = match || daily[daily.length - 1];
        setSelectedHeaterGrowthDay(pick.growth_day);
      } else {
        setSelectedHeaterGrowthDay(null);
      }
    },
    []
  );

  /** Auto-load cached heater history when house changes (cheap path; Rotem fetch stays manual). */
  useEffect(() => {
    if (!house?.id) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await monitoringApi.getHouseHeaterHistory(house.id);
        if (cancelled) return;
        applyHeaterHistoryPayload(data.heater_history as Record<string, unknown>, dodRef.current);
      } catch {
        /* ignore — user can load manually */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [house?.id, applyHeaterHistoryPayload]);

  const loadHeaterHistoryCached = async () => {
    if (!house?.id) return;
    try {
      setHeaterCacheLoading(true);
      setHeaterError(null);
      const data = await monitoringApi.getHouseHeaterHistory(house.id);
      applyHeaterHistoryPayload(data.heater_history as Record<string, unknown>, dodRef.current);
    } catch (error) {
      console.error('Failed to load cached heater history:', error);
      setHeaterError('Could not load saved heater history.');
    } finally {
      setHeaterCacheLoading(false);
    }
  };

  const fetchHeaterHistoryFromRotem = async () => {
    if (!house?.id) return;
    try {
      setHeaterRotemLoading(true);
      setHeaterError(null);
      const data = await monitoringApi.refreshHouseHeaterHistory(house.id);
      applyHeaterHistoryPayload(data.heater_history as Record<string, unknown>, dodRef.current);
    } catch (error: any) {
      const msg =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        'Failed to fetch heater history from Rotem.';
      setHeaterError(typeof msg === 'string' ? msg : 'Failed to fetch heater history from Rotem.');
    } finally {
      setHeaterRotemLoading(false);
    }
  };

  const getTrendColor = (deltaPct: number | null | undefined): 'success' | 'warning' | 'error' | 'default' => {
    if (deltaPct === null || deltaPct === undefined) return 'default';
    const abs = Math.abs(deltaPct);
    if (abs <= 10) return 'success';
    if (abs <= 25) return 'warning';
    return 'error';
  };

  const formatDelta = (delta: number | null | undefined, pct: number | null | undefined, unit = ''): string => {
    if (delta === null || delta === undefined || pct === null || pct === undefined) return 'N/A';
    const sign = delta >= 0 ? '+' : '';
    return `${sign}${delta.toFixed(1)}${unit} (${sign}${pct.toFixed(1)}%)`;
  };
  const formatTemperature = (temp: number | null | string | undefined): string => {
    if (temp === null || temp === undefined || temp === '') return '---';
    const numTemp = typeof temp === 'string' ? parseFloat(temp) : temp;
    if (isNaN(numTemp)) return '---';
    return `${numTemp.toFixed(1)} F°`;
  };

  const formatHumidity = (humidity: number | null | string | undefined): string => {
    if (humidity === null || humidity === undefined || humidity === '') return '---';
    const numHumidity = typeof humidity === 'string' ? parseFloat(humidity) : humidity;
    if (isNaN(numHumidity)) return '---';
    return `${Math.round(numHumidity)} %`;
  };

  const formatPressure = (pressure: number | null | string | undefined): string => {
    if (pressure === null || pressure === undefined || pressure === '') return '0.000';
    const numPressure = typeof pressure === 'string' ? parseFloat(pressure) : pressure;
    if (isNaN(numPressure)) return '0.000';
    return numPressure.toFixed(3);
  };

  const formatTime = (time: string | null): string => {
    if (!time) return '---';
    try {
      const date = new Date(time);
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '---';
    }
  };

  const formatDodCaption = (
    current: number | null | undefined,
    previous: number | null | undefined,
    unit: string
  ): string => {
    const ctx = kpis?.day_over_day_context;
    const curTitle = ctx?.reference_date ? formatShortCalendarDate(ctx.reference_date) : 'Today';
    const prevTitle = ctx?.compare_date ? formatShortCalendarDate(ctx.compare_date) : 'Yesterday';
    const fmt = (v: number | null | undefined) =>
      v != null && !Number.isNaN(v) ? v.toFixed(1) : 'N/A';
    return `${curTitle}: ${fmt(current)}${unit} | ${prevTitle}: ${fmt(previous)}${unit}`;
  };

  const heaterDaily: HeaterHistoryDailyRow[] = Array.isArray(
    (heaterHistory as { daily?: HeaterHistoryDailyRow[] } | null)?.daily
  )
    ? ((heaterHistory as { daily: HeaterHistoryDailyRow[] }).daily)
    : [];
  const selectedHeaterRow =
    selectedHeaterGrowthDay != null
      ? heaterDaily.find((r) => r.growth_day === selectedHeaterGrowthDay)
      : undefined;

  useEffect(() => {
    const daily = heaterHistory?.daily as HeaterHistoryDailyRow[] | undefined;
    if (!daily?.length || dodReferenceDate == null || dodReferenceDate === '') return;
    const row = daily.find((r) => r.date === dodReferenceDate);
    if (row) setSelectedHeaterGrowthDay(row.growth_day);
  }, [dodReferenceDate, heaterHistory]);

  if (!monitoring) {
    return (
      <Box textAlign="center" py={4}>
        <Typography variant="body1" color="text.secondary">
          No monitoring data available
        </Typography>
        <IconButton onClick={onRefresh} sx={{ mt: 2 }}>
          <Refresh />
        </IconButton>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Real-Time Monitoring</Typography>
        <IconButton onClick={onRefresh}>
          <Refresh />
        </IconButton>
      </Box>

      <Grid container spacing={3}>
        {/* New KPI Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Box display="flex" alignItems="center" gap={1}>
                  <LocalFireDepartment color="error" />
                  <Typography variant="subtitle2">Heater Runtime (24h)</Typography>
                </Box>
                <Chip
                  size="small"
                  color={kpis?.heater_runtime?.hours_24h && kpis.heater_runtime.hours_24h > 8 ? 'warning' : 'success'}
                  label={kpiLoading ? 'Loading...' : `${kpis?.heater_runtime?.hours_24h ?? 0} h`}
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                Cycles: {kpis?.heater_runtime?.cycles_24h ?? 'N/A'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Estimated from status snapshots
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card
            variant="outlined"
            sx={{
              borderRadius: 2,
              boxShadow: 1,
              bgcolor: 'background.paper',
            }}
          >
            <CardContent>
              <Box display="flex" flexWrap="wrap" justifyContent="space-between" alignItems="center" gap={1} mb={1}>
                <Typography variant="h6">Heater History (Command 43)</Typography>
                <Box display="flex" flexWrap="wrap" gap={1} alignItems="center">
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={loadHeaterHistoryCached}
                    disabled={heaterCacheLoading || heaterRotemLoading}
                    startIcon={heaterCacheLoading ? <CircularProgress size={16} /> : undefined}
                  >
                    Load saved
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={fetchHeaterHistoryFromRotem}
                    disabled={heaterRotemLoading}
                    startIcon={heaterRotemLoading ? <CircularProgress size={16} color="inherit" /> : undefined}
                  >
                    Fetch from Rotem
                  </Button>
                  {heaterHistory?.freshness?.sync_status ? (
                    <Chip
                      size="small"
                      color={heaterHistory?.freshness?.stale ? 'warning' : 'success'}
                      label={heaterHistory.freshness.sync_status}
                    />
                  ) : null}
                </Box>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={1}>
                Cached history loads automatically when you open Overview; use &quot;Fetch from Rotem&quot; for the
                latest from the controller. Select a row to align water/feed day-over-day with that calendar day.
              </Typography>
              {heaterError && (
                <Alert severity="error" sx={{ mb: 1 }} onClose={() => setHeaterError(null)}>
                  {heaterError}
                </Alert>
              )}
              {heaterRotemLoading && <LinearProgress sx={{ mb: 1 }} />}
              <Typography variant="body2" color="text.secondary" mb={2}>
                Total: {heaterHistory?.summary?.total_hours ?? '—'} h (
                {heaterHistory?.summary?.days_count ?? 0} days, {heaterHistory?.summary?.device_count ?? 0}{' '}
                devices)
              </Typography>

              {heaterDaily.length > 0 ? (
                <>
                  <TableContainer
                    component={Paper}
                    variant="outlined"
                    sx={{
                      maxHeight: 320,
                      borderRadius: 1,
                      '& .MuiTableCell-head': {
                        bgcolor: 'action.hover',
                        fontWeight: 600,
                        whiteSpace: 'nowrap',
                      },
                    }}
                  >
                    <Table size="small" stickyHeader>
                      <TableHead>
                        <TableRow>
                          <TableCell>Growth day</TableCell>
                          <TableCell>Date</TableCell>
                          <TableCell align="right">Total</TableCell>
                          <TableCell>Devices (summary)</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {heaterDaily.map((row) => {
                          const deviceSummary = Object.entries(row.per_device || {})
                            .map(([k, v]) => `${k.replace(/_/g, ' ')} ${v.hours}h`)
                            .join(', ');
                          const shortSummary =
                            deviceSummary.length > 56 ? `${deviceSummary.slice(0, 53)}…` : deviceSummary;
                          return (
                            <TableRow
                              key={row.growth_day}
                              hover
                              selected={selectedHeaterGrowthDay === row.growth_day}
                              onClick={() => {
                                setSelectedHeaterGrowthDay(row.growth_day);
                                onDodReferenceDateChange(row.date ?? null);
                              }}
                              sx={{
                                cursor: 'pointer',
                                '&.Mui-selected': {
                                  bgcolor: 'action.selected',
                                },
                                '&:last-child td': { borderBottom: 0 },
                              }}
                            >
                              <TableCell>Day {row.growth_day}</TableCell>
                              <TableCell>{row.date ?? '—'}</TableCell>
                              <TableCell align="right">{row.total_hours} h</TableCell>
                              <TableCell>
                                <Typography variant="body2" color="text.secondary" noWrap title={deviceSummary}>
                                  {shortSummary || '—'}
                                </Typography>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  {selectedHeaterRow ? (
                    <Box
                      mt={2}
                      pt={2}
                      sx={{
                        borderTop: 1,
                        borderColor: 'divider',
                      }}
                    >
                      <Box display="flex" flexWrap="wrap" alignItems="center" justifyContent="space-between" gap={1}>
                        <Typography variant="subtitle2" color="text.secondary">
                          Selected — Day {selectedHeaterRow.growth_day}
                          {selectedHeaterRow.date ? ` · ${selectedHeaterRow.date}` : ''} — per device
                        </Typography>
                        <Button size="small" variant="outlined" onClick={() => setHeaterDetailOpen(true)}>
                          Open day details
                        </Button>
                      </Box>
                      <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
                        {Object.entries(selectedHeaterRow.per_device || {}).map(([device, value]) => (
                          <Chip
                            key={device}
                            size="small"
                            variant="outlined"
                            label={`${device.replace(/_/g, ' ')}: ${value.hours} h`}
                          />
                        ))}
                      </Box>
                    </Box>
                  ) : null}
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Click &quot;Load saved&quot; or &quot;Fetch from Rotem&quot; to show heater runtime by day.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            variant="outlined"
            sx={{
              cursor: onNavigateToWaterHistory ? 'pointer' : 'default',
              transition: 'box-shadow 0.2s',
              '&:hover': onNavigateToWaterHistory ? { boxShadow: 2 } : {},
            }}
            onClick={() => {
              if (onNavigateToWaterHistory) {
                onNavigateToWaterHistory(kpis?.day_over_day_context?.reference_date ?? null);
              }
            }}
          >
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                <Box display="flex" alignItems="center" gap={1}>
                  <TrendingUp color="info" />
                  <Typography variant="subtitle2">Water Day-over-Day</Typography>
                </Box>
                <Box display="flex" flexDirection="column" alignItems="flex-end" gap={0.5}>
                  <Chip
                    size="small"
                    color={getTrendColor(kpis?.water_day_over_day?.delta_pct)}
                    label={formatDelta(kpis?.water_day_over_day?.delta, kpis?.water_day_over_day?.delta_pct, 'L')}
                  />
                  <Tooltip title="Short-term trend (snapshots)">
                    <Button
                      size="small"
                      variant="text"
                      onClick={(e) => {
                        e.stopPropagation();
                        setTrendMetric('water');
                        setTrendOpen(true);
                      }}
                    >
                      View trend
                    </Button>
                  </Tooltip>
                </Box>
              </Box>
              <Typography variant="caption" color="text.secondary" component="div">
                {formatDodCaption(
                  kpis?.water_day_over_day?.current,
                  kpis?.water_day_over_day?.previous,
                  'L'
                )}
              </Typography>
              {onNavigateToWaterHistory && (
                <Typography variant="caption" color="primary" sx={{ mt: 0.5, display: 'block' }}>
                  Click card to open Water History
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            variant="outlined"
            sx={{ cursor: 'pointer', transition: 'box-shadow 0.2s', '&:hover': { boxShadow: 2 } }}
            onClick={() => {
              setTrendMetric('feed');
              setTrendOpen(true);
            }}
          >
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                <Box display="flex" alignItems="center" gap={1}>
                  <TrendingFlat color="secondary" />
                  <Typography variant="subtitle2">Feed Day-over-Day</Typography>
                </Box>
                <Chip
                  size="small"
                  color={getTrendColor(kpis?.feed_day_over_day?.delta_pct)}
                  label={formatDelta(kpis?.feed_day_over_day?.delta, kpis?.feed_day_over_day?.delta_pct, 'lb')}
                />
              </Box>
              <Typography variant="caption" color="text.secondary" component="div">
                {formatDodCaption(
                  kpis?.feed_day_over_day?.current,
                  kpis?.feed_day_over_day?.previous,
                  'lb'
                )}
              </Typography>
              <Typography variant="caption" color="primary" sx={{ mt: 0.5, display: 'block' }}>
                Click card for consumption trend
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Average Temperature */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Box display="flex" alignItems="center" gap={1}>
                  <Thermostat color="primary" />
                  <Typography variant="h6">Avg. Temperature</Typography>
                </Box>
                <Chip
                  label={formatTemperature(monitoring.average_temperature)}
                  color="primary"
                  size="small"
                />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Set: {formatTemperature(monitoring.target_temperature)}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Offset: 0.0 F°
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Out: {formatTemperature(monitoring.outside_temperature)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Humidity */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Box display="flex" alignItems="center" gap={1}>
                  <WaterDrop color="info" />
                  <Typography variant="subtitle2">Humidity</Typography>
                </Box>
              </Box>
              <Typography variant="h5" gutterBottom>
                {formatHumidity(monitoring.humidity)}
              </Typography>
              <Chip label="Off" size="small" variant="outlined" />
            </CardContent>
          </Card>
        </Grid>

        {/* Static Pressure */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Box display="flex" alignItems="center" gap={1}>
                  <Air color="secondary" />
                  <Typography variant="subtitle2">S.Pressure</Typography>
                </Box>
              </Box>
              <Typography variant="h5" gutterBottom>
                {formatPressure(monitoring.static_pressure)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                BAR
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Ventilation Level */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Vent. Level
              </Typography>
              <Typography variant="h4" gutterBottom>
                {monitoring.airflow_cfm ? monitoring.airflow_cfm.toLocaleString() : '0'} CFM
              </Typography>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Min: 6 | Max: 30
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={monitoring.airflow_percentage || 0}
                  sx={{ mt: 1, height: 8, borderRadius: 4 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {monitoring.airflow_percentage || 0} %
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" gutterBottom>
                  Minimum Vent.
                </Typography>
                <Chip
                  label={monitoring.ventilation_level ? 'On' : 'Off'}
                  color={monitoring.ventilation_level ? 'success' : 'default'}
                  size="small"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Temperature Sensors */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Temperature Sensors
              </Typography>
              <Grid container spacing={2}>
                {monitoring.sensor_data && Object.entries(monitoring.sensor_data).slice(0, 8).map(([key, value]: [string, any]) => (
                  <Grid item xs={6} sm={3} key={key}>
                    <Box textAlign="center">
                      <Typography variant="caption" color="text.secondary">
                        {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Typography>
                      <Typography variant="h6">
                        {formatTemperature(value)}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Device Status */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Device Status
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={4} md={2}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      Heaters
                    </Typography>
                    <Typography variant="body1">
                      Off / 8
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      Tunnel Fans
                    </Typography>
                    <Typography variant="body1">
                      {monitoring.ventilation_level ? '1' : '0'} / 14
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      Exh Fans
                    </Typography>
                    <Typography variant="body1">
                      {monitoring.ventilation_level ? '1' : '0'} / 4
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      Stir Fans
                    </Typography>
                    <Typography variant="body1">
                      Off / 2
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      Cooling Pad
                    </Typography>
                    <Typography variant="body1">
                      Off / 4
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      Light
                    </Typography>
                    <Typography variant="body1">
                      2 / 4
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Livability */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Livability
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Box flex={1}>
                  <LinearProgress
                    variant="determinate"
                    value={monitoring.livability || 100}
                    sx={{ height: 20, borderRadius: 2 }}
                  />
                  <Typography variant="h4" mt={1}>
                    {monitoring.livability || 100}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {monitoring.bird_count || 0} Birds
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Daily Consumption */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Daily Consumption
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      Water (WOD)
                    </Typography>
                    <Typography variant="h6">
                      {monitoring.water_consumption ? monitoring.water_consumption.toFixed(0) : '0'}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      Feed (LB)
                    </Typography>
                    <Typography variant="h6">
                      {monitoring.feed_consumption ? monitoring.feed_consumption.toFixed(0) : '0'}
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      FCR
                    </Typography>
                    <Typography variant="h6">
                      N/A
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box textAlign="center">
                    <Typography variant="caption" color="text.secondary">
                      W/F
                    </Typography>
                    <Typography variant="h6">
                      N/A
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={heaterDetailOpen} onClose={() => setHeaterDetailOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Heater runtime — Day {selectedHeaterRow?.growth_day ?? '—'}
          {selectedHeaterRow?.date ? ` · ${selectedHeaterRow.date}` : ''}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Per-device hours for the selected day
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={0.5}>
            {selectedHeaterRow &&
              Object.entries(selectedHeaterRow.per_device || {}).map(([device, value]) => (
                <Chip
                  key={device}
                  size="medium"
                  variant="outlined"
                  label={`${device.replace(/_/g, ' ')}: ${value.hours} h`}
                />
              ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHeaterDetailOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={trendOpen} onClose={() => setTrendOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {trendMetric === 'water' ? 'Water' : 'Feed'} — recent snapshots
        </DialogTitle>
        <DialogContent>
          {house?.id ? (
            <HouseMonitoringCharts houseId={house.id} highlightMetric={trendMetric} />
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTrendOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HouseOverviewTab;

