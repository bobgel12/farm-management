import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  FormControlLabel,
  Switch,
  CircularProgress,
  Grid,
} from '@mui/material';
import { useWorker } from '../contexts/WorkerContext';

interface WorkerFormProps {
  open: boolean;
  onClose: () => void;
  farmId: number;
  farmName: string;
  worker?: any;
  onSuccess?: () => void;
}

const WorkerForm: React.FC<WorkerFormProps> = ({
  open,
  onClose,
  farmId,
  farmName,
  worker,
  onSuccess,
}) => {
  const { createWorker, updateWorker, loading } = useWorker();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    role: '',
    is_active: true,
    receive_daily_tasks: true,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (worker) {
      setFormData({
        name: worker.name || '',
        email: worker.email || '',
        phone: worker.phone || '',
        role: worker.role || '',
        is_active: worker.is_active ?? true,
        receive_daily_tasks: worker.receive_daily_tasks ?? true,
      });
    } else {
      setFormData({
        name: '',
        email: '',
        phone: '',
        role: '',
        is_active: true,
        receive_daily_tasks: true,
      });
    }
    setErrors({});
  }, [worker, open]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (formData.phone && !/^[+]?[1-9][\d]{0,15}$/.test(formData.phone.replace(/\D/g, ''))) {
      newErrors.phone = 'Please enter a valid phone number';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    const workerData = {
      ...formData,
      farm_id: farmId,
    };

    const success = worker 
      ? await updateWorker(worker.id, workerData)
      : await createWorker(workerData);

    if (success) {
      onSuccess?.();
      onClose();
    }
  };

  const handleChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {worker ? 'Edit Worker' : 'Add New Worker'} - {farmName}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 1 }}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={handleChange('name')}
                error={!!errors.name}
                helperText={errors.name}
                required
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={handleChange('email')}
                error={!!errors.email}
                helperText={errors.email}
                required
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={handleChange('phone')}
                error={!!errors.phone}
                helperText={errors.phone || 'Optional'}
                placeholder="+1-555-123-4567"
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Role"
                value={formData.role}
                onChange={handleChange('role')}
                helperText="e.g., Manager, Supervisor, Worker"
                placeholder="Worker"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Box display="flex" flexDirection="column" gap={1}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_active}
                      onChange={handleChange('is_active')}
                    />
                  }
                  label="Active Worker"
                />
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.receive_daily_tasks}
                      onChange={handleChange('receive_daily_tasks')}
                    />
                  }
                  label="Receive Daily Task Emails"
                />
              </Box>
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Saving...' : (worker ? 'Update' : 'Add')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default WorkerForm;
