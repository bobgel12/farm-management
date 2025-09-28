import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Alert,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Close,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { useRotem } from '../../contexts/RotemContext';
import { AddFarmFormData } from '../../types/rotem';

interface AddFarmDialogProps {
  open: boolean;
  onClose: () => void;
}

const AddFarmDialog: React.FC<AddFarmDialogProps> = ({ open, onClose }) => {
  const { addFarm, state } = useRotem();
  const [formData, setFormData] = useState<AddFarmFormData>({
    farm_name: '',
    gateway_name: '',
    username: '',
    password: '',
    gateway_alias: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Partial<AddFarmFormData>>({});

  const handleInputChange = (field: keyof AddFarmFormData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: event.target.value,
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<AddFarmFormData> = {};

    if (!formData.farm_name.trim()) {
      newErrors.farm_name = 'Farm name is required';
    }

    if (!formData.gateway_name.trim()) {
      newErrors.gateway_name = 'Gateway name is required';
    }

    if (!formData.username.trim()) {
      newErrors.username = 'Username is required';
    }

    if (!formData.password.trim()) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      await addFarm({
        ...formData,
        gateway_alias: formData.gateway_alias || formData.farm_name,
      });
      
      // Reset form
      setFormData({
        farm_name: '',
        gateway_name: '',
        username: '',
        password: '',
        gateway_alias: '',
      });
      setErrors({});
      onClose();
    } catch (error) {
      // Error is handled by the context
    }
  };

  const handleClose = () => {
    setFormData({
      farm_name: '',
      gateway_name: '',
      username: '',
      password: '',
      gateway_alias: '',
    });
    setErrors({});
    onClose();
  };

  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Add New Farm
          <IconButton onClick={handleClose} size="small">
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="Farm Name"
            value={formData.farm_name}
            onChange={handleInputChange('farm_name')}
            error={!!errors.farm_name}
            helperText={errors.farm_name}
            fullWidth
            required
          />
          
          <TextField
            label="Gateway Name"
            value={formData.gateway_name}
            onChange={handleInputChange('gateway_name')}
            error={!!errors.gateway_name}
            helperText={errors.gateway_name || 'Unique identifier for the farm gateway'}
            fullWidth
            required
          />
          
          <TextField
            label="Gateway Alias"
            value={formData.gateway_alias}
            onChange={handleInputChange('gateway_alias')}
            helperText="Optional display name (defaults to farm name)"
            fullWidth
          />
          
          <TextField
            label="Rotem Username"
            value={formData.username}
            onChange={handleInputChange('username')}
            error={!!errors.username}
            helperText={errors.username}
            fullWidth
            required
          />
          
          <TextField
            label="Rotem Password"
            type={showPassword ? 'text' : 'password'}
            value={formData.password}
            onChange={handleInputChange('password')}
            error={!!errors.password}
            helperText={errors.password}
            fullWidth
            required
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={togglePasswordVisibility}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          
          <Alert severity="info" sx={{ mt: 2 }}>
            <strong>Note:</strong> The farm will be automatically scraped after creation to collect initial data.
          </Alert>
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ p: 3, pt: 1 }}>
        <Button onClick={handleClose} disabled={state.loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={state.loading}
        >
          {state.loading ? 'Adding...' : 'Add Farm'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddFarmDialog;
