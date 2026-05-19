import React, { useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  LinearProgress,
  Typography,
} from '@mui/material';
import monitoringApi from '../../services/monitoringApi';
import { FarmDataQualityResponse } from '../../types/monitoring';

interface Props {
  farmId: number;
  days?: number;
}

const MonitoringDataQualityPanel: React.FC<Props> = ({ farmId, days = 1 }) => {
  const [data, setData] = useState<FarmDataQualityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const result = await monitoringApi.getFarmDataQuality(farmId, days);
        if (!cancelled) setData(result);
      } catch (e) {
        if (!cancelled) setError('Failed to load data quality metrics');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [farmId, days]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={2}>
        <CircularProgress size={28} />
      </Box>
    );
  }

  if (error || !data) {
    return <Alert severity="warning">{error ?? 'No data quality metrics'}</Alert>;
  }

  return (
    <Card variant="outlined">
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Data collection quality</Typography>
          <Chip
            label={data.meets_target ? 'On target (≥95%)' : 'Below target'}
            color={data.meets_target ? 'success' : 'warning'}
            size="small"
          />
        </Box>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Farm avg completeness: {data.avg_completeness_percent}% · Stale houses: {data.stale_house_count}
        </Typography>
        {data.houses.map((h) => (
          <Box key={h.house_id} sx={{ mt: 2 }}>
            <Box display="flex" justifyContent="space-between" mb={0.5}>
              <Typography variant="subtitle2">House {h.house_number}</Typography>
              <Typography variant="caption" color={h.is_stale ? 'error' : 'text.secondary'}>
                {h.completeness_percent}% · {h.snapshot_count}/{h.expected_snapshots} snapshots
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={Math.min(100, h.completeness_percent)}
              color={h.meets_target ? 'success' : 'warning'}
            />
          </Box>
        ))}
      </CardContent>
    </Card>
  );
};

export default MonitoringDataQualityPanel;
