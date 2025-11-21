import React, { memo } from 'react';
import {
  Box,
  Typography,
  Button,
  Chip,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Settings,
  IntegrationInstructions,
  Sync,
  Refresh,
  CheckCircle,
  Error,
  Warning,
  Home,
} from '@mui/icons-material';
import { Farm } from '../../types';

interface IntegrationHealth {
  is_healthy: boolean;
  success_rate_24h: number;
  consecutive_failures: number;
  average_response_time?: number;
  last_successful_sync?: string;
  last_attempted_sync?: string;
}

interface FarmHeaderSectionProps {
  farm: Farm;
  integrationHealth: IntegrationHealth | null;
  loadingHealth: boolean;
  onRefresh: () => void;
  onSyncData: () => void;
  onGenerateHouses: () => void;
  onConfigureIntegration: (farmId: number) => void;
  formatLastSync: (lastSync?: string) => string;
  getIntegrationStatusColor: (status: string) => 'success' | 'error' | 'warning' | 'default';
  getIntegrationStatusIcon: (status: string) => React.ReactElement;
}

const FarmHeaderSection: React.FC<FarmHeaderSectionProps> = ({
  farm,
  integrationHealth,
  loadingHealth,
  onRefresh,
  onSyncData,
  onGenerateHouses,
  onConfigureIntegration,
  formatLastSync,
  getIntegrationStatusColor,
  getIntegrationStatusIcon,
}) => {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            <Typography variant="h4" gutterBottom>
              {farm.name}
            </Typography>
            <Typography color="textSecondary" variant="h6" gutterBottom>
              {farm.location}
            </Typography>
            {farm.description && (
              <Typography color="textSecondary" sx={{ mt: 1 }}>
                {farm.description}
              </Typography>
            )}
          </Box>
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={onRefresh}
              size="small"
              aria-label="Refresh farm data"
            >
              Refresh
            </Button>
            {farm.has_system_integration && (
              <>
                <Button
                  variant="outlined"
                  startIcon={<Sync />}
                  onClick={onSyncData}
                  size="small"
                  aria-label="Sync data from integrated system"
                >
                  Sync Data
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Home />}
                  onClick={onGenerateHouses}
                  size="small"
                  color="primary"
                  aria-label="Generate houses and tasks"
                >
                  Generate Houses & Tasks
                </Button>
              </>
            )}
            <Button
              variant="outlined"
              startIcon={<Settings />}
              onClick={() => onConfigureIntegration(farm.id)}
              size="small"
              aria-label="Configure farm integration settings"
            >
              Configure
            </Button>
          </Box>
        </Box>

        {/* Integration Status */}
        <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
          <Chip
            label={farm.integration_type === 'none' ? 'Manual Management' : 'System Integrated'}
            color={farm.integration_type === 'none' ? 'default' : 'primary'}
            icon={farm.integration_type === 'none' ? <Settings /> : <IntegrationInstructions />}
          />
          {farm.has_system_integration && (
            <Chip
              label={`Status: ${farm.integration_status}`}
              color={getIntegrationStatusColor(farm.integration_status)}
              icon={getIntegrationStatusIcon(farm.integration_status)}
            />
          )}
          {farm.last_sync && (
            <Chip
              label={`Last Sync: ${formatLastSync(farm.last_sync)}`}
              color="info"
              variant="outlined"
            />
          )}
        </Box>

        {/* Integration Health (for integrated farms) */}
        {farm.has_system_integration && (
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Integration Health
            </Typography>
            {loadingHealth ? (
              <CircularProgress size={20} />
            ) : integrationHealth ? (
              <Box display="flex" gap={2} flexWrap="wrap">
                <Chip
                  label={`Success Rate: ${integrationHealth.success_rate_24h.toFixed(1)}%`}
                  color={integrationHealth.success_rate_24h > 90 ? 'success' : 'warning'}
                  size="small"
                />
                <Chip
                  label={`Failures: ${integrationHealth.consecutive_failures}`}
                  color={integrationHealth.consecutive_failures > 3 ? 'error' : 'default'}
                  size="small"
                />
                {integrationHealth.average_response_time && (
                  <Chip
                    label={`Avg Response: ${integrationHealth.average_response_time.toFixed(2)}s`}
                    color="info"
                    size="small"
                  />
                )}
              </Box>
            ) : (
              <Alert severity="warning" sx={{ mt: 1 }}>
                Unable to load integration health data
              </Alert>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default memo(FarmHeaderSection);

