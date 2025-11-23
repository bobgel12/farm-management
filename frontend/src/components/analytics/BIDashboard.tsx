import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Alert,
  Button,
  Chip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Remove as RemoveIcon,
  Analytics as AnalyticsIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useAnalytics } from '../../contexts/AnalyticsContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import { KPI, Dashboard } from '../../types';

const BIDashboard: React.FC = () => {
  const {
    dashboards,
    kpis,
    loading,
    error,
    fetchDashboards,
    fetchKPIs,
  } = useAnalytics();
  const { currentOrganization } = useOrganization();

  const [selectedDashboard, setSelectedDashboard] = useState<Dashboard | null>(null);

  useEffect(() => {
    if (currentOrganization) {
      fetchDashboards(currentOrganization.id);
      fetchKPIs(currentOrganization.id);
    }
  }, [currentOrganization, fetchDashboards, fetchKPIs]);

  if (loading && dashboards.length === 0 && kpis.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading analytics...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
            Business Intelligence Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Executive insights and key performance indicators
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {/* Navigate to create dashboard */}}
          sx={{ borderRadius: 2 }}
        >
          New Dashboard
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* KPI Cards */}
      {kpis.length > 0 && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {kpis.slice(0, 4).map((kpi) => (
            <Grid item xs={12} sm={6} md={3} key={kpi.id}>
              <KPICard kpi={kpi} />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Dashboard Placeholder */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 8 }}>
            <AnalyticsIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Executive Dashboard
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3, textAlign: 'center' }}>
              Create custom dashboards with KPIs, charts, and analytics
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {/* Navigate to create dashboard */}}
            >
              Create Dashboard
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Dashboards List */}
      {dashboards.length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Available Dashboards
          </Typography>
          <Grid container spacing={2}>
            {dashboards.map((dashboard) => (
              <Grid item xs={12} sm={6} md={4} key={dashboard.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => setSelectedDashboard(dashboard)}
                >
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {dashboard.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {dashboard.description || 'No description'}
                    </Typography>
                    <Chip
                      label={dashboard.dashboard_type}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
    </Box>
  );
};

interface KPICardProps {
  kpi: KPI;
}

const KPICard: React.FC<KPICardProps> = ({ kpi }) => {
  const [value, setValue] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const { calculateKPI } = useAnalytics();

  useEffect(() => {
    const fetchKPIValue = async () => {
      try {
        setLoading(true);
        const result = await calculateKPI(kpi.id);
        setValue(result.value);
      } catch (err) {
        console.error('Error calculating KPI:', err);
      } finally {
        setLoading(false);
      }
    };

    if (kpi.id) {
      fetchKPIValue();
    }
  }, [kpi.id, calculateKPI]);

  return (
    <Card>
      <CardContent>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {kpi.name}
        </Typography>
        {loading ? (
          <LinearProgress sx={{ mt: 1 }} />
        ) : (
          <Typography variant="h4" sx={{ fontWeight: 600, my: 1 }}>
            {value !== null ? `${value.toFixed(2)} ${kpi.unit || ''}` : 'N/A'}
          </Typography>
        )}
        {kpi.target_value && value !== null && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
            {value >= kpi.target_value ? (
              <TrendingUpIcon sx={{ fontSize: 16, color: 'success.main' }} />
            ) : (
              <TrendingDownIcon sx={{ fontSize: 16, color: 'error.main' }} />
            )}
            <Typography variant="caption" color="text.secondary">
              Target: {kpi.target_value} {kpi.unit || ''}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default BIDashboard;

