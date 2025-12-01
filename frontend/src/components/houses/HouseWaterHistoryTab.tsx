import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { House } from '../../types';
import { rotemApi } from '../../services/rotemApi';
import { useFarm } from '../../contexts/FarmContext';
import dayjs from 'dayjs';

interface HouseWaterHistoryTabProps {
  houseId: string;
  house: House & { farm?: { is_integrated?: boolean } };
}

export const HouseWaterHistoryTab: React.FC<HouseWaterHistoryTabProps> = ({ houseId, house }) => {
  const { farms } = useFarm();
  const [waterHistory, setWaterHistory] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [daysFilter, setDaysFilter] = useState<number>(30);
  const isRequestInFlightRef = useRef<boolean>(false);

  // Get farm info to check if it's integrated
  const farm = house.farm_id ? farms.find(f => f.id === house.farm_id) : null;
  const isIntegrated = house.farm?.is_integrated || farm?.is_integrated || false;

  const loadWaterHistory = useCallback(async () => {
    // Prevent duplicate concurrent requests
    if (isRequestInFlightRef.current) {
      return;
    }

    if (!isIntegrated) {
      setError('This house is not connected to a Rotem-integrated farm');
      setLoading(false);
      return;
    }

    isRequestInFlightRef.current = true;
    setLoading(true);
    setError(null);

    try {
      const data = await rotemApi.getWaterHistory({
        house_id: parseInt(houseId),
        days: daysFilter,
      });
      setWaterHistory(data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load water history');
    } finally {
      setLoading(false);
      isRequestInFlightRef.current = false;
    }
  }, [houseId, daysFilter, isIntegrated]);

  useEffect(() => {
    loadWaterHistory();
  }, [loadWaterHistory]);

  if (loading) {
    return <CircularProgress />;
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!waterHistory || !waterHistory.water_history || waterHistory.water_history.length === 0) {
    return (
      <Alert severity="info">
        No water consumption history available for this house. Data will appear once Rotem integration starts collecting data.
      </Alert>
    );
  }

  // Prepare chart data
  const chartData = waterHistory.water_history.map((entry: any) => ({
    date: dayjs(entry.date).format('MMM DD'),
    fullDate: entry.date,
    avg: entry.consumption_avg,
    min: entry.consumption_min,
    max: entry.consumption_max,
  }));

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Water Consumption History - House {house.house_number}</Typography>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Time Period</InputLabel>
          <Select
            value={daysFilter}
            label="Time Period"
            onChange={(e) => setDaysFilter(e.target.value as number)}
          >
            <MenuItem value={7}>Last 7 days</MenuItem>
            <MenuItem value={30}>Last 30 days</MenuItem>
            <MenuItem value={60}>Last 60 days</MenuItem>
            <MenuItem value={90}>Last 90 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Average Daily Consumption</Typography>
              <Typography variant="h4">
                {waterHistory.average_consumption.toFixed(2)} L/day
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Days Recorded</Typography>
              <Typography variant="h4">{waterHistory.total_days}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Farm</Typography>
              <Typography variant="h6">{waterHistory.farm_name || 'N/A'}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Water Consumption Trend</Typography>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis label={{ value: 'Liters', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="avg" stroke="#1976d2" name="Average (L/day)" />
            <Line type="monotone" dataKey="min" stroke="#90caf9" name="Min (L/day)" strokeDasharray="5 5" />
            <Line type="monotone" dataKey="max" stroke="#42a5f5" name="Max (L/day)" strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell align="right">Average (L/day)</TableCell>
              <TableCell align="right">Min (L/day)</TableCell>
              <TableCell align="right">Max (L/day)</TableCell>
              <TableCell align="right">Data Points</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {waterHistory.water_history.map((entry: any) => (
              <TableRow key={entry.date}>
                <TableCell>{dayjs(entry.date).format('MMM DD, YYYY')}</TableCell>
                <TableCell align="right">{entry.consumption_avg.toFixed(2)}</TableCell>
                <TableCell align="right">{entry.consumption_min?.toFixed(2) || 'N/A'}</TableCell>
                <TableCell align="right">{entry.consumption_max?.toFixed(2) || 'N/A'}</TableCell>
                <TableCell align="right">{entry.data_points}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default HouseWaterHistoryTab;

