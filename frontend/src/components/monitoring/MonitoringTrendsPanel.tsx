import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from '@mui/material';
import monitoringApi from '../../services/monitoringApi';
import { MonitoringTrendsResponse } from '../../types/monitoring';

interface Props {
  houseId: number;
  growthDay?: number | null;
}

const MonitoringTrendsPanel: React.FC<Props> = ({ houseId, growthDay }) => {
  const [data, setData] = useState<MonitoringTrendsResponse | null>(null);
  const [period, setPeriod] = useState(14);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const result = await monitoringApi.getHouseMonitoringTrends(
          houseId,
          period,
          growthDay ?? undefined
        );
        if (!cancelled) setData(result);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [houseId, period, growthDay]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={2}>
        <CircularProgress size={28} />
      </Box>
    );
  }

  if (!data || data.current_series.length === 0) {
    return (
      <Alert severity="info">
        Trend data will appear after daily summaries are collected (run backfill or wait for nightly job).
      </Alert>
    );
  }

  const latest = data.current_series[data.current_series.length - 1];

  return (
    <Card variant="outlined">
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">14-day trends (House {data.house_number})</Typography>
          <FormControl size="small" sx={{ minWidth: 100 }}>
            <InputLabel>Days</InputLabel>
            <Select value={period} label="Days" onChange={(e) => setPeriod(Number(e.target.value))}>
              <MenuItem value={7}>7</MenuItem>
              <MenuItem value={14}>14</MenuItem>
              <MenuItem value={30}>30</MenuItem>
            </Select>
          </FormControl>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Latest: water {latest.water_consumption_avg?.toFixed(0) ?? '—'} L · feed{' '}
          {latest.feed_consumption_avg?.toFixed(0) ?? '—'} kg · temp{' '}
          {latest.temperature_avg?.toFixed(1) ?? '—'}°C
        </Typography>
        {data.comparison_series.length > 0 && (
          <Typography variant="caption" display="block" sx={{ mt: 1 }}>
            Comparison at growth day {data.comparison_growth_day}:{' '}
            {data.comparison_series.length} prior flock day(s) on record
          </Typography>
        )}
        <Box component="ul" sx={{ mt: 2, pl: 2 }}>
          {data.current_series.slice(-5).map((row) => (
            <Typography component="li" variant="body2" key={row.id}>
              {row.date}: water {row.water_consumption_avg?.toFixed(0) ?? '—'} · feed{' '}
              {row.feed_consumption_avg?.toFixed(0) ?? '—'}
            </Typography>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default MonitoringTrendsPanel;
