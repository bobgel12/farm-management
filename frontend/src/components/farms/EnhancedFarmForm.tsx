import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Card,
  CardContent,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Chip,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  CheckCircle,
  Error,
  Settings,
  IntegrationInstructions,
} from '@mui/icons-material';

interface FarmFormData {
  // Basic farm information
  name: string;
  location: string;
  description: string;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  
  // Integration selection
  integration_type: 'none' | 'rotem' | 'future_system';
  
  // Rotem credentials (only if integration_type='rotem')
  rotem_credentials?: {
    username: string;
    password: string;
  };
}

interface EnhancedFarmFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: FarmFormData) => void;
  editingFarm?: any;
  loading?: boolean;
}

const EnhancedFarmForm: React.FC<EnhancedFarmFormProps> = ({
  open,
  onClose,
  onSubmit,
  editingFarm,
  loading = false,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [formData, setFormData] = useState<FarmFormData>({
    name: '',
    location: '',
    description: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    integration_type: 'none',
    rotem_credentials: {
      username: '',
      password: '',
    },
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [connectionError, setConnectionError] = useState('');

  const steps = ['Basic Information', 'System Integration', 'Review & Create'];

  useEffect(() => {
    if (editingFarm) {
      setFormData({
        name: editingFarm.name || '',
        location: editingFarm.location || '',
        description: editingFarm.description || '',
        contact_person: editingFarm.contact_person || '',
        contact_phone: editingFarm.contact_phone || '',
        contact_email: editingFarm.contact_email || '',
        integration_type: editingFarm.integration_type || 'none',
        rotem_credentials: {
          username: editingFarm.rotem_username || '',
          password: editingFarm.rotem_password || '',
        },
      });
    } else {
      setFormData({
        name: '',
        location: '',
        description: '',
        contact_person: '',
        contact_phone: '',
        contact_email: '',
        integration_type: 'none',
        rotem_credentials: {
          username: '',
          password: '',
        },
      });
    }
    setActiveStep(0);
    setConnectionStatus('idle');
    setConnectionError('');
  }, [editingFarm, open]);

  const handleInputChange = (field: keyof FarmFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleRotemCredentialChange = (field: 'username' | 'password', value: string) => {
    setFormData(prev => ({
      ...prev,
      rotem_credentials: {
        ...prev.rotem_credentials!,
        [field]: value,
      },
    }));
  };

  const handleNext = () => {
    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const testRotemConnection = async () => {
    if (!formData.rotem_credentials?.username || !formData.rotem_credentials?.password) {
      setConnectionError('Please enter both username and password');
      setConnectionStatus('error');
      return;
    }

    setTestingConnection(true);
    setConnectionStatus('testing');
    setConnectionError('');

    try {
      // Test connection with temporary credentials
      const testData = {
        ...formData,
        rotem_username: formData.rotem_credentials.username,
        rotem_password: formData.rotem_credentials.password,
      };

      const response = await fetch(`/api/farms/${editingFarm?.id || 'test'}/configure_integration/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          integration_type: 'rotem',
          username: formData.rotem_credentials.username,
          password: formData.rotem_credentials.password,
        }),
      });

      if (response.ok) {
        setConnectionStatus('success');
        setConnectionError('');
      } else {
        const errorData = await response.json();
        setConnectionError(errorData.error || 'Connection failed');
        setConnectionStatus('error');
      }
    } catch (error) {
      setConnectionError('Connection test failed');
      setConnectionStatus('error');
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSubmit = () => {
    onSubmit(formData);
  };

  const isStepValid = (step: number) => {
    switch (step) {
      case 0:
        return formData.name && formData.location && formData.contact_person && formData.contact_email;
      case 1:
        if (formData.integration_type === 'rotem') {
          return formData.rotem_credentials?.username && formData.rotem_credentials?.password;
        }
        return true;
      case 2:
        return true;
      default:
        return false;
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Farm Name"
              fullWidth
              required
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              InputProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
              InputLabelProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
            />
            <TextField
              label="Location"
              fullWidth
              required
              value={formData.location}
              onChange={(e) => handleInputChange('location', e.target.value)}
              InputProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
              InputLabelProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              placeholder="Optional description of the farm"
              InputProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
              InputLabelProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
            />
            <TextField
              label="Contact Person"
              fullWidth
              required
              value={formData.contact_person}
              onChange={(e) => handleInputChange('contact_person', e.target.value)}
              InputProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
              InputLabelProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
            />
            <TextField
              label="Contact Phone"
              fullWidth
              value={formData.contact_phone}
              onChange={(e) => handleInputChange('contact_phone', e.target.value)}
              InputProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
              InputLabelProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
            />
            <TextField
              label="Contact Email"
              fullWidth
              required
              type="email"
              value={formData.contact_email}
              onChange={(e) => handleInputChange('contact_email', e.target.value)}
              InputProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
              InputLabelProps={{
                sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
              }}
            />
          </Box>
        );

      case 1:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <FormControl component="fieldset">
              <FormLabel component="legend" sx={{ fontSize: '1.1rem', fontWeight: 600, mb: 2 }}>
                System Integration
              </FormLabel>
              <RadioGroup
                value={formData.integration_type}
                onChange={(e) => handleInputChange('integration_type', e.target.value)}
              >
                <FormControlLabel
                  value="none"
                  control={<Radio />}
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Settings color="action" />
                      <Box>
                        <Typography variant="body1" fontWeight={500}>
                          No Integration (Manual Management)
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Manage your farm manually without external system integration
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
                <FormControlLabel
                  value="rotem"
                  control={<Radio />}
                  label={
                    <Box display="flex" alignItems="center" gap={1}>
                      <IntegrationInstructions color="primary" />
                      <Box>
                        <Typography variant="body1" fontWeight={500}>
                          Rotem System Integration
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          Connect to Rotem monitoring system for automated data collection
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>

            {formData.integration_type === 'rotem' && (
              <Card sx={{ mt: 2, p: 2, border: '1px solid', borderColor: 'primary.main' }}>
                <Typography variant="h6" gutterBottom>
                  Rotem System Configuration
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="Rotem Username"
                    fullWidth
                    value={formData.rotem_credentials?.username || ''}
                    onChange={(e) => handleRotemCredentialChange('username', e.target.value)}
                    InputProps={{
                      sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
                    }}
                    InputLabelProps={{
                      sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
                    }}
                  />
                  <TextField
                    label="Rotem Password"
                    fullWidth
                    type={showPassword ? 'text' : 'password'}
                    value={formData.rotem_credentials?.password || ''}
                    onChange={(e) => handleRotemCredentialChange('password', e.target.value)}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            onClick={() => setShowPassword(!showPassword)}
                            edge="end"
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      ),
                      sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
                    }}
                    InputLabelProps={{
                      sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
                    }}
                  />
                  <Button
                    variant="outlined"
                    onClick={testRotemConnection}
                    disabled={testingConnection || !formData.rotem_credentials?.username || !formData.rotem_credentials?.password}
                    startIcon={
                      testingConnection ? (
                        <CircularProgress size={20} />
                      ) : connectionStatus === 'success' ? (
                        <CheckCircle color="success" />
                      ) : connectionStatus === 'error' ? (
                        <Error color="error" />
                      ) : null
                    }
                    sx={{ alignSelf: 'flex-start' }}
                  >
                    {testingConnection ? 'Testing...' : 'Test Connection'}
                  </Button>
                  {connectionError && (
                    <Alert severity="error" sx={{ mt: 1 }}>
                      {connectionError}
                    </Alert>
                  )}
                  {connectionStatus === 'success' && (
                    <Alert severity="success" sx={{ mt: 1 }}>
                      Connection successful! You can proceed to create the farm.
                    </Alert>
                  )}
                </Box>
              </Card>
            )}
          </Box>
        );

      case 2:
        return (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="h6" gutterBottom>
              Review Farm Details
            </Typography>
            <Card sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Basic Information
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                <Typography><strong>Name:</strong> {formData.name}</Typography>
                <Typography><strong>Location:</strong> {formData.location}</Typography>
                <Typography><strong>Description:</strong> {formData.description || 'None'}</Typography>
                <Typography><strong>Contact Person:</strong> {formData.contact_person}</Typography>
                <Typography><strong>Contact Phone:</strong> {formData.contact_phone || 'None'}</Typography>
                <Typography><strong>Contact Email:</strong> {formData.contact_email}</Typography>
              </Box>
              
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                System Integration
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={formData.integration_type === 'none' ? 'Manual Management' : 'Rotem Integration'}
                  color={formData.integration_type === 'none' ? 'default' : 'primary'}
                  icon={formData.integration_type === 'none' ? <Settings /> : <IntegrationInstructions />}
                />
                {formData.integration_type === 'rotem' && connectionStatus === 'success' && (
                  <Chip
                    label="Connection Verified"
                    color="success"
                    icon={<CheckCircle />}
                    size="small"
                  />
                )}
              </Box>
            </Card>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          maxHeight: { xs: '95vh', sm: '90vh' },
          minHeight: { xs: '80vh', sm: '70vh' }
        }
      }}
    >
      <DialogTitle sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' }, fontWeight: 600 }}>
        {editingFarm ? 'Edit Farm' : 'Add New Farm'}
      </DialogTitle>
      
      <DialogContent sx={{ p: { xs: 2, sm: 3 } }}>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {renderStepContent(activeStep)}
      </DialogContent>
      
      <DialogActions sx={{ p: { xs: 2, sm: 3 }, gap: 1 }}>
        <Button 
          onClick={activeStep === 0 ? onClose : handleBack}
          sx={{ 
            fontSize: { xs: '0.875rem', sm: '0.875rem' },
            minHeight: { xs: 44, sm: 36 }
          }}
        >
          {activeStep === 0 ? 'Cancel' : 'Back'}
        </Button>
        
        {activeStep < steps.length - 1 ? (
          <Button 
            onClick={handleNext}
            variant="contained"
            disabled={!isStepValid(activeStep)}
            sx={{ 
              fontSize: { xs: '0.875rem', sm: '0.875rem' },
              minHeight: { xs: 44, sm: 36 }
            }}
          >
            Next
          </Button>
        ) : (
          <Button 
            onClick={handleSubmit}
            variant="contained"
            disabled={loading || (formData.integration_type === 'rotem' && connectionStatus !== 'success')}
            sx={{ 
              fontSize: { xs: '0.875rem', sm: '0.875rem' },
              minHeight: { xs: 44, sm: 36 }
            }}
          >
            {loading ? <CircularProgress size={20} /> : (editingFarm ? 'Update Farm' : 'Create Farm')}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default EnhancedFarmForm;
