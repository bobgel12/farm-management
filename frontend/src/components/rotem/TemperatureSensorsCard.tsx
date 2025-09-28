import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  Paper,
  Chip,
} from '@mui/material';
import { Thermostat } from '@mui/icons-material';
import { HouseSensorData } from '../../types/rotem';

interface TemperatureSensorsCardProps {
  houseData: HouseSensorData;
}

const TemperatureSensorsCard: React.FC<TemperatureSensorsCardProps> = ({ houseData }) => {
  const sensors = [
    { key: 'sensor_1', label: 'Sensor 1' },
    { key: 'sensor_2', label: 'Sensor 2' },
    { key: 'sensor_3', label: 'Sensor 3' },
    { key: 'sensor_4', label: 'Sensor 4' },
    { key: 'sensor_5', label: 'Sensor 5' },
    { key: 'sensor_6', label: 'Sensor 6' },
    { key: 'sensor_7', label: 'Sensor 7' },
    { key: 'sensor_8', label: 'Sensor 8' },
    { key: 'sensor_9', label: 'Sensor 9' },
  ];

  const getTemperatureColor = (temp: number, target: number) => {
    const diff = Math.abs(temp - target);
    if (diff <= 1) return 'success';
    if (diff <= 3) return 'warning';
    return 'error';
  };

  const getTemperatureVariant = (temp: number, target: number) => {
    const diff = Math.abs(temp - target);
    if (diff <= 1) return 'filled';
    if (diff <= 3) return 'outlined';
    return 'outlined';
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <Thermostat color="primary" sx={{ mr: 1 }} />
          <Typography variant="h6" component="h2">
            Temperature Sensors - House {houseData.house_number}
          </Typography>
        </Box>

        <Grid container spacing={2}>
          {/* Main Temperature Readings */}
          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Average Temperature
              </Typography>
              <Typography variant="h4" color={getTemperatureColor(houseData.temperature, houseData.target_temperature)}>
                {houseData.temperature.toFixed(1)}°C
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Tunnel Temperature
              </Typography>
              <Typography variant="h4" color={getTemperatureColor(houseData.tunnel_temperature, houseData.target_temperature)}>
                {houseData.tunnel_temperature.toFixed(1)}°C
              </Typography>
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Wind Chill
              </Typography>
              <Typography variant="h4" color={getTemperatureColor(houseData.wind_chill_temperature, houseData.target_temperature)}>
                {houseData.wind_chill_temperature.toFixed(1)}°C
              </Typography>
            </Paper>
          </Grid>

          {/* Individual Sensors */}
          {sensors.map((sensor) => {
            const temp = houseData.temperature_sensors[sensor.key as keyof typeof houseData.temperature_sensors];
            return (
              <Grid item xs={6} sm={4} md={3} key={sensor.key}>
                <Paper sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    {sensor.label}
                  </Typography>
                  <Chip
                    label={`${temp.toFixed(1)}°C`}
                    color={getTemperatureColor(temp, houseData.target_temperature) as any}
                    variant={getTemperatureVariant(temp, houseData.target_temperature) as any}
                    size="small"
                  />
                </Paper>
              </Grid>
            );
          })}
        </Grid>

        {/* Wind Information */}
        <Box mt={3}>
          <Typography variant="subtitle2" gutterBottom>
            Wind Conditions
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Wind Speed
                </Typography>
                <Typography variant="h6">
                  {houseData.wind_speed.toFixed(1)} mph
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={6}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Wind Direction
                </Typography>
                <Typography variant="h6">
                  {houseData.wind_direction}°
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  );
};

export default TemperatureSensorsCard;
