import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Sync as SyncIcon,
  Scale,
  Assessment,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import api from '../../services/api';
import { useFarm } from '../../contexts/FarmContext';
import { useFlock } from '../../contexts/FlockContext';

interface HouseFlockTabProps {
  houseId: string;
  house: any;
}

const HouseFlockTab: React.FC<HouseFlockTabProps> = ({ houseId, house }) => {
  const navigate = useNavigate();
  const { farms } = useFarm();
  const { syncFlockFromRotem } = useFlock();

  const [flocks, setFlocks] = useState<any[]>([]);
  const [activeFlock, setActiveFlock] = useState<any | null>(null);
  const [performanceRecords, setPerformanceRecords] = useState<any[]>([]);
  const [flockSummary, setFlockSummary] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState<{ severity: 'success' | 'error'; text: string } | null>(null);

  const farmForHouse = useMemo(() => {
    const farmId = house?.farm_id ?? house?.farm?.id;
    const fromNested = house?.farm;
    const fromContext = farmId != null ? farms.find((f) => f.id === farmId) : undefined;
    return fromNested || fromContext;
  }, [house, farms]);

  const showRotemSync = farmForHouse?.integration_type === 'rotem';

  useEffect(() => {
    loadFlocks();
  }, [houseId]);

  useEffect(() => {
    if (activeFlock) {
      loadFlockDetails(activeFlock.id);
    } else {
      setPerformanceRecords([]);
      setFlockSummary(null);
    }
  }, [activeFlock]);

  const loadFlocks = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/flocks/`, {
        params: { house_id: houseId, is_active: 'true' },
      });
      const flocksData = Array.isArray(response.data) ? response.data : response.data.results || [];
      setFlocks(flocksData);
      if (flocksData.length > 0) {
        setActiveFlock(flocksData[0]);
      } else {
        setActiveFlock(null);
      }
    } catch (err: any) {
      const d = err.response?.data;
      setError(d?.detail || d?.message || 'Failed to load flock data');
    } finally {
      setLoading(false);
    }
  };

  const loadFlockDetails = async (flockId: number) => {
    try {
      const perfResponse = await api.get(`/flocks/${flockId}/performance/`);
      setPerformanceRecords(Array.isArray(perfResponse.data) ? perfResponse.data : []);

      const summaryResponse = await api.get(`/flocks/${flockId}/summary/`);
      setFlockSummary(summaryResponse.data);
    } catch (err: any) {
      console.error('Error loading flock details:', err);
    }
  };

  const handleSyncFromRotem = async () => {
    setSyncFeedback(null);
    setSyncLoading(true);
    try {
      const result = await syncFlockFromRotem(parseInt(houseId, 10));
      setSyncFeedback({
        severity: 'success',
        text: result.message || (result.created ? 'Flock created from Rotem data.' : 'Flock updated from Rotem data.'),
      });
      await loadFlocks();
      if (result.flock) {
        setActiveFlock(result.flock);
      }
    } catch (err: any) {
      const d = err.response?.data;
      const msg = typeof d?.detail === 'string' ? d.detail : d?.message || err.message || 'Sync failed';
      setSyncFeedback({ severity: 'error', text: msg });
    } finally {
      setSyncLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
      </Alert>
    );
  }

  const currentActiveFlock = activeFlock || flocks.find((f: any) => f.is_active);
  const inferredStart = house?.batch_start_date || house?.chicken_in_date;
  const inferredAge =
    house?.current_age_days != null ? house.current_age_days : undefined;

  const newFlockHref = `/flocks/new?house_id=${houseId}`;

  return (
    <Box>
      {syncFeedback && (
        <Alert severity={syncFeedback.severity} sx={{ mb: 2 }} onClose={() => setSyncFeedback(null)}>
          {syncFeedback.text}
        </Alert>
      )}

      <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2} mb={3}>
        <Typography variant="h6">Flock Information</Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
          {showRotemSync && (
            <Button
              variant="outlined"
              startIcon={syncLoading ? <CircularProgress size={18} /> : <SyncIcon />}
              onClick={handleSyncFromRotem}
              disabled={syncLoading}
            >
              Sync flock information from Rotem Integration
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate(newFlockHref)}
          >
            New Flock
          </Button>
        </Box>
      </Box>

      {!currentActiveFlock ? (
        <Box>
          <Alert severity="info" sx={{ mb: 2 }}>
            No active flock found for this house.
            {showRotemSync
              ? ' Use the sync button to create or update the flock from Rotem house data, or add one manually.'
              : ' Add a flock manually to track performance here.'}
          </Alert>
          {showRotemSync && (
            <Card variant="outlined" sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Inferred from Rotem (house record)
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Batch / start date:{' '}
                  {inferredStart
                    ? new Date(inferredStart).toLocaleDateString()
                    : 'Not set — run house monitoring sync or set batch dates on the house.'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Day-old (age):{' '}
                  {inferredAge != null ? `${inferredAge} days` : 'Unknown'}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Box>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Flock
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Batch: {currentActiveFlock.batch_number}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Breed: {currentActiveFlock.breed_name || currentActiveFlock.breed?.name || 'N/A'}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Status: <Chip label={currentActiveFlock.status} size="small" />
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Start / arrival: {new Date(currentActiveFlock.arrival_date).toLocaleDateString()}
                </Typography>
                {currentActiveFlock.start_date && currentActiveFlock.start_date !== currentActiveFlock.arrival_date && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Start date: {new Date(currentActiveFlock.start_date).toLocaleDateString()}
                  </Typography>
                )}
                {currentActiveFlock.expected_harvest_date && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Expected Harvest: {new Date(currentActiveFlock.expected_harvest_date).toLocaleDateString()}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Flock Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Initial Count
                    </Typography>
                    <Typography variant="h6">
                      {currentActiveFlock.initial_chicken_count?.toLocaleString() || 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Current Count
                    </Typography>
                    <Typography variant="h6">
                      {currentActiveFlock.current_chicken_count?.toLocaleString() || 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Age
                    </Typography>
                    <Typography variant="h6">
                      {currentActiveFlock.current_age_days ?? 0} days
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Livability
                    </Typography>
                    <Typography variant="h6">
                      {currentActiveFlock.livability != null
                        ? `${Number(currentActiveFlock.livability).toFixed(1)}%`
                        : 'N/A'}
                    </Typography>
                    {currentActiveFlock.livability != null && (
                      <LinearProgress
                        variant="determinate"
                        value={Math.min(100, Number(currentActiveFlock.livability))}
                        sx={{ mt: 1, height: 8, borderRadius: 1 }}
                      />
                    )}
                  </Grid>
                  {currentActiveFlock.mortality_count != null && (
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Mortality
                      </Typography>
                      <Typography variant="h6" color="error">
                        {currentActiveFlock.mortality_count}
                      </Typography>
                    </Grid>
                  )}
                  {currentActiveFlock.mortality_rate != null && (
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Mortality Rate
                      </Typography>
                      <Typography variant="h6" color="error">
                        {Number(currentActiveFlock.mortality_rate).toFixed(2)}%
                      </Typography>
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {flockSummary && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Summary
                  </Typography>
                  <Grid container spacing={2}>
                    {flockSummary.average_weight && (
                      <Grid item xs={6} md={3}>
                        <Box textAlign="center">
                          <Scale color="primary" sx={{ fontSize: 40, mb: 1 }} />
                          <Typography variant="caption" color="text.secondary">
                            Avg. Weight
                          </Typography>
                          <Typography variant="h6">
                            {flockSummary.average_weight.toFixed(2)} g
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                    {flockSummary.feed_conversion_ratio && (
                      <Grid item xs={6} md={3}>
                        <Box textAlign="center">
                          <Assessment color="primary" sx={{ fontSize: 40, mb: 1 }} />
                          <Typography variant="caption" color="text.secondary">
                            FCR
                          </Typography>
                          <Typography variant="h6">
                            {flockSummary.feed_conversion_ratio.toFixed(2)}
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                    {flockSummary.total_feed_consumed && (
                      <Grid item xs={6} md={3}>
                        <Box textAlign="center">
                          <Typography variant="caption" color="text.secondary">
                            Total Feed
                          </Typography>
                          <Typography variant="h6">
                            {flockSummary.total_feed_consumed.toFixed(0)} kg
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                    {flockSummary.total_water_consumed && (
                      <Grid item xs={6} md={3}>
                        <Box textAlign="center">
                          <Typography variant="caption" color="text.secondary">
                            Total Water
                          </Typography>
                          <Typography variant="h6">
                            {flockSummary.total_water_consumed.toFixed(0)} L
                          </Typography>
                        </Box>
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}

          {performanceRecords.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Bird Weight Growth
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={performanceRecords.filter((r: any) => r.average_weight_grams)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="flock_age_days"
                        label={{ value: 'Age (days)', position: 'insideBottom', offset: -5 }}
                      />
                      <YAxis label={{ value: 'Weight (g)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="average_weight_grams"
                        stroke="#8884d8"
                        name="Average Weight (g)"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          )}

          {performanceRecords.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Records
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Date</TableCell>
                          <TableCell>Age (days)</TableCell>
                          <TableCell>Avg. Weight (g)</TableCell>
                          <TableCell>FCR</TableCell>
                          <TableCell>Feed (kg)</TableCell>
                          <TableCell>Water (L)</TableCell>
                          <TableCell>Count</TableCell>
                          <TableCell>Livability</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {performanceRecords.slice(0, 10).map((record: any) => (
                          <TableRow key={record.id}>
                            <TableCell>
                              {new Date(record.record_date).toLocaleDateString()}
                            </TableCell>
                            <TableCell>{record.flock_age_days}</TableCell>
                            <TableCell>
                              {record.average_weight_grams ? record.average_weight_grams.toFixed(1) : '---'}
                            </TableCell>
                            <TableCell>
                              {record.feed_conversion_ratio ? record.feed_conversion_ratio.toFixed(2) : '---'}
                            </TableCell>
                            <TableCell>
                              {record.daily_feed_consumption_kg
                                ? record.daily_feed_consumption_kg.toFixed(1)
                                : '---'}
                            </TableCell>
                            <TableCell>
                              {record.daily_water_consumption_liters
                                ? record.daily_water_consumption_liters.toFixed(1)
                                : '---'}
                            </TableCell>
                            <TableCell>{record.current_chicken_count}</TableCell>
                            <TableCell>
                              {record.livability ? `${record.livability.toFixed(1)}%` : '---'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}
    </Box>
  );
};

export default HouseFlockTab;
