import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  Warning,
  Error,
  Info,
  CheckCircle,
  Close,
  Schedule,
} from '@mui/icons-material';
import { HouseAlarm, WaterConsumptionAlert } from '../../types/monitoring';
import monitoringApiService from '../../services/monitoringApi';

interface HouseAlertsPanelProps {
  houseId: number;
  alarms: HouseAlarm[];
}

const HouseAlertsPanel: React.FC<HouseAlertsPanelProps> = ({ houseId, alarms }) => {
  const [waterAlerts, setWaterAlerts] = useState<WaterConsumptionAlert[]>([]);

  const loadWaterAlerts = async () => {
    try {
      const response = await monitoringApiService.getWaterAlerts(houseId);
      setWaterAlerts(response.results || []);
    } catch (error) {
      // Keep UI resilient; water alerts are additive.
    }
  };

  useEffect(() => {
    loadWaterAlerts();
  }, [houseId]);

  const handleAcknowledgeWaterAlert = async (id: number) => {
    await monitoringApiService.acknowledgeWaterAlert(id);
    await loadWaterAlerts();
  };

  const handleResolveWaterAlert = async (id: number) => {
    await monitoringApiService.resolveWaterAlert(id);
    await loadWaterAlerts();
  };

  const handleSnoozeWaterAlert = async (id: number, hours: number) => {
    await monitoringApiService.snoozeWaterAlert(id, hours);
    await loadWaterAlerts();
  };
  const [filter, setFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');

  const handleFilterChange = (event: SelectChangeEvent<string>) => {
    setFilter(event.target.value);
  };

  const handleSeverityFilterChange = (event: SelectChangeEvent<string>) => {
    setSeverityFilter(event.target.value);
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <Error color="error" />;
      case 'high':
        return <Error color="error" />;
      case 'medium':
        return <Warning color="warning" />;
      default:
        return <Info color="info" />;
    }
  };

  const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'success' => {
    switch (severity) {
      case 'critical':
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'info';
    }
  };

  // Filter alarms
  const filteredAlarms = alarms.filter((alarm) => {
    if (filter !== 'all' && alarm.alarm_type !== filter) return false;
    if (severityFilter !== 'all' && alarm.severity !== severityFilter) return false;
    return alarm.is_active;
  });

  const activeAlarmsCount = alarms.filter(a => a.is_active).length;
  const criticalAlarmsCount = alarms.filter(a => a.is_active && a.severity === 'critical').length;

  if (alarms.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Active Alarms ({activeAlarmsCount})
          </Typography>
          <Box display="flex" gap={2}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <Select value={filter} onChange={handleFilterChange}>
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="temperature">Temperature</MenuItem>
                <MenuItem value="humidity">Humidity</MenuItem>
                <MenuItem value="pressure">Pressure</MenuItem>
                <MenuItem value="connection">Connection</MenuItem>
                <MenuItem value="consumption">Consumption</MenuItem>
                <MenuItem value="equipment">Equipment</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <Select value={severityFilter} onChange={handleSeverityFilterChange}>
                <MenuItem value="all">All Severities</MenuItem>
                <MenuItem value="critical">Critical</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>

        {criticalAlarmsCount > 0 && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {criticalAlarmsCount} critical alarm{criticalAlarmsCount > 1 ? 's' : ''} active
          </Alert>
        )}

        {filteredAlarms.length === 0 ? (
          <Alert severity="info">No alarms match the selected filters</Alert>
        ) : (
          <List>
            {filteredAlarms.map((alarm) => (
              <ListItem
                key={alarm.id}
                sx={{
                  borderLeft: `4px solid`,
                  borderColor: getSeverityColor(alarm.severity) === 'error' ? 'error.main' :
                              getSeverityColor(alarm.severity) === 'warning' ? 'warning.main' :
                              'info.main',
                  mb: 1,
                  bgcolor: 'background.paper',
                }}
              >
                <ListItemIcon>
                  {getSeverityIcon(alarm.severity)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle1">{alarm.message}</Typography>
                      <Chip
                        label={alarm.severity}
                        size="small"
                        color={getSeverityColor(alarm.severity)}
                      />
                      <Chip
                        label={alarm.alarm_type}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(alarm.timestamp).toLocaleString()}
                      </Typography>
                      {alarm.parameter_name && alarm.parameter_value !== null && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {alarm.parameter_name}: {alarm.parameter_value}
                          {alarm.threshold_value !== null && ` (threshold: ${alarm.threshold_value})`}
                        </Typography>
                      )}
                    </Box>
                  }
                />
                {alarm.is_resolved && (
                  <Chip
                    icon={<CheckCircle />}
                    label="Resolved"
                    size="small"
                    color="success"
                    sx={{ ml: 2 }}
                  />
                )}
              </ListItem>
            ))}
          </List>
        )}

        {waterAlerts.length > 0 && (
          <Box mt={3}>
            <Typography variant="subtitle1" gutterBottom>
              Water Alert Workflow ({waterAlerts.filter((a) => !a.is_resolved).length} open)
            </Typography>
            <List>
              {waterAlerts.map((alert) => (
                <ListItem key={`water-${alert.id}`}>
                  <ListItemIcon>
                    {alert.is_resolved ? <CheckCircle color="success" /> : <Warning color="warning" />}
                  </ListItemIcon>
                  <ListItemText
                    primary={`${alert.severity.toUpperCase()} ${alert.anomaly_direction} water anomaly`}
                    secondary={`${new Date(alert.alert_date).toLocaleDateString()} - ${alert.current_consumption.toFixed(2)} L/day`}
                  />
                  {!alert.is_acknowledged && (
                    <Tooltip title="Acknowledge">
                      <IconButton onClick={() => handleAcknowledgeWaterAlert(alert.id)}>
                        <CheckCircle />
                      </IconButton>
                    </Tooltip>
                  )}
                  {!alert.is_resolved && (
                    <Tooltip title="Snooze 6h">
                      <IconButton onClick={() => handleSnoozeWaterAlert(alert.id, 6)}>
                        <Schedule />
                      </IconButton>
                    </Tooltip>
                  )}
                  {!alert.is_resolved && (
                    <Tooltip title="Resolve">
                      <IconButton onClick={() => handleResolveWaterAlert(alert.id)}>
                        <Close />
                      </IconButton>
                    </Tooltip>
                  )}
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default HouseAlertsPanel;

