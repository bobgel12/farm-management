import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Button,
  Switch,
  Slider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
} from '@mui/material';
import {
  Refresh,
  CheckCircle,
  Error,
  Warning,
  PowerSettingsNew,
} from '@mui/icons-material';
import api from '../../services/api';

interface HouseDevicesTabProps {
  houseId: string;
  house: any;
}

const HouseDevicesTab: React.FC<HouseDevicesTabProps> = ({ houseId, house }) => {
  const [devices, setDevices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [controlDialog, setControlDialog] = useState<{ open: boolean; device: any | null }>({
    open: false,
    device: null,
  });
  const [percentage, setPercentage] = useState(0);

  useEffect(() => {
    loadDevices();
  }, [houseId]);

  const loadDevices = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get(`/houses/${houseId}/devices/`);
      setDevices(Array.isArray(response.data) ? response.data : []);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load devices');
    } finally {
      setLoading(false);
    }
  };

  const handleDeviceControl = async (deviceId: number, action: string, percentage?: number) => {
    try {
      const payload: any = { action };
      if (percentage !== undefined) {
        payload.percentage = percentage;
      }
      await api.post(`/devices/${deviceId}/control/`, payload);
      loadDevices(); // Refresh device list
    } catch (err: any) {
      console.error('Error controlling device:', err);
      setError(err.response?.data?.message || 'Failed to control device');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Device Management</Typography>
        <IconButton onClick={loadDevices}>
          <Refresh />
        </IconButton>
      </Box>

      {devices.length === 0 ? (
        <Card>
          <CardContent>
            <Typography variant="body1" color="text.secondary" align="center">
              No devices configured. Devices will appear here once they are added to the system.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2}>
          {devices.map((device) => (
            <Grid item xs={12} sm={6} md={4} key={device.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Box>
                      <Typography variant="h6">
                        {device.name || device.device_type.replace('_', ' ')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        #{device.device_number}
                      </Typography>
                    </Box>
                    <Chip
                      label={device.status}
                      color={
                        device.status === 'on' ? 'success' :
                        device.status === 'error' ? 'error' :
                        device.status === 'maintenance' ? 'warning' : 'default'
                      }
                      size="small"
                    />
                  </Box>
                  
                  {device.percentage !== null && (
                    <Box mb={2}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Level: {device.percentage}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={device.percentage}
                        sx={{ height: 8, borderRadius: 1 }}
                      />
                    </Box>
                  )}
                  
                  <Box display="flex" gap={1} mt={2}>
                    <Button
                      size="small"
                      variant={device.status === 'on' ? 'contained' : 'outlined'}
                      startIcon={<PowerSettingsNew />}
                      onClick={() => handleDeviceControl(
                        device.id,
                        device.status === 'on' ? 'off' : 'on'
                      )}
                    >
                      {device.status === 'on' ? 'Turn Off' : 'Turn On'}
                    </Button>
                    {device.percentage !== null && (
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          setControlDialog({ open: true, device });
                          setPercentage(device.percentage || 0);
                        }}
                      >
                        Set Level
                      </Button>
                    )}
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                    Last update: {new Date(device.last_update).toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Control Dialog */}
      <Dialog
        open={controlDialog.open}
        onClose={() => setControlDialog({ open: false, device: null })}
      >
        <DialogTitle>
          Control {controlDialog.device?.name || controlDialog.device?.device_type}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ width: 300, mt: 2 }}>
            <Typography gutterBottom>Percentage: {percentage}%</Typography>
            <Slider
              value={percentage}
              onChange={(e, value) => setPercentage(value as number)}
              min={0}
              max={100}
              step={1}
              marks={[
                { value: 0, label: '0%' },
                { value: 50, label: '50%' },
                { value: 100, label: '100%' },
              ]}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setControlDialog({ open: false, device: null })}>
            Cancel
          </Button>
          <Button
            onClick={() => {
              if (controlDialog.device) {
                handleDeviceControl(controlDialog.device.id, 'set_percentage', percentage);
                setControlDialog({ open: false, device: null });
              }
            }}
            variant="contained"
          >
            Apply
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default HouseDevicesTab;

