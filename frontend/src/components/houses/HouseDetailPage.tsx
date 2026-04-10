import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Paper,
  IconButton,
  Tooltip,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  ArrowBack,
  Dashboard as OverviewIcon,
  Devices as DevicesIcon,
  Pets as FlockIcon,
  Message as MessageIcon,
  Settings as SettingsIcon,
  Home,
  CompareArrows,
  Assignment as TasksIcon,
  TrendingDown as MortalityIcon,
  Report as IssuesIcon,
  WaterDrop as WaterDropIcon,
} from '@mui/icons-material';
import api from '../../services/api';
import { useFarm } from '../../contexts/FarmContext';
import HouseOverviewTab from './HouseOverviewTab';
import HouseDevicesTab from './HouseDevicesTab';
import HouseFlockTab from './HouseFlockTab';
import HouseMessagesTab from './HouseMessagesTab';
import HouseMenuTab from './HouseMenuTab';
import HouseTasksTab from './HouseTasksTab';
import HouseMortalityTab from './HouseMortalityTab';
import HouseIssuesTab from './HouseIssuesTab';
import HouseWaterHistoryTab from './HouseWaterHistoryTab';
import { QuickIssueButton } from '../issues';

interface HouseDetails {
  house: any;
  monitoring: any;
  alarms: any[];
  stats: any;
  tasks?: {
    all: any[];
    today: any[];
    upcoming: any[];
    past: any[];
    completed: any[];
    total: number;
    completed_count: number;
    pending_count: number;
  };
}

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
      id={`house-tabpanel-${index}`}
      aria-labelledby={`house-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const HouseDetailPage: React.FC = () => {
  const { houseId, farmId } = useParams<{ houseId: string; farmId?: string }>();
  const navigate = useNavigate();
  const { farms } = useFarm();
  const [houseDetails, setHouseDetails] = useState<HouseDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  // Get farm info
  const currentFarm = farmId ? farms.find(f => f.id === parseInt(farmId)) : null;
  const houseFarmId = houseDetails?.house?.farm_id || houseDetails?.house?.farm?.id || (farmId ? parseInt(farmId) : null);
  const houseFarm = houseFarmId ? farms.find(f => f.id === houseFarmId) : null;
  
  // Check if farm is integrated with Rotem (from nested farm object or context)
  // Show water history tab if Rotem integration is configured (regardless of status)
  // This allows access to historical data even if integration status is not 'active'
  const farmFromDetails = houseDetails?.house?.farm;
  const farmFromContext = houseFarm || currentFarm;
  const farm = farmFromDetails || farmFromContext;
  
  // Simple check: Show tab if integration_type is 'rotem' (regardless of status or other flags)
  // This is the most permissive check to ensure the tab shows for all Rotem-configured farms
  // Check multiple sources: farm integration_type, rotem_farm_id, or house is_integrated
  const isFarmIntegrated = (
    // Check farm integration_type
    (farm && (farm.integration_type === 'rotem' || (farm.rotem_farm_id && String(farm.rotem_farm_id).trim() !== ''))) ||
    // Fallback: check house is_integrated flag (house-level integration indicator)
    (houseDetails?.house?.is_integrated === true)
  );
  
  // Debug logging (remove in production if needed)
  if (process.env.NODE_ENV === 'development') {
    console.log('Farm integration check:', {
      farm: farm ? { id: farm.id, name: farm.name } : null,
      farmFromDetails: farmFromDetails ? { id: farmFromDetails.id, integration_type: farmFromDetails.integration_type } : null,
      farmFromContext: farmFromContext ? { id: farmFromContext.id, integration_type: farmFromContext.integration_type } : null,
      integration_type: farm?.integration_type,
      has_system_integration: farm?.has_system_integration,
      is_integrated: farm?.is_integrated,
      integration_status: farm?.integration_status,
      rotem_farm_id: farm?.rotem_farm_id ? 'exists' : 'missing',
      isFarmIntegrated
    });
  }

  useEffect(() => {
    if (houseId) {
      loadHouseDetails();
    }
  }, [houseId]);

  const loadHouseDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/houses/${houseId}/details/`);
      setHouseDetails(response.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load house details');
      console.error('Error loading house details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 3 }}>
        {error}
      </Alert>
    );
  }

  if (!houseDetails || !houseDetails.house) {
    return (
      <Alert severity="warning" sx={{ m: 3 }}>
        House not found
      </Alert>
    );
  }

  const house = houseDetails.house;

  const handleBack = () => {
    if (farmId) {
      navigate(`/farms/${farmId}`);
    } else if (houseFarmId) {
      navigate(`/farms/${houseFarmId}`);
    } else {
      navigate(-1);
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Breadcrumbs */}
      {(farmId || houseFarmId) && (currentFarm || houseFarm) && (
        <Breadcrumbs sx={{ mb: 2, px: 2, pt: 2 }}>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/farms')}
            sx={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}
          >
            <Home sx={{ mr: 0.5, fontSize: 20 }} />
            Farms
          </Link>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate(`/farms/${farmId || houseFarmId}`)}
            sx={{ textDecoration: 'none' }}
          >
            {(currentFarm || houseFarm)?.name}
          </Link>
          <Typography color="text.primary">House {house.house_number}</Typography>
        </Breadcrumbs>
      )}

      {/* Header */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" p={2}>
          <Box display="flex" alignItems="center" gap={2}>
            <IconButton onClick={handleBack}>
              <ArrowBack />
            </IconButton>
            <Box>
              <Typography variant="h4" component="h1">
                House {house.house_number}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {house.farm_name || house.farm?.name || (currentFarm || houseFarm)?.name}
              </Typography>
            </Box>
            {(house.age_days ?? house.current_day) !== null && (
              <Chip
                label={`Day ${house.age_days ?? house.current_day}`}
                color="primary"
                variant="outlined"
              />
            )}
            <Chip
              label={house.status}
              color={
                house.status === 'production' || house.status === 'growth'
                  ? 'success'
                  : house.status === 'warning'
                  ? 'warning'
                  : 'default'
              }
            />
          </Box>
          <Box display="flex" gap={1}>
            {(farmId || houseFarmId) && (
              <IconButton
                onClick={() => navigate(`/farms/${farmId || houseFarmId}/houses/comparison`)}
                title="View Comparison"
              >
                <CompareArrows />
              </IconButton>
            )}
          </Box>
        </Box>

        {/* Tabs */}
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="house detail tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab
            icon={<OverviewIcon />}
            iconPosition="start"
            label="Overview"
            id="house-tab-0"
            aria-controls="house-tabpanel-0"
          />
          <Tab
            icon={<DevicesIcon />}
            iconPosition="start"
            label="Devices"
            id="house-tab-1"
            aria-controls="house-tabpanel-1"
          />
          <Tab
            icon={<FlockIcon />}
            iconPosition="start"
            label="Flock"
            id="house-tab-2"
            aria-controls="house-tabpanel-2"
          />
          <Tab
            icon={<TasksIcon />}
            iconPosition="start"
            label="Tasks"
            id="house-tab-3"
            aria-controls="house-tabpanel-3"
          />
          <Tab
            icon={<MessageIcon />}
            iconPosition="start"
            label="Messages"
            id="house-tab-4"
            aria-controls="house-tabpanel-4"
          />
          <Tab
            icon={<MortalityIcon />}
            iconPosition="start"
            label="Mortality"
            id="house-tab-5"
            aria-controls="house-tabpanel-5"
          />
          <Tab
            icon={<IssuesIcon />}
            iconPosition="start"
            label="Issues"
            id="house-tab-6"
            aria-controls="house-tabpanel-6"
          />
          <Tab
            icon={<SettingsIcon />}
            iconPosition="start"
            label="House Menu"
            id="house-tab-7"
            aria-controls="house-tabpanel-7"
          />
          {isFarmIntegrated && (
            <Tab
              icon={<WaterDropIcon />}
              iconPosition="start"
              label="Water History"
              id="house-tab-8"
              aria-controls="house-tabpanel-8"
            />
          )}
        </Tabs>
      </Box>

      {/* Tab Panels */}
      <TabPanel value={activeTab} index={0}>
        <HouseOverviewTab
          house={house}
          monitoring={houseDetails.monitoring}
          alarms={houseDetails.alarms}
          stats={houseDetails.stats}
          onRefresh={loadHouseDetails}
        />
      </TabPanel>
      <TabPanel value={activeTab} index={1}>
        <HouseDevicesTab houseId={houseId!} house={house} />
      </TabPanel>
      <TabPanel value={activeTab} index={2}>
        <HouseFlockTab houseId={houseId!} house={house} />
      </TabPanel>
      <TabPanel value={activeTab} index={3}>
        {houseDetails.tasks ? (
          <HouseTasksTab
            tasks={houseDetails.tasks}
            currentDay={house.current_day}
            loading={loading}
          />
        ) : (
          <Alert severity="info">
            Tasks are not available. They will be generated when a program is assigned to the farm and houses are synced.
          </Alert>
        )}
      </TabPanel>
      <TabPanel value={activeTab} index={4}>
        <HouseMessagesTab houseId={houseId!} house={house} />
      </TabPanel>
      <TabPanel value={activeTab} index={5}>
        <HouseMortalityTab houseId={parseInt(houseId!)} house={house} />
      </TabPanel>
      <TabPanel value={activeTab} index={6}>
        <HouseIssuesTab houseId={parseInt(houseId!)} house={house} />
      </TabPanel>
      <TabPanel value={activeTab} index={7}>
        <HouseMenuTab houseId={houseId!} house={house} />
      </TabPanel>
      {isFarmIntegrated && (
        <TabPanel value={activeTab} index={8}>
          <HouseWaterHistoryTab houseId={houseId!} house={house} />
        </TabPanel>
      )}

      {/* Quick Issue Report Button */}
      <QuickIssueButton
        houseId={parseInt(houseId!)}
        houseName={`House ${house.house_number}`}
      />
    </Box>
  );
};

export default HouseDetailPage;

