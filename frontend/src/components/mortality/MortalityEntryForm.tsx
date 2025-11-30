import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Grid,
  Collapse,
  IconButton,
  Alert,
  CircularProgress,
  Divider,
  InputAdornment,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Save as SaveIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { MortalityRecordCreate } from '../../types';
import { mortalityApi } from '../../services/mortalityApi';

interface MortalityEntryFormProps {
  flockId: number;
  houseId: number;
  onSuccess?: () => void;
  onCancel?: () => void;
  compact?: boolean;
}

const CAUSE_LABELS = {
  disease_deaths: 'Disease',
  culling_deaths: 'Culling',
  accident_deaths: 'Accident',
  heat_stress_deaths: 'Heat Stress',
  cold_stress_deaths: 'Cold Stress',
  unknown_deaths: 'Unknown',
  other_deaths: 'Other',
};

export const MortalityEntryForm: React.FC<MortalityEntryFormProps> = ({
  flockId,
  houseId,
  onSuccess,
  onCancel,
  compact = false,
}) => {
  const [formData, setFormData] = useState<MortalityRecordCreate>({
    flock: flockId,
    house: houseId,
    record_date: new Date().toISOString().split('T')[0],
    total_deaths: 0,
    disease_deaths: 0,
    culling_deaths: 0,
    accident_deaths: 0,
    heat_stress_deaths: 0,
    cold_stress_deaths: 0,
    unknown_deaths: 0,
    other_deaths: 0,
    notes: '',
  });

  const [showBreakdown, setShowBreakdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (field: keyof MortalityRecordCreate) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = field === 'notes' || field === 'record_date'
      ? e.target.value
      : parseInt(e.target.value) || 0;
    
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
    setSuccess(false);
  };

  const breakdownTotal = 
    (formData.disease_deaths || 0) +
    (formData.culling_deaths || 0) +
    (formData.accident_deaths || 0) +
    (formData.heat_stress_deaths || 0) +
    (formData.cold_stress_deaths || 0) +
    (formData.unknown_deaths || 0) +
    (formData.other_deaths || 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.total_deaths <= 0) {
      setError('Please enter the number of deaths');
      return;
    }

    if (showBreakdown && breakdownTotal > formData.total_deaths) {
      setError('Breakdown total cannot exceed total deaths');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await mortalityApi.createRecord(formData);
      setSuccess(true);
      
      // Reset form
      setFormData(prev => ({
        ...prev,
        total_deaths: 0,
        disease_deaths: 0,
        culling_deaths: 0,
        accident_deaths: 0,
        heat_stress_deaths: 0,
        cold_stress_deaths: 0,
        unknown_deaths: 0,
        other_deaths: 0,
        notes: '',
      }));
      
      onSuccess?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.error || 'Failed to record mortality');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickEntry = async () => {
    if (formData.total_deaths <= 0) {
      setError('Please enter the number of deaths');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await mortalityApi.quickEntry({
        flock_id: flockId,
        house_id: houseId,
        total_deaths: formData.total_deaths,
        record_date: formData.record_date,
        notes: formData.notes,
      });
      setSuccess(true);
      
      // Reset form
      setFormData(prev => ({
        ...prev,
        total_deaths: 0,
        notes: '',
      }));
      
      onSuccess?.();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.response?.data?.error || 'Failed to record mortality');
    } finally {
      setLoading(false);
    }
  };

  if (compact) {
    return (
      <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <TextField
          size="small"
          type="number"
          label="Deaths"
          value={formData.total_deaths || ''}
          onChange={handleChange('total_deaths')}
          inputProps={{ min: 0 }}
          sx={{ width: 100 }}
        />
        <Button
          variant="contained"
          color="error"
          size="small"
          startIcon={loading ? <CircularProgress size={16} /> : <AddIcon />}
          onClick={handleQuickEntry}
          disabled={loading || formData.total_deaths <= 0}
        >
          Record
        </Button>
      </Box>
    );
  }

  return (
    <Card elevation={2}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          📊 Record Mortality
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(false)}>
            Mortality recorded successfully!
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="date"
                label="Date"
                value={formData.record_date}
                onChange={handleChange('record_date')}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Total Deaths"
                value={formData.total_deaths || ''}
                onChange={handleChange('total_deaths')}
                inputProps={{ min: 0 }}
                required
                InputProps={{
                  endAdornment: <InputAdornment position="end">birds</InputAdornment>,
                }}
              />
            </Grid>
          </Grid>

          <Box sx={{ mt: 2 }}>
            <Button
              size="small"
              onClick={() => setShowBreakdown(!showBreakdown)}
              endIcon={showBreakdown ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            >
              {showBreakdown ? 'Hide' : 'Show'} Detailed Breakdown
            </Button>
          </Box>

          <Collapse in={showBreakdown}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Breakdown by Cause (optional)
            </Typography>
            <Grid container spacing={2}>
              {Object.entries(CAUSE_LABELS).map(([field, label]) => (
                <Grid item xs={6} sm={4} md={3} key={field}>
                  <TextField
                    fullWidth
                    size="small"
                    type="number"
                    label={label}
                    value={(formData as any)[field] || ''}
                    onChange={handleChange(field as keyof MortalityRecordCreate)}
                    inputProps={{ min: 0 }}
                  />
                </Grid>
              ))}
            </Grid>
            {breakdownTotal > 0 && (
              <Typography
                variant="body2"
                color={breakdownTotal > formData.total_deaths ? 'error' : 'text.secondary'}
                sx={{ mt: 1 }}
              >
                Breakdown total: {breakdownTotal} / {formData.total_deaths}
                {breakdownTotal > formData.total_deaths && ' (exceeds total)'}
              </Typography>
            )}
          </Collapse>

          <TextField
            fullWidth
            multiline
            rows={2}
            label="Notes"
            value={formData.notes}
            onChange={handleChange('notes')}
            placeholder="Any additional observations..."
            sx={{ mt: 2 }}
          />

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            {onCancel && (
              <Button onClick={onCancel} disabled={loading}>
                Cancel
              </Button>
            )}
            <Button
              variant="outlined"
              onClick={handleQuickEntry}
              disabled={loading || formData.total_deaths <= 0}
            >
              Quick Entry
            </Button>
            <Button
              type="submit"
              variant="contained"
              color="error"
              startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
              disabled={loading || formData.total_deaths <= 0}
            >
              Save Record
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default MortalityEntryForm;

