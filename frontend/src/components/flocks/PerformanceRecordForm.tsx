import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  ArrowBack as ArrowBackIcon,
  Calculate as CalculateIcon,
} from '@mui/icons-material';
import { useFlock } from '../../contexts/FlockContext';
import { FlockPerformance } from '../../types';
import dayjs from 'dayjs';

const PerformanceRecordForm: React.FC = () => {
  const navigate = useNavigate();
  const { flockId } = useParams<{ flockId: string }>();
  const {
    currentFlock,
    loading,
    error,
    fetchFlock,
    addPerformanceRecord,
    calculatePerformance,
  } = useFlock();

  const [formData, setFormData] = useState<Partial<FlockPerformance>>({
    record_date: dayjs().format('YYYY-MM-DD'),
    current_chicken_count: currentFlock?.current_chicken_count || currentFlock?.initial_chicken_count || 0,
    mortality_count: 0,
    average_weight_grams: undefined,
    feed_consumed_kg: undefined,
    daily_feed_consumption_kg: undefined,
    daily_water_consumption_liters: undefined,
    average_temperature: undefined,
    average_humidity: undefined,
    notes: '',
  });

  const [autoCalculate, setAutoCalculate] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [calculating, setCalculating] = useState(false);

  useEffect(() => {
    if (flockId) {
      fetchFlock(parseInt(flockId));
    }
  }, [flockId, fetchFlock]);

  useEffect(() => {
    if (currentFlock) {
      setFormData((prev) => ({
        ...prev,
        current_chicken_count: currentFlock.current_chicken_count || currentFlock.initial_chicken_count || 0,
      }));
    }
  }, [currentFlock]);

  const handleChange = (field: keyof FlockPerformance, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAutoCalculate = async () => {
    if (!flockId) return;

    setCalculating(true);
    setSubmitError(null);

    try {
      const recordDate = formData.record_date || dayjs().format('YYYY-MM-DD');
      const calculated = await calculatePerformance(parseInt(flockId), recordDate as any);
      
      // Update form with calculated values
      setFormData((prev) => ({
        ...prev,
        current_chicken_count: calculated.current_chicken_count,
        mortality_count: calculated.mortality_count || 0,
        average_weight_grams: calculated.average_weight_grams,
        feed_consumed_kg: calculated.feed_consumed_kg,
        daily_feed_consumption_kg: calculated.daily_feed_consumption_kg,
        feed_conversion_ratio: calculated.feed_conversion_ratio,
        daily_water_consumption_liters: calculated.daily_water_consumption_liters,
        mortality_rate: calculated.mortality_rate,
        livability: calculated.livability,
        average_temperature: calculated.average_temperature,
        average_humidity: calculated.average_humidity,
      }));
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to calculate performance metrics');
    } finally {
      setCalculating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flockId) return;

    setSubmitError(null);
    setSubmitting(true);

    try {
      if (autoCalculate) {
        // First try to auto-calculate if enabled
        try {
          const recordDate = formData.record_date || dayjs().format('YYYY-MM-DD');
          await calculatePerformance(parseInt(flockId), recordDate);
        } catch (calcErr) {
          // If auto-calculation fails, proceed with manual entry
          console.warn('Auto-calculation failed, using manual entry:', calcErr);
        }
      }

      // Create performance record with form data
      await addPerformanceRecord(parseInt(flockId), formData);
      navigate(`/flocks/${flockId}`);
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to save performance record');
    } finally {
      setSubmitting(false);
    }
  };

  // Calculate derived metrics
  const calculateDerivedMetrics = () => {
    const currentCount = formData.current_chicken_count || 0;
    const initialCount = currentFlock?.initial_chicken_count || 0;
    const mortalityCount = formData.mortality_count || 0;
    
    if (initialCount > 0) {
      const totalMortality = initialCount - currentCount;
      const mortalityRate = (totalMortality / initialCount) * 100;
      const livability = (currentCount / initialCount) * 100;
      
      return {
        total_mortality: totalMortality,
        mortality_rate: mortalityRate,
        livability,
      };
    }
    return null;
  };

  const derivedMetrics = calculateDerivedMetrics();

  if (loading && !currentFlock) {
    return (
      <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!currentFlock) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Flock not found</Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/flocks')}
          sx={{ mt: 2 }}
        >
          Back to Flocks
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(`/flocks/${flockId}`)}
        >
          Back
        </Button>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Add Performance Record
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {currentFlock.batch_number} • {currentFlock.flock_code}
        </Typography>
      </Box>

      {(error || submitError) && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {submitError || error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <form onSubmit={handleSubmit}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      required
                      label="Record Date"
                      type="date"
                      value={formData.record_date}
                      onChange={(e) => handleChange('record_date', e.target.value)}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      required
                      label="Current Chicken Count"
                      type="number"
                      value={formData.current_chicken_count || ''}
                      onChange={(e) => handleChange('current_chicken_count', parseInt(e.target.value) || 0)}
                      inputProps={{ min: 0 }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Mortality Count"
                      type="number"
                      value={formData.mortality_count || ''}
                      onChange={(e) => handleChange('mortality_count', parseInt(e.target.value) || 0)}
                      inputProps={{ min: 0 }}
                      helperText="Number of deaths since last record"
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Average Weight (grams)"
                      type="number"
                      value={formData.average_weight_grams || ''}
                      onChange={(e) => handleChange('average_weight_grams', parseFloat(e.target.value) || null)}
                      inputProps={{ min: 0, step: 0.1 }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Feed Consumed (kg)"
                      type="number"
                      value={formData.feed_consumed_kg || ''}
                      onChange={(e) => handleChange('feed_consumed_kg', parseFloat(e.target.value) || null)}
                      inputProps={{ min: 0, step: 0.01 }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Daily Feed Consumption (kg)"
                      type="number"
                      value={formData.daily_feed_consumption_kg || ''}
                      onChange={(e) => handleChange('daily_feed_consumption_kg', parseFloat(e.target.value) || null)}
                      inputProps={{ min: 0, step: 0.01 }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Daily Water Consumption (liters)"
                      type="number"
                      value={formData.daily_water_consumption_liters || ''}
                      onChange={(e) => handleChange('daily_water_consumption_liters', parseFloat(e.target.value) || null)}
                      inputProps={{ min: 0, step: 0.01 }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Average Temperature (°C)"
                      type="number"
                      value={formData.average_temperature || ''}
                      onChange={(e) => handleChange('average_temperature', parseFloat(e.target.value) || null)}
                      inputProps={{ min: 0, step: 0.1 }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Average Humidity (%)"
                      type="number"
                      value={formData.average_humidity || ''}
                      onChange={(e) => handleChange('average_humidity', parseFloat(e.target.value) || null)}
                      inputProps={{ min: 0, max: 100, step: 0.1 }}
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Notes"
                      multiline
                      rows={4}
                      value={formData.notes || ''}
                      onChange={(e) => handleChange('notes', e.target.value)}
                      placeholder="Additional notes about this performance record..."
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={autoCalculate}
                          onChange={(e) => setAutoCalculate(e.target.checked)}
                        />
                      }
                      label="Auto-calculate metrics from house data (if available)"
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                      <Button
                        variant="outlined"
                        startIcon={<CancelIcon />}
                        onClick={() => navigate(`/flocks/${flockId}`)}
                        disabled={submitting || calculating}
                      >
                        Cancel
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={calculating ? <CircularProgress size={20} /> : <CalculateIcon />}
                        onClick={handleAutoCalculate}
                        disabled={submitting || calculating}
                      >
                        Calculate
                      </Button>
                      <Button
                        type="submit"
                        variant="contained"
                        startIcon={submitting ? <CircularProgress size={20} /> : <SaveIcon />}
                        disabled={submitting || calculating}
                      >
                        {submitting ? 'Saving...' : 'Save Record'}
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </form>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Calculated Metrics
              </Typography>
              {derivedMetrics ? (
                <Box sx={{ mt: 2 }}>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Total Mortality
                    </Typography>
                    <Typography variant="h6">
                      {derivedMetrics.total_mortality.toLocaleString()}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Mortality Rate
                    </Typography>
                    <Typography variant="h6">
                      {derivedMetrics.mortality_rate.toFixed(2)}%
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Livability
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      {derivedMetrics.livability.toFixed(2)}%
                    </Typography>
                  </Box>
                  {formData.feed_conversion_ratio && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Feed Conversion Ratio (FCR)
                      </Typography>
                      <Typography variant="h6">
                        {formData.feed_conversion_ratio.toFixed(2)}
                      </Typography>
                    </Box>
                  )}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Enter data to see calculated metrics
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PerformanceRecordForm;

