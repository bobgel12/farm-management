import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
} from '@mui/material';
import {
  Storage,
} from '@mui/icons-material';
import { FarmDataSummary } from '../../types/rotem';

interface DataSummaryCardProps {
  summary: FarmDataSummary[];
}

const DataSummaryCard: React.FC<DataSummaryCardProps> = ({ summary }) => {
  const totalDataPoints = summary.reduce((sum, farm) => sum + farm.total_data_points, 0);
  const recentDataPoints = summary.reduce((sum, farm) => sum + farm.recent_data_points, 0);
  const totalControllers = summary.reduce((sum, farm) => sum + farm.controllers, 0);

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
        <Typography variant="h6" component="h2" gutterBottom>
          Data Summary
        </Typography>
        <Divider sx={{ mb: 2 }} />

        {/* Overall Stats */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" color="textSecondary">
              Total Data Points
            </Typography>
            <Typography variant="h6">
              {totalDataPoints.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="body2" color="textSecondary">
              Recent (24h)
            </Typography>
            <Typography variant="h6">
              {recentDataPoints.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="body2" color="textSecondary">
              Controllers
            </Typography>
            <Typography variant="h6">
              {totalControllers}
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="textSecondary">
              Data Health
            </Typography>
            <Chip
              label={getDataHealthText(recentDataPoints, totalDataPoints)}
              color={getDataHealthColor(recentDataPoints, totalDataPoints)}
              size="small"
            />
          </Box>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Farm Breakdown */}
        <Typography variant="subtitle2" gutterBottom>
          By Farm
        </Typography>
        <List dense>
          {summary.map((farm) => (
            <ListItem key={farm.farm_id} sx={{ px: 0 }}>
              <ListItemIcon sx={{ minWidth: 32 }}>
                <Storage fontSize="small" />
              </ListItemIcon>
              <ListItemText
                primary={farm.farm_name}
                secondary={
                  <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                    <Chip
                      label={`${farm.total_data_points.toLocaleString()} total`}
                      size="small"
                      variant="outlined"
                    />
                    <Chip
                      label={`${farm.recent_data_points.toLocaleString()} recent`}
                      size="small"
                      variant="outlined"
                      color={getDataHealthColor(farm.recent_data_points, farm.total_data_points)}
                    />
                    <Chip
                      label={`${farm.controllers} controllers`}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>

        {summary.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body2" color="textSecondary">
              No data available
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default DataSummaryCard;
