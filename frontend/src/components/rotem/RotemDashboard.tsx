import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Alert,
  IconButton,
  Tooltip,
  Paper,
  Divider,
} from '@mui/material';
import {
  Refresh,
  Add,
  Settings,
  TrendingUp,
  Warning,
  CheckCircle,
  Error,
  Schedule,
} from '@mui/icons-material';
import { useRotem } from '../../contexts/RotemContext';
import { FarmDataSummary, RotemScrapeLog } from '../../types/rotem';
import FarmCard from './FarmCard';
import DataSummaryCard from './DataSummaryCard';
import RecentLogsCard from './RecentLogsCard';
import AddFarmDialog from './AddFarmDialog';

const RotemDashboard: React.FC = () => {
  const { state, refreshAllData, scrapeAllFarms, clearError } = useRotem();
  const [addFarmOpen, setAddFarmOpen] = useState(false);
  const [isScraping, setIsScraping] = useState(false);

  const handleRefresh = async () => {
    await refreshAllData();
  };

  const handleScrapeAll = async () => {
    setIsScraping(true);
    try {
      await scrapeAllFarms();
    } finally {
      setIsScraping(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle />;
      case 'failed':
        return <Error />;
      case 'running':
        return <Schedule />;
      default:
        return <Warning />;
    }
  };

  const totalDataPoints = state.dataSummary.reduce(
    (sum, farm) => sum + farm.total_data_points,
    0
  );

  const recentDataPoints = state.dataSummary.reduce(
    (sum, farm) => sum + farm.recent_data_points,
    0
  );

  const activeFarms = Array.isArray(state.farms) ? state.farms.filter(farm => farm.is_active).length : 0;
  const totalControllers = state.dataSummary.reduce(
    (sum, farm) => sum + farm.controllers,
    0
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Rotem Integration Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Add />}
            onClick={() => setAddFarmOpen(true)}
          >
            Add Farm
          </Button>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={state.loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<TrendingUp />}
            onClick={handleScrapeAll}
            disabled={state.loading || isScraping}
          >
            {isScraping ? 'Scraping...' : 'Scrape All Farms'}
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {state.error && (
        <Alert severity="error" onClose={clearError} sx={{ mb: 3 }}>
          {state.error}
        </Alert>
      )}

      {/* Loading Indicator */}
      {state.loading && (
        <LinearProgress sx={{ mb: 3 }} />
      )}

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Farms
              </Typography>
              <Typography variant="h4">
                {activeFarms}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Controllers
              </Typography>
              <Typography variant="h4">
                {totalControllers}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Data Points
              </Typography>
              <Typography variant="h4">
                {totalDataPoints.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Recent Data (24h)
              </Typography>
              <Typography variant="h4">
                {recentDataPoints.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Farm Cards */}
        <Grid item xs={12} lg={8}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" component="h2">
                Farms Overview
              </Typography>
              <Chip
                label={`${Array.isArray(state.farms) ? state.farms.length : 0} farms`}
                color="primary"
                variant="outlined"
              />
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            {!Array.isArray(state.farms) || state.farms.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="h6" color="textSecondary" gutterBottom>
                  No farms configured
                </Typography>
                <Typography color="textSecondary" sx={{ mb: 2 }}>
                  Add your first farm to start collecting data
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setAddFarmOpen(true)}
                >
                  Add Farm
                </Button>
              </Box>
            ) : (
              <Grid container spacing={2}>
                {Array.isArray(state.farms) && state.farms.map((farm) => (
                  <Grid item xs={12} sm={6} md={4} key={farm.farm_id}>
                    <FarmCard farm={farm} />
                  </Grid>
                ))}
              </Grid>
            )}
          </Paper>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Data Summary */}
            <DataSummaryCard summary={state.dataSummary} />
            
            {/* Recent Logs */}
            <RecentLogsCard logs={state.scrapeLogs} />
          </Box>
        </Grid>
      </Grid>

      {/* Add Farm Dialog */}
      <AddFarmDialog
        open={addFarmOpen}
        onClose={() => setAddFarmOpen(false)}
      />
    </Box>
  );
};

export default RotemDashboard;
