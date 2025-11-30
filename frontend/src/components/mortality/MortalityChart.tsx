import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  ToggleButton,
  ToggleButtonGroup,
  useTheme,
} from '@mui/material';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { MortalityTrend, MortalitySummary } from '../../types';
import { mortalityApi } from '../../services/mortalityApi';

interface MortalityChartProps {
  flockId?: number;
  houseId?: number;
  days?: number;
  refresh?: number;
}

type ChartType = 'line' | 'bar' | 'pie';

const COLORS = {
  disease: '#f44336',
  culling: '#2196f3',
  accident: '#ff9800',
  heat_stress: '#e91e63',
  cold_stress: '#00bcd4',
  unknown: '#9e9e9e',
  other: '#607d8b',
  total: '#d32f2f',
};

export const MortalityChart: React.FC<MortalityChartProps> = ({
  flockId,
  houseId,
  days = 30,
  refresh = 0,
}) => {
  const theme = useTheme();
  const [trendData, setTrendData] = useState<MortalityTrend[]>([]);
  const [summary, setSummary] = useState<MortalitySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chartType, setChartType] = useState<ChartType>('line');

  useEffect(() => {
    loadData();
  }, [flockId, houseId, days, refresh]);

  const loadData = async () => {
    if (!flockId && !houseId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const params: { flock_id?: number; house_id?: number; days: number } = { days };
      if (flockId) params.flock_id = flockId;
      if (houseId) params.house_id = houseId;

      const trendsResponse = await mortalityApi.getTrends(params);
      setTrendData(trendsResponse.data);

      if (flockId) {
        const summaryResponse = await mortalityApi.getSummary(flockId);
        setSummary(summaryResponse);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load chart data');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const pieData = summary
    ? [
        { name: 'Disease', value: summary.disease_total, color: COLORS.disease },
        { name: 'Culling', value: summary.culling_total, color: COLORS.culling },
        { name: 'Accident', value: summary.accident_total, color: COLORS.accident },
        { name: 'Heat Stress', value: summary.heat_stress_total, color: COLORS.heat_stress },
        { name: 'Cold Stress', value: summary.cold_stress_total, color: COLORS.cold_stress },
        { name: 'Unknown', value: summary.unknown_total, color: COLORS.unknown },
        { name: 'Other', value: summary.other_total, color: COLORS.other },
      ].filter(d => d.value > 0)
    : [];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (trendData.length === 0 && !summary) {
    return (
      <Card>
        <CardContent>
          <Typography color="text.secondary" align="center">
            No mortality data to display
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">📈 Mortality Trends</Typography>
          <ToggleButtonGroup
            value={chartType}
            exclusive
            onChange={(_, value) => value && setChartType(value)}
            size="small"
          >
            <ToggleButton value="line">Line</ToggleButton>
            <ToggleButton value="bar">Bar</ToggleButton>
            {summary && pieData.length > 0 && (
              <ToggleButton value="pie">Pie</ToggleButton>
            )}
          </ToggleButtonGroup>
        </Box>

        {chartType === 'line' && trendData.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDate} />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => formatDate(value as string)}
                contentStyle={{
                  backgroundColor: theme.palette.background.paper,
                  border: `1px solid ${theme.palette.divider}`,
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="total_deaths"
                name="Total Deaths"
                stroke={COLORS.total}
                strokeWidth={2}
                dot={{ fill: COLORS.total }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}

        {chartType === 'bar' && trendData.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={formatDate} />
              <YAxis />
              <Tooltip
                labelFormatter={(value) => formatDate(value as string)}
                contentStyle={{
                  backgroundColor: theme.palette.background.paper,
                  border: `1px solid ${theme.palette.divider}`,
                }}
              />
              <Legend />
              <Bar dataKey="disease" name="Disease" stackId="a" fill={COLORS.disease} />
              <Bar dataKey="culling" name="Culling" stackId="a" fill={COLORS.culling} />
              <Bar dataKey="accident" name="Accident" stackId="a" fill={COLORS.accident} />
              <Bar dataKey="heat_stress" name="Heat Stress" stackId="a" fill={COLORS.heat_stress} />
              <Bar dataKey="cold_stress" name="Cold Stress" stackId="a" fill={COLORS.cold_stress} />
              <Bar dataKey="unknown" name="Unknown" stackId="a" fill={COLORS.unknown} />
              <Bar dataKey="other" name="Other" stackId="a" fill={COLORS.other} />
            </BarChart>
          </ResponsiveContainer>
        )}

        {chartType === 'pie' && pieData.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={2}
                dataKey="value"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}

        {summary && (
          <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
            <Box sx={{ textAlign: 'center', px: 2 }}>
              <Typography variant="h4" color="error.main">
                {summary.total_mortality}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Deaths
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center', px: 2 }}>
              <Typography variant="h4" color="warning.main">
                {summary.mortality_rate.toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Mortality Rate
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center', px: 2 }}>
              <Typography variant="h4" color="success.main">
                {summary.livability.toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Livability
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center', px: 2 }}>
              <Typography variant="h4">
                {summary.daily_average}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Daily Average
              </Typography>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default MortalityChart;

