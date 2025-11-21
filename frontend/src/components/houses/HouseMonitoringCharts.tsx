import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  CircularProgress,
  Alert,
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent,
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
  ComposedChart,
  Bar,
} from 'recharts';
import dayjs from 'dayjs';
import monitoringApi from '../../services/monitoringApi';
import { HouseMonitoringSummary } from '../../types/monitoring';

interface HouseMonitoringChartsProps {
  houseId: number;
}

const HouseMonitoringCharts: React.FC<HouseMonitoringChartsProps> = ({ houseId }) => {
  const [history, setHistory] = useState<HouseMonitoringSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<number>(24); // hours

  useEffect(() => {
    fetchHistory();
  }, [houseId, period]);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const endDate = new Date().toISOString();
      const startDate = new Date(Date.now() - period * 60 * 60 * 1000).toISOString();
      
      const data = await monitoringApi.getHouseMonitoringHistory(
        houseId,
        startDate,
        endDate,
        200
      );
      setHistory(data.results);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch historical data');
    } finally {
      setLoading(false);
    }
  };

  const handlePeriodChange = (event: SelectChangeEvent<number>) => {
    setPeriod(event.target.value as number);
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
      <Alert severity="error">{error}</Alert>
    );
  }

  if (history.length === 0) {
    return (
      <Alert severity="info">No historical data available for the selected period</Alert>
    );
  }

  // Prepare chart data
  const chartData = history.map((snapshot) => ({
    time: dayjs(snapshot.timestamp).format('HH:mm'),
    date: dayjs(snapshot.timestamp).format('MM/DD HH:mm'),
    temperature: snapshot.average_temperature,
    targetTemp: snapshot.target_temperature,
    outsideTemp: snapshot.outside_temperature,
    humidity: snapshot.humidity,
    pressure: snapshot.static_pressure,
    ventilation: snapshot.ventilation_level,
    water: snapshot.water_consumption,
    feed: snapshot.feed_consumption,
  }));

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">Historical Data</Typography>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <Select value={period} onChange={handlePeriodChange}>
            <MenuItem value={6}>Last 6 hours</MenuItem>
            <MenuItem value={12}>Last 12 hours</MenuItem>
            <MenuItem value={24}>Last 24 hours</MenuItem>
            <MenuItem value={48}>Last 48 hours</MenuItem>
            <MenuItem value={168}>Last 7 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Grid container spacing={2}>
        {/* Temperature Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Temperature Trends
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis label={{ value: '°C', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="temperature"
                    stroke="#1976d2"
                    name="Temperature"
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="targetTemp"
                    stroke="#ff9800"
                    name="Target"
                    strokeDasharray="5 5"
                  />
                  <Line
                    type="monotone"
                    dataKey="outsideTemp"
                    stroke="#757575"
                    name="Outside"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Humidity & Pressure Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Humidity & Pressure
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis yAxisId="left" label={{ value: 'Humidity (%)', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="right" orientation="right" label={{ value: 'Pressure (hPa)', angle: 90, position: 'insideRight' }} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="humidity" fill="#42a5f5" name="Humidity (%)" />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="pressure"
                    stroke="#e91e63"
                    name="Pressure (hPa)"
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Ventilation Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Ventilation Level
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis label={{ value: 'Ventilation (%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="ventilation"
                    stroke="#4caf50"
                    name="Ventilation Level"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Consumption Chart */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                Consumption
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis yAxisId="left" label={{ value: 'Water (L)', angle: -90, position: 'insideLeft' }} />
                  <YAxis yAxisId="right" orientation="right" label={{ value: 'Feed (kg)', angle: 90, position: 'insideRight' }} />
                  <Tooltip />
                  <Legend />
                  <Bar yAxisId="left" dataKey="water" fill="#2196f3" name="Water (L/day)" />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="feed"
                    stroke="#ff5722"
                    name="Feed (kg/day)"
                    strokeWidth={2}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HouseMonitoringCharts;

