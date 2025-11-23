import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  IconButton,
} from '@mui/material';
import {
  Save,
  Refresh,
  Thermostat,
  WaterDrop,
  Air,
  Lightbulb,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import api from '../../services/api';

interface ControlPanelProps {
  houseId: string;
  house: any;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ houseId, house }) => {
  const [settings, setSettings] = useState<any>(null);
  const [temperatureCurve, setTemperatureCurve] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadControlSettings();
  }, [houseId]);

  const loadControlSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const [settingsResponse, curveResponse] = await Promise.all([
        api.get(`/houses/${houseId}/control/`),
        api.get(`/houses/${houseId}/control/temperature-curve/`),
      ]);
      setSettings(settingsResponse.data);
      setTemperatureCurve(Array.isArray(curveResponse.data) ? curveResponse.data : []);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load control settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      await api.put(`/houses/${houseId}/control/`, settings);
      // Save temperature curve if changed
      if (temperatureCurve.length > 0) {
        await api.post(`/houses/${houseId}/control/temperature-curve/`, temperatureCurve);
      }
      await loadControlSettings();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to save control settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (!settings) {
    return (
      <Alert severity="warning">
        Control settings not found. They will be created when you save.
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Control Settings</Typography>
        <Box>
          <IconButton onClick={loadControlSettings}>
            <Refresh />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSave}
            disabled={saving}
          >
            Save
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Temperature Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Thermostat color="primary" />
                <Typography variant="h6">Temperature Settings</Typography>
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Min Temperature (°F)"
                    type="number"
                    value={settings.min_temperature || ''}
                    onChange={(e) => setSettings({
                      ...settings,
                      min_temperature: parseFloat(e.target.value) || null
                    })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Max Temperature (°F)"
                    type="number"
                    value={settings.max_temperature || ''}
                    onChange={(e) => setSettings({
                      ...settings,
                      max_temperature: parseFloat(e.target.value) || null
                    })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Target Temperature (°F)"
                    type="number"
                    value={settings.target_temperature || ''}
                    onChange={(e) => setSettings({
                      ...settings,
                      target_temperature: parseFloat(e.target.value) || null
                    })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Temperature Offset (°F)"
                    type="number"
                    value={settings.temperature_offset || 0}
                    onChange={(e) => setSettings({
                      ...settings,
                      temperature_offset: parseFloat(e.target.value) || 0
                    })}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Humidity Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <WaterDrop color="info" />
                <Typography variant="h6">Humidity Settings</Typography>
              </Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.humidity_treatment_enabled || false}
                    onChange={(e) => setSettings({
                      ...settings,
                      humidity_treatment_enabled: e.target.checked
                    })}
                  />
                }
                label="Humidity Treatment Enabled"
              />
              <Grid container spacing={2} mt={1}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Target Humidity (%)"
                    type="number"
                    value={settings.humidity_target || ''}
                    onChange={(e) => setSettings({
                      ...settings,
                      humidity_target: parseFloat(e.target.value) || null
                    })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Min Humidity (%)"
                    type="number"
                    value={settings.humidity_min || ''}
                    onChange={(e) => setSettings({
                      ...settings,
                      humidity_min: parseFloat(e.target.value) || null
                    })}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    label="Max Humidity (%)"
                    type="number"
                    value={settings.humidity_max || ''}
                    onChange={(e) => setSettings({
                      ...settings,
                      humidity_max: parseFloat(e.target.value) || null
                    })}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Ventilation Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Air color="secondary" />
                <Typography variant="h6">Ventilation Settings</Typography>
              </Box>
              <FormControl fullWidth>
                <InputLabel>Ventilation Mode</InputLabel>
                <Select
                  value={settings.ventilation_mode || 'minimum'}
                  onChange={(e) => setSettings({
                    ...settings,
                    ventilation_mode: e.target.value
                  })}
                >
                  <MenuItem value="minimum">Minimum Ventilation</MenuItem>
                  <MenuItem value="tunnel">Tunnel Ventilation</MenuItem>
                  <MenuItem value="natural">Natural Ventilation</MenuItem>
                  <MenuItem value="mixed">Mixed Mode</MenuItem>
                </Select>
              </FormControl>
              <Grid container spacing={2} mt={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Static Pressure Target"
                    type="number"
                    value={settings.static_pressure_target || ''}
                    onChange={(e) => setSettings({
                      ...settings,
                      static_pressure_target: parseFloat(e.target.value) || null
                    })}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Lighting Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <Lightbulb color="warning" />
                <Typography variant="h6">Lighting Settings</Typography>
              </Box>
              <TextField
                fullWidth
                label="Light Dimmer Level (%)"
                type="number"
                value={settings.light_dimmer_level || ''}
                onChange={(e) => setSettings({
                  ...settings,
                  light_dimmer_level: parseFloat(e.target.value) || null
                })}
                inputProps={{ min: 0, max: 100 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Temperature Curve */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Temperature Curve
              </Typography>
              {temperatureCurve.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={temperatureCurve}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" label={{ value: 'Day', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'Temperature (°F)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="target_temperature"
                      stroke="#8884d8"
                      name="Target Temperature"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No temperature curve data. Temperature curve editor will be available in a future update.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ControlPanel;

