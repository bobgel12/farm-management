import React, { useMemo } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Grid,
  Paper,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { RotemDataPoint, SensorChartData } from '../../types/rotem';

interface SensorDataChartProps {
  data: RotemDataPoint[];
  title?: string;
  height?: number;
}

const SensorDataChart: React.FC<SensorDataChartProps> = ({ 
  data, 
  title = "Sensor Data",
  height = 300 
}) => {
  const [selectedDataType, setSelectedDataType] = React.useState<string>('');

  // Get available data types
  const dataTypes = useMemo(() => {
    return Array.from(new Set(data.map(point => point.data_type)));
  }, [data]);

  // Set default data type
  React.useEffect(() => {
    if (dataTypes.length > 0 && !selectedDataType) {
      setSelectedDataType(dataTypes[0]);
    }
  }, [dataTypes, selectedDataType]);

  // Process chart data
  const chartData = useMemo(() => {
    if (!selectedDataType) return [];

    return data
      .filter(point => point.data_type === selectedDataType)
      .map(point => ({
        timestamp: new Date(point.timestamp).getTime(),
        value: point.value,
        unit: point.unit,
        quality: point.quality,
      }))
      .sort((a, b) => a.timestamp - b.timestamp)
      .slice(-50); // Show last 50 points
  }, [data, selectedDataType]);

  // Get current value and unit
  const currentValue = useMemo(() => {
    if (chartData.length === 0) return null;
    return chartData[chartData.length - 1];
  }, [chartData]);

  // Get average value
  const averageValue = useMemo(() => {
    if (chartData.length === 0) return null;
    const sum = chartData.reduce((acc, point) => acc + point.value, 0);
    return sum / chartData.length;
  }, [chartData]);

  // Get min/max values
  const minValue = useMemo(() => {
    if (chartData.length === 0) return null;
    return Math.min(...chartData.map(point => point.value));
  }, [chartData]);

  const maxValue = useMemo(() => {
    if (chartData.length === 0) return null;
    return Math.max(...chartData.map(point => point.value));
  }, [chartData]);

  // Format timestamp for display
  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Get optimal range for the data type
  const getOptimalRange = (dataType: string) => {
    switch (dataType) {
      case 'temperature':
        return { min: 20, max: 25, unit: '°C' };
      case 'humidity':
        return { min: 50, max: 70, unit: '%' };
      case 'air_pressure':
        return { min: 1010, max: 1020, unit: 'hPa' };
      case 'wind_speed':
        return { min: 0.5, max: 2.0, unit: 'm/s' };
      case 'water_consumption':
        return { min: 100, max: 200, unit: 'L/h' };
      case 'feed_consumption':
        return { min: 50, max: 100, unit: 'kg/h' };
      default:
        return null;
    }
  };

  const optimalRange = getOptimalRange(selectedDataType);

  if (data.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography color="textSecondary">
              No sensor data available
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Data Type</InputLabel>
            <Select
              value={selectedDataType}
              onChange={(e) => setSelectedDataType(e.target.value)}
              label="Data Type"
            >
              {dataTypes.map((type) => (
                <MenuItem key={type} value={type}>
                  {type.replace('_', ' ').toUpperCase()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {currentValue && (
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6} sm={3}>
              <Paper sx={{ p: 1, textAlign: 'center' }}>
                <Typography variant="caption" color="textSecondary">
                  Current
                </Typography>
                <Typography variant="h6">
                  {currentValue.value.toFixed(1)} {currentValue.unit}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Paper sx={{ p: 1, textAlign: 'center' }}>
                <Typography variant="caption" color="textSecondary">
                  Average
                </Typography>
                <Typography variant="h6">
                  {averageValue?.toFixed(1)} {currentValue.unit}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Paper sx={{ p: 1, textAlign: 'center' }}>
                <Typography variant="caption" color="textSecondary">
                  Min
                </Typography>
                <Typography variant="h6">
                  {minValue?.toFixed(1)} {currentValue.unit}
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Paper sx={{ p: 1, textAlign: 'center' }}>
                <Typography variant="caption" color="textSecondary">
                  Max
                </Typography>
                <Typography variant="h6">
                  {maxValue?.toFixed(1)} {currentValue.unit}
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        )}

        {optimalRange && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="textSecondary">
              Optimal Range: {optimalRange.min}-{optimalRange.max} {optimalRange.unit}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
              <Chip
                label={`Min: ${optimalRange.min}${optimalRange.unit}`}
                size="small"
                color="info"
                variant="outlined"
              />
              <Chip
                label={`Max: ${optimalRange.max}${optimalRange.unit}`}
                size="small"
                color="info"
                variant="outlined"
              />
            </Box>
          </Box>
        )}

        <Box sx={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatTimestamp}
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => new Date(value).toLocaleString()}
                formatter={(value: number, name: string) => [
                  `${value.toFixed(2)} ${currentValue?.unit || ''}`,
                  selectedDataType?.replace('_', ' ').toUpperCase() || ''
                ]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#1976d2"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              {optimalRange && (
                <>
                  <ReferenceLine
                    y={optimalRange.min}
                    stroke="#4caf50"
                    strokeDasharray="5 5"
                    label={{ value: `Min (${optimalRange.min}${optimalRange.unit})`, position: "top" }}
                  />
                  <ReferenceLine
                    y={optimalRange.max}
                    stroke="#4caf50"
                    strokeDasharray="5 5"
                    label={{ value: `Max (${optimalRange.max}${optimalRange.unit})`, position: "top" }}
                  />
                </>
              )}
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
};

export default SensorDataChart;
