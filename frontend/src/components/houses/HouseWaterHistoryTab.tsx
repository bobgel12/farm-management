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
  Button,
  Snackbar,
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { House } from '../../types';
import { rotemApi } from '../../services/rotemApi';
import { useFarm } from '../../contexts/FarmContext';
import { Search as SearchIcon, CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import dayjs from 'dayjs';

interface HouseWaterHistoryTabProps {
  houseId: string;
  house: House & { 
    farm?: { 
      is_integrated?: boolean;
      has_system_integration?: boolean;
      integration_type?: 'none' | 'rotem' | 'future_system';
      rotem_farm_id?: string;
    };
    farm_id?: number;
  };
}

export const HouseWaterHistoryTab: React.FC<HouseWaterHistoryTabProps> = ({ houseId, house }) => {
  const { farms } = useFarm();
  const [waterHistory, setWaterHistory] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [daysFilter, setDaysFilter] = useState<number>(30);
  const [detecting, setDetecting] = useState(false);
  const [detectionSuccess, setDetectionSuccess] = useState<string | null>(null);
  const [detectionError, setDetectionError] = useState<string | null>(null);
  const [detectionResults, setDetectionResults] = useState<{
    houses_checked?: number;
    alerts_created?: number;
    emails_sent?: number;
  } | null>(null);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isRequestInFlightRef = useRef<boolean>(false);

  // Get farm info to check if it's integrated with Rotem
  // Use the same permissive check as HouseDetailPage to ensure consistency
  const farm = house.farm_id ? farms.find(f => f.id === house.farm_id) : null;
  const farmData = (house.farm || farm) as any;
  
  // Calculate isIntegrated for UI (button disabled state, etc.)
  // Simple check: Show tab if integration_type is 'rotem' (regardless of status or other flags)
  // Also check rotem_farm_id as a fallback indicator that Rotem is configured
  // And check house-level is_integrated flag as additional fallback
  const isIntegrated = (
    (farmData && (
      farmData.integration_type === 'rotem' || 
      (farmData.rotem_farm_id && String(farmData.rotem_farm_id).trim() !== '')
    )) ||
    house.is_integrated === true
  );
  
  // Debug logging (remove in production if needed)
  if (process.env.NODE_ENV === 'development') {
    console.log('HouseWaterHistoryTab integration check:', {
      houseId,
      farmData: farmData ? { 
        id: farmData.id, 
        name: farmData.name,
        integration_type: farmData.integration_type,
        has_system_integration: farmData.has_system_integration,
        is_integrated: farmData.is_integrated,
        rotem_farm_id: farmData.rotem_farm_id
      } : null,
      houseIsIntegrated: house.is_integrated,
      isIntegrated
    });
  }

  const loadWaterHistory = useCallback(async () => {
    // Prevent duplicate concurrent requests
    if (isRequestInFlightRef.current) {
      return;
    }

    // Recheck integration status with latest data (recalculate to ensure we have latest)
    const currentFarm = house.farm_id ? farms.find(f => f.id === house.farm_id) : null;
    const currentFarmData = (house.farm || currentFarm) as any;
    
    // More permissive check - if any indicator suggests Rotem integration, allow it
    const isIntegratedNow = (
      // Check farm integration_type
      (currentFarmData && currentFarmData.integration_type === 'rotem') ||
      // Check rotem_farm_id
      (currentFarmData && currentFarmData.rotem_farm_id && String(currentFarmData.rotem_farm_id).trim() !== '') ||
      // Check farm is_integrated flag
      (currentFarmData && currentFarmData.is_integrated === true) ||
      // Check house is_integrated flag
      house.is_integrated === true
    );
    
    // Log for debugging (including production)
    console.log('HouseWaterHistoryTab - Integration check:', {
      houseId,
      houseFarmId: house.farm_id,
      houseIsIntegrated: house.is_integrated,
      farmDataExists: !!currentFarmData,
      farmIntegrationType: currentFarmData?.integration_type,
      farmIsIntegrated: currentFarmData?.is_integrated,
      farmRotemFarmId: currentFarmData?.rotem_farm_id,
      isIntegratedNow
    });
    
    if (!isIntegratedNow) {
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
  }, [houseId, daysFilter, house.farm, house.farm_id, house.is_integrated, farms]);

  useEffect(() => {
    loadWaterHistory();
  }, [loadWaterHistory]);

  const handleTriggerDetection = async () => {
    setDetecting(true);
    setDetectionError(null);
    setDetectionSuccess(null);
    setDetectionResults(null);
    setCurrentTaskId(null);

    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    try {
      const result = await rotemApi.triggerWaterAnomalyDetection(
        parseInt(houseId),
        house.farm_id
      );
      
      // Check if task ran synchronously (no task_id means it completed immediately)
      if (result.execution_mode === 'synchronous' || result.execution_mode === 'synchronous_fallback' || !result.task_id) {
        // Task completed synchronously
        setDetecting(false);
        if (result.result) {
          setDetectionResults({
            houses_checked: result.result.houses_checked,
            alerts_created: result.result.alerts_created,
            emails_sent: result.result.emails_sent,
          });
          
          const resultMessage = result.warning 
            ? `${result.message} ${result.warning}`
            : result.message;
          setDetectionSuccess(resultMessage);
        } else {
          setDetectionSuccess(result.message || 'Detection completed');
        }
      } else {
        // Task is running asynchronously, start polling
        setCurrentTaskId(result.task_id);
        setDetectionSuccess('Water consumption anomaly detection started. Checking status...');
        
        // Start polling for task status
        startPollingTaskStatus(result.task_id);
      }
    } catch (err: any) {
      setDetectionError(
        err.response?.data?.error || 'Failed to trigger anomaly detection'
      );
      setDetecting(false);
    }
  };

  const startPollingTaskStatus = (taskId: string) => {
    let pollCount = 0;
    const maxPolls = 60; // Maximum 60 polls (2 minutes total)
    
    // Poll every 2 seconds
    pollingIntervalRef.current = setInterval(async () => {
      pollCount++;
      
      // Timeout after max polls
      if (pollCount > maxPolls) {
        clearInterval(pollingIntervalRef.current!);
        pollingIntervalRef.current = null;
        setDetecting(false);
        setDetectionError('Detection is taking longer than expected. Please check back later or check your email for alerts.');
        setCurrentTaskId(null);
        return;
      }
      
      try {
        const status = await rotemApi.checkWaterAnomalyDetectionStatus(taskId);
        
        if (status.state === 'SUCCESS') {
          // Task completed successfully
          clearInterval(pollingIntervalRef.current!);
          pollingIntervalRef.current = null;
          setDetecting(false);
          setDetectionResults({
            houses_checked: status.houses_checked,
            alerts_created: status.alerts_created,
            emails_sent: status.emails_sent,
          });
          
          const resultMessage = `Detection completed! Checked ${status.houses_checked || 0} house(s), created ${status.alerts_created || 0} alert(s), and sent ${status.emails_sent || 0} email(s).`;
          setDetectionSuccess(resultMessage);
          setCurrentTaskId(null);
        } else if (status.state === 'FAILURE') {
          // Task failed
          clearInterval(pollingIntervalRef.current!);
          pollingIntervalRef.current = null;
          setDetecting(false);
          setDetectionError(
            status.error || 'Anomaly detection task failed'
          );
          setCurrentTaskId(null);
        } else if (status.state === 'PENDING' || status.state === 'PROGRESS') {
          // Task still running, continue polling
          setDetectionSuccess(status.message || 'Detection in progress...');
        }
      } catch (err: any) {
        // Error checking status - stop polling after a few failures
        if (pollCount > 5) {
          clearInterval(pollingIntervalRef.current!);
          pollingIntervalRef.current = null;
          setDetecting(false);
          setDetectionError('Failed to check detection status. The task may still be running in the background.');
          setCurrentTaskId(null);
        }
        console.error('Error checking task status:', err);
      }
    }, 2000); // Poll every 2 seconds
  };

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

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
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Button
            variant="outlined"
            color="primary"
            startIcon={detecting ? <CircularProgress size={16} /> : <SearchIcon />}
            onClick={handleTriggerDetection}
            disabled={detecting || !isIntegrated}
            sx={{ minWidth: 200 }}
          >
            {detecting 
              ? (detectionSuccess && detectionSuccess.includes('in progress') 
                  ? 'Detecting...' 
                  : 'Processing...')
              : 'Detect Anomalies'}
          </Button>
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
      </Box>

      {/* Detection Results Card */}
      {detectionResults && (
        <Card sx={{ mb: 3, bgcolor: 'success.light', color: 'success.contrastText' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Detection Results
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Typography variant="body2">Houses Checked</Typography>
                <Typography variant="h5">{detectionResults.houses_checked || 0}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="body2">Alerts Created</Typography>
                <Typography variant="h5">{detectionResults.alerts_created || 0}</Typography>
              </Grid>
              <Grid item xs={4}>
                <Typography variant="body2">Emails Sent</Typography>
                <Typography variant="h5">{detectionResults.emails_sent || 0}</Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Success/Error Snackbars */}
      <Snackbar
        open={!!detectionSuccess}
        autoHideDuration={detectionResults ? 10000 : 6000}
        onClose={() => setDetectionSuccess(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setDetectionSuccess(null)}
          severity="success"
          icon={<CheckCircle />}
          sx={{ width: '100%' }}
        >
          {detectionSuccess}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!detectionError}
        autoHideDuration={6000}
        onClose={() => setDetectionError(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setDetectionError(null)}
          severity="error"
          icon={<ErrorIcon />}
          sx={{ width: '100%' }}
        >
          {detectionError}
        </Alert>
      </Snackbar>

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

