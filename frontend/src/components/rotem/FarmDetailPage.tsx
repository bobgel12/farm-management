import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack,
  Refresh,
  TrendingUp,
  Settings,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useRotem } from '../../contexts/RotemContext';
import { FarmDashboardData, RotemDataPoint } from '../../types/rotem';
import SensorDataChart from './SensorDataChart';
import FarmInfoCard from './FarmInfoCard';
import ControllerStatusCard from './ControllerStatusCard';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`farm-tabpanel-${index}`}
      aria-labelledby={`farm-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const FarmDetailPage: React.FC = () => {
  const { farmId } = useParams<{ farmId: string }>();
  const navigate = useNavigate();
  const { getFarmDashboard, scrapeFarm, state } = useRotem();
  const [farmData, setFarmData] = useState<FarmDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [isScraping, setIsScraping] = useState(false);

  const loadFarmData = async () => {
    if (!farmId) return;

    try {
      console.log('DEBUG: FarmDetailPage loadFarmData called with farmId:', farmId);
      setLoading(true);
      setError(null);
      const data = await getFarmDashboard(farmId);
      console.log('DEBUG: FarmDetailPage data loaded:', data);
      setFarmData(data);
    } catch (err) {
      console.error('DEBUG: FarmDetailPage error:', err);
      setError('Failed to load farm data');
    } finally {
      setLoading(false);
    }
  };

  const handleScrape = async () => {
    if (!farmId) return;

    setIsScraping(true);
    try {
      await scrapeFarm(farmId);
      await loadFarmData(); // Refresh data
    } finally {
      setIsScraping(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  useEffect(() => {
    loadFarmData();
  }, [farmId]);

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading farm data...</Typography>
      </Box>
    );
  }

  if (error || !farmData) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || 'Farm not found'}
        </Alert>
        <Button
          variant="contained"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/rotem')}
        >
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  const { farm, controllers, recent_data, summary, last_scrape } = farmData;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton
          onClick={() => navigate('/rotem')}
          sx={{ mr: 2 }}
        >
          <ArrowBack />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            {farm.farm_name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              label={farm.is_active ? 'Active' : 'Inactive'}
              color={farm.is_active ? 'success' : 'default'}
              size="small"
            />
            <Chip
              label={farm.gateway_name}
              variant="outlined"
              size="small"
            />
            <Chip
              label={`${summary.total_data_points} data points`}
              variant="outlined"
              size="small"
            />
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadFarmData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<TrendingUp />}
            onClick={handleScrape}
            disabled={isScraping}
          >
            {isScraping ? 'Scraping...' : 'Scrape Data'}
          </Button>
        </Box>
      </Box>

      {/* Last Scrape Status */}
      {last_scrape && (
        <Alert
          severity={last_scrape.status === 'success' ? 'success' : 'error'}
          sx={{ mb: 3 }}
          icon={last_scrape.status === 'success' ? <CheckCircle /> : <Error />}
        >
          Last scrape: {last_scrape.status} - {last_scrape.data_points_collected} data points collected
          {last_scrape.error_message && ` - ${last_scrape.error_message}`}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="farm detail tabs"
        >
          <Tab label="Overview" />
          <Tab label="Sensor Data" />
          <Tab label="Controllers" />
          <Tab label="Settings" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FarmInfoCard farm={farm} summary={summary} />
          </Grid>
          <Grid item xs={12} md={6}>
            <ControllerStatusCard controllers={controllers} />
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <SensorDataChart
          data={recent_data}
          title={`${farm.farm_name} - Sensor Data`}
          height={400}
        />
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={2}>
          {controllers.map((controller) => (
            <Grid item xs={12} sm={6} md={4} key={controller.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {controller.controller_name}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                    <Chip
                      label={controller.is_connected ? 'Connected' : 'Disconnected'}
                      color={controller.is_connected ? 'success' : 'error'}
                      size="small"
                    />
                    <Chip
                      label={controller.controller_type}
                      variant="outlined"
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="textSecondary">
                    Last seen: {controller.last_seen 
                      ? new Date(controller.last_seen).toLocaleString()
                      : 'Never'
                    }
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Farm Settings
            </Typography>
            <Typography color="textSecondary">
              Farm settings and configuration options will be available here.
            </Typography>
          </CardContent>
        </Card>
      </TabPanel>
    </Box>
  );
};

export default FarmDetailPage;
