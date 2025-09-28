import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  Chip,
  LinearProgress,
  Tooltip,
  Paper,
} from '@mui/material';
import {
  Thermostat,
  Water,
  Air,
  Speed,
  Feed,
  Visibility,
  Warning,
  CheckCircle,
} from '@mui/icons-material';
import { HouseSensorData } from '../../types/rotem';

interface RealTimeSensorCardProps {
  houseData: HouseSensorData;
  isLoading?: boolean;
}

const RealTimeSensorCard: React.FC<RealTimeSensorCardProps> = ({ 
  houseData, 
  isLoading = false 
}) => {
  const getTemperatureColor = (temp: number, target: number) => {
    const diff = Math.abs(temp - target);
    if (diff <= 1) return 'success';
    if (diff <= 3) return 'warning';
    return 'error';
  };

  const getHumidityColor = (humidity: number) => {
    if (humidity >= 50 && humidity <= 70) return 'success';
    if (humidity >= 40 && humidity <= 80) return 'warning';
    return 'error';
  };

  const getConnectionStatus = (status: number) => {
    return status === 1 ? 'Connected' : 'Disconnected';
  };

  const getConnectionColor = (status: number) => {
    return status === 1 ? 'success' : 'error';
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            House {houseData.house_number} - Loading...
          </Typography>
          <LinearProgress />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" component="h2">
            House {houseData.house_number}
          </Typography>
          <Chip
            label={getConnectionStatus(houseData.connection_status)}
            color={getConnectionColor(houseData.connection_status) as any}
            size="small"
            icon={houseData.connection_status === 1 ? <CheckCircle /> : <Warning />}
          />
        </Box>

        <Grid container spacing={2}>
          {/* Temperature Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box display="flex" alignItems="center" mb={1}>
                <Thermostat color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold">
                  Temperature
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h4" color={getTemperatureColor(houseData.temperature, houseData.target_temperature)}>
                  {houseData.temperature.toFixed(1)}°C
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Target: {houseData.target_temperature.toFixed(1)}°C
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Outside: {houseData.outside_temperature.toFixed(1)}°C
              </Typography>
            </Paper>
          </Grid>

          {/* Humidity Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box display="flex" alignItems="center" mb={1}>
                <Water color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold">
                  Humidity
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h4" color={getHumidityColor(houseData.humidity)}>
                  {houseData.humidity.toFixed(0)}%
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={houseData.humidity}
                  color={getHumidityColor(houseData.humidity) as any}
                  sx={{ width: 100, height: 8, borderRadius: 4 }}
                />
              </Box>
            </Paper>
          </Grid>

          {/* Ventilation Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box display="flex" alignItems="center" mb={1}>
                <Air color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold">
                  Ventilation
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h5">
                  {houseData.ventilation_level}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {houseData.airflow_cfm.toLocaleString()} CFM
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Airflow: {houseData.airflow_percentage}%
              </Typography>
            </Paper>
          </Grid>

          {/* Pressure Section */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box display="flex" alignItems="center" mb={1}>
                <Speed color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold">
                  Pressure
                </Typography>
              </Box>
              <Typography variant="h5">
                {houseData.pressure.toFixed(1)} hPa
              </Typography>
            </Paper>
          </Grid>

          {/* Feed Consumption */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box display="flex" alignItems="center" mb={1}>
                <Feed color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold">
                  Feed Consumption
                </Typography>
              </Box>
              <Typography variant="h5">
                {houseData.feed_consumption.toFixed(0)} kg
              </Typography>
            </Paper>
          </Grid>

          {/* Water Consumption */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box display="flex" alignItems="center" mb={1}>
                <Water color="info" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold">
                  Water Consumption
                </Typography>
              </Box>
              <Typography variant="h5">
                {houseData.water_consumption.toFixed(1)} L/day
              </Typography>
            </Paper>
          </Grid>

          {/* Bird Count */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Box display="flex" alignItems="center" mb={1}>
                <Visibility color="primary" sx={{ mr: 1 }} />
                <Typography variant="subtitle2" fontWeight="bold">
                  Birds
                </Typography>
              </Box>
              <Typography variant="h5">
                {houseData.bird_count.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Livability: {houseData.livability.toFixed(1)}%
              </Typography>
            </Paper>
          </Grid>

          {/* Growth Day */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                Growth Day: {houseData.growth_day}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Day {houseData.growth_day} of growth cycle
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default RealTimeSensorCard;
