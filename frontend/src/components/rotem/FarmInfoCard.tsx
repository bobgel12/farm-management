import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  Divider,
} from '@mui/material';
import {
  Storage,
  Person,
  Schedule,
  TrendingUp,
} from '@mui/icons-material';
import { RotemFarm, FarmDataSummary } from '../../types/rotem';

interface FarmInfoCardProps {
  farm: RotemFarm;
  summary: FarmDataSummary;
}

const FarmInfoCard: React.FC<FarmInfoCardProps> = ({ farm, summary }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getDataHealthColor = (recent: number, total: number) => {
    if (total === 0) return 'default';
    const ratio = recent / total;
    if (ratio > 0.1) return 'success';
    if (ratio > 0.05) return 'warning';
    return 'error';
  };

  const getDataHealthText = (recent: number, total: number) => {
    if (total === 0) return 'No Data';
    const ratio = recent / total;
    if (ratio > 0.1) return 'Excellent';
    if (ratio > 0.05) return 'Good';
    return 'Poor';
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Farm Information
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Storage sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="textSecondary">
                Farm Name
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {farm.farm_name}
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Person sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="textSecondary">
                Gateway
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {farm.gateway_name}
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Schedule sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="textSecondary">
                Created
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {formatDate(farm.created_at)}
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <TrendingUp sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="textSecondary">
                Data Health
              </Typography>
            </Box>
            <Chip
              label={getDataHealthText(summary.recent_data_points, summary.total_data_points)}
              color={getDataHealthColor(summary.recent_data_points, summary.total_data_points)}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Storage sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="textSecondary">
                Status
              </Typography>
            </Box>
            <Chip
              label={farm.is_active ? 'Active' : 'Inactive'}
              color={farm.is_active ? 'success' : 'default'}
              sx={{ mb: 2 }}
            />

            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Person sx={{ mr: 1, color: 'text.secondary' }} />
              <Typography variant="body2" color="textSecondary">
                Username
              </Typography>
            </Box>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {farm.rotem_username}
            </Typography>
          </Grid>
        </Grid>

        <Divider sx={{ my: 2 }} />

        {/* Data Statistics */}
        <Typography variant="subtitle2" gutterBottom>
          Data Statistics
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {summary.total_data_points.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Total Data Points
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={6}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="secondary">
                {summary.recent_data_points.toLocaleString()}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                Recent (24h)
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default FarmInfoCard;
