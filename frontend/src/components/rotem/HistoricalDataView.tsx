import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';
import { useParams } from 'react-router-dom';
import { rotemApi } from '../../services/rotemApi';
import { RotemDailySummary, RotemFarm, RotemController } from '../../types/rotem';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`historical-tabpanel-${index}`}
      aria-labelledby={`historical-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const HistoricalDataView: React.FC = () => {
  const { farmId } = useParams<{ farmId?: string }>();
  const [farms, setFarms] = useState<RotemFarm[]>([]);
  const [controllers, setControllers] = useState<RotemController[]>([]);
  const [selectedFarmId, setSelectedFarmId] = useState<string>(farmId || '');
  const [selectedControllerId, setSelectedControllerId] = useState<number | ''>('');
  const [startDate, setStartDate] = useState<Dayjs | null>(dayjs().subtract(30, 'days'));
  const [endDate, setEndDate] = useState<Dayjs | null>(dayjs());
  const [summaries, setSummaries] = useState<RotemDailySummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    loadFarms();
    if (farmId) {
      loadControllers();
    }
  }, [farmId]);

  useEffect(() => {
    if (selectedFarmId) {
      loadControllers();
    } else {
      setControllers([]);
    }
  }, [selectedFarmId]);

  const loadFarms = async () => {
    try {
      const farmData = await rotemApi.getFarms();
      setFarms(farmData);
    } catch (err) {
      console.error('Error loading farms:', err);
    }
  };

  const loadControllers = async () => {
    try {
      const controllerData = await rotemApi.getControllers();
      const filtered = selectedFarmId
        ? controllerData.filter(c => c.farm_name?.includes(selectedFarmId) || c.farm === parseInt(selectedFarmId))
        : controllerData;
      setControllers(filtered);
    } catch (err) {
      console.error('Error loading controllers:', err);
    }
  };

  const loadHistoricalData = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params: any = {
        start_date: startDate.format('YYYY-MM-DD'),
        end_date: endDate.format('YYYY-MM-DD'),
      };

      if (selectedFarmId) {
        params.farm_id = selectedFarmId;
      }

      if (selectedControllerId) {
        params.controller_id = selectedControllerId;
      }

      const data = await rotemApi.getDailySummaries(params);
      setSummaries(data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load historical data');
      console.error('Error loading historical data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Prepare chart data
  const temperatureData = summaries
    .filter(s => s.temperature_avg !== null)
    .map(s => ({
      date: dayjs(s.date).format('MMM DD'),
      avg: s.temperature_avg,
      min: s.temperature_min,
      max: s.temperature_max,
    }));

  const humidityData = summaries
    .filter(s => s.humidity_avg !== null)
    .map(s => ({
      date: dayjs(s.date).format('MMM DD'),
      avg: s.humidity_avg,
      min: s.humidity_min,
      max: s.humidity_max,
    }));

  const anomaliesData = summaries.map(s => ({
    date: dayjs(s.date).format('MMM DD'),
    anomalies: s.anomalies_count,
    warnings: s.warnings_count,
    errors: s.errors_count,
  }));

  const consumptionData = summaries
    .filter(s => s.water_consumption_avg !== null || s.feed_consumption_avg !== null)
    .map(s => ({
      date: dayjs(s.date).format('MMM DD'),
      water: s.water_consumption_avg || 0,
      feed: s.feed_consumption_avg || 0,
    }));

  // Calculate statistics
  const totalDataPoints = summaries.reduce((sum, s) => sum + s.total_data_points, 0);
  const totalAnomalies = summaries.reduce((sum, s) => sum + s.anomalies_count, 0);
  const avgTemperature = summaries
    .filter(s => s.temperature_avg !== null)
    .reduce((sum, s) => sum + (s.temperature_avg || 0), 0) / summaries.filter(s => s.temperature_avg !== null).length || 0;
  const avgHumidity = summaries
    .filter(s => s.humidity_avg !== null)
    .reduce((sum, s) => sum + (s.humidity_avg || 0), 0) / summaries.filter(s => s.humidity_avg !== null).length || 0;

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Typography variant="h5" component="h1" gutterBottom>
          Historical Data Analysis
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          View and analyze historical sensor data aggregated by day
        </Typography>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Farm</InputLabel>
                  <Select
                    value={selectedFarmId}
                    onChange={(e) => {
                      setSelectedFarmId(e.target.value);
                      setSelectedControllerId('');
                    }}
                    label="Farm"
                  >
                    <MenuItem value="">All Farms</MenuItem>
                    {farms.map((farm) => (
                      <MenuItem key={farm.farm_id} value={farm.farm_id}>
                        {farm.farm_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth disabled={!selectedFarmId}>
                  <InputLabel>Controller</InputLabel>
                  <Select
                    value={selectedControllerId}
                    onChange={(e) => setSelectedControllerId(e.target.value as number | '')}
                    label="Controller"
                  >
                    <MenuItem value="">All Controllers</MenuItem>
                    {controllers.map((controller) => (
                      <MenuItem key={controller.id} value={controller.id}>
                        {controller.controller_name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6} md={2}>
                <DatePicker
                  label="Start Date"
                  value={startDate}
                  onChange={(newValue) => setStartDate(newValue)}
                  maxDate={endDate || undefined}
                  slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={2}>
                <DatePicker
                  label="End Date"
                  value={endDate}
                  onChange={(newValue) => setEndDate(newValue)}
                  minDate={startDate || undefined}
                  maxDate={dayjs()}
                  slotProps={{ textField: { fullWidth: true, size: 'small' } }}
                />
              </Grid>

              <Grid item xs={12} sm={12} md={2}>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={loadHistoricalData}
                  disabled={loading || !startDate || !endDate}
                >
                  {loading ? <CircularProgress size={24} /> : 'Load Data'}
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {summaries.length === 0 && !loading && (
          <Alert severity="info" sx={{ mb: 3 }}>
            No data available. Select filters and click "Load Data" to view historical data.
          </Alert>
        )}

        {summaries.length > 0 && (
          <>
            {/* Summary Statistics */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Total Data Points
                  </Typography>
                  <Typography variant="h4">{totalDataPoints.toLocaleString()}</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Avg Temperature
                  </Typography>
                  <Typography variant="h4">{avgTemperature.toFixed(1)}°C</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Avg Humidity
                  </Typography>
                  <Typography variant="h4">{avgHumidity.toFixed(1)}%</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Total Anomalies
                  </Typography>
                  <Typography variant="h4" color={totalAnomalies > 0 ? 'error' : 'inherit'}>
                    {totalAnomalies}
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            {/* Charts Tabs */}
            <Card>
              <CardContent>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                  <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
                    <Tab label="Temperature" />
                    <Tab label="Humidity" />
                    <Tab label="Anomalies" />
                    <Tab label="Consumption" />
                  </Tabs>
                </Box>

                <TabPanel value={tabValue} index={0}>
                  {temperatureData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={temperatureData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft' }} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="avg" stroke="#1976d2" name="Average" strokeWidth={2} />
                        <Line type="monotone" dataKey="min" stroke="#4caf50" name="Minimum" strokeWidth={1} strokeDasharray="5 5" />
                        <Line type="monotone" dataKey="max" stroke="#f44336" name="Maximum" strokeWidth={1} strokeDasharray="5 5" />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <Typography color="textSecondary">No temperature data available</Typography>
                    </Box>
                  )}
                </TabPanel>

                <TabPanel value={tabValue} index={1}>
                  {humidityData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={humidityData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis label={{ value: 'Humidity (%)', angle: -90, position: 'insideLeft' }} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="avg" stroke="#1976d2" name="Average" strokeWidth={2} />
                        <Line type="monotone" dataKey="min" stroke="#4caf50" name="Minimum" strokeWidth={1} strokeDasharray="5 5" />
                        <Line type="monotone" dataKey="max" stroke="#f44336" name="Maximum" strokeWidth={1} strokeDasharray="5 5" />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <Typography color="textSecondary">No humidity data available</Typography>
                    </Box>
                  )}
                </TabPanel>

                <TabPanel value={tabValue} index={2}>
                  {anomaliesData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={anomaliesData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="anomalies" fill="#ff9800" name="Anomalies" />
                        <Bar dataKey="warnings" fill="#ffc107" name="Warnings" />
                        <Bar dataKey="errors" fill="#f44336" name="Errors" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <Typography color="textSecondary">No anomaly data available</Typography>
                    </Box>
                  )}
                </TabPanel>

                <TabPanel value={tabValue} index={3}>
                  {consumptionData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={consumptionData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="water" fill="#2196f3" name="Water (L/h)" />
                        <Bar dataKey="feed" fill="#4caf50" name="Feed (kg/h)" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <Typography color="textSecondary">No consumption data available</Typography>
                    </Box>
                  )}
                </TabPanel>
              </CardContent>
            </Card>
          </>
        )}
      </Box>
    </LocalizationProvider>
  );
};

export default HistoricalDataView;

