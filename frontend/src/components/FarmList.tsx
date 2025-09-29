import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  IconButton,
  Alert,
  CircularProgress,
  Chip,
  Dialog,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Home as HomeIcon,
  Settings,
  IntegrationInstructions,
  CheckCircle,
  Error,
  Warning,
} from '@mui/icons-material';
import { useFarm } from '../contexts/FarmContext';
import EnhancedFarmForm from './farms/EnhancedFarmForm';
import UnifiedFarmDashboard from './farms/UnifiedFarmDashboard';
import IntegrationManagement from './farms/IntegrationManagement';

const FarmList: React.FC = () => {
  const navigate = useNavigate();
  const { farms, loading, error, fetchFarms, createFarm, updateFarm, deleteFarm } = useFarm();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingFarm, setEditingFarm] = useState<any>(null);
  const [selectedFarm, setSelectedFarm] = useState<any>(null);
  const [integrationDialogOpen, setIntegrationDialogOpen] = useState(false);
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    fetchFarms();
  }, [fetchFarms]);

  const handleOpenDialog = (farm?: any) => {
    setEditingFarm(farm || null);
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingFarm(null);
  };

  const handleSubmit = async (formData: any) => {
    setFormLoading(true);
    try {
      if (editingFarm) {
        await updateFarm(editingFarm.id, formData);
      } else {
        await createFarm(formData);
      }
      handleCloseDialog();
    } catch (error) {
      console.error('Error saving farm:', error);
    } finally {
      setFormLoading(false);
    }
  };

  const handleFarmClick = (farm: any) => {
    setSelectedFarm(farm);
  };

  const handleConfigureIntegration = (farmId: number) => {
    const farm = farms.find(f => f.id === farmId);
    if (farm) {
      setSelectedFarm(farm);
      setIntegrationDialogOpen(true);
    }
  };

  const handleUpdateIntegration = async (farmId: number, integrationData: any) => {
    try {
      const response = await fetch(`/api/farms/${farmId}/configure_integration/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(integrationData),
      });
      
      if (response.ok) {
        await fetchFarms(); // Refresh farms list
        setIntegrationDialogOpen(false);
      } else {
        throw new Error('Failed to update integration');
      }
    } catch (error) {
      console.error('Error updating integration:', error);
      throw error;
    }
  };

  const handleTestConnection = async (farmId: number): Promise<boolean> => {
    try {
      const response = await fetch(`/api/farms/${farmId}/test_connection/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });
      return response.ok;
    } catch (error) {
      console.error('Error testing connection:', error);
      return false;
    }
  };

  const handleSyncData = async (farmId: number) => {
    try {
      const response = await fetch(`/api/farms/${farmId}/sync_data/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        await fetchFarms(); // Refresh farms list
      } else {
        throw new Error('Failed to sync data');
      }
    } catch (error) {
      console.error('Error syncing data:', error);
      throw error;
    }
  };

  const handleDelete = async (farmId: number) => {
    if (window.confirm('Are you sure you want to delete this farm?')) {
      await deleteFarm(farmId);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box 
        display="flex" 
        justifyContent="space-between" 
        alignItems={{ xs: 'flex-start', sm: 'center' }} 
        mb={3}
        flexDirection={{ xs: 'column', sm: 'row' }}
        gap={{ xs: 2, sm: 0 }}
      >
        <Typography 
          variant="h4"
          sx={{ 
            fontSize: { xs: '1.75rem', sm: '2.125rem' },
            fontWeight: 600
          }}
        >
          Farms
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          sx={{
            minHeight: { xs: 48, sm: 36 },
            fontSize: { xs: '0.875rem', sm: '0.875rem' },
            width: { xs: '100%', sm: 'auto' }
          }}
        >
          Add Farm
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {Array.isArray(farms) && farms.length > 0 ? (
        <Grid container spacing={{ xs: 2, sm: 3 }}>
          {farms.map((farm) => (
            <Grid item xs={12} sm={6} md={4} key={farm.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ p: { xs: 2, sm: 3 }, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography 
                      variant="h6" 
                      component="div"
                      sx={{ 
                        fontSize: { xs: '1.1rem', sm: '1.25rem' },
                        fontWeight: 600,
                        pr: 1
                      }}
                    >
                      {farm.name}
                    </Typography>
                    <Box display="flex" gap={0.5}>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(farm)}
                        sx={{ minWidth: 32, minHeight: 32 }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(farm.id)}
                        color="error"
                        sx={{ minWidth: 32, minHeight: 32 }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>
                  
                  <Typography 
                    color="textSecondary" 
                    gutterBottom
                    sx={{ 
                      fontSize: { xs: '0.875rem', sm: '1rem' },
                      mb: 2
                    }}
                  >
                    {farm.location}
                  </Typography>
                  
                  <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                    <Chip
                      label={`${farm.active_houses || 0} Active`}
                      color="primary"
                      size="small"
                      sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                    />
                    <Chip
                      label={`${farm.total_houses || 0} Total`}
                      variant="outlined"
                      size="small"
                      sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                    />
                    <Chip
                      label={farm.integration_type === 'none' ? 'Manual' : 'Integrated'}
                      color={farm.integration_type === 'none' ? 'default' : 'primary'}
                      icon={farm.integration_type === 'none' ? <Settings /> : <IntegrationInstructions />}
                      size="small"
                      sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                    />
                    {farm.has_system_integration && (
                      <Chip
                        label={farm.integration_status}
                        color={
                          farm.integration_status === 'active' ? 'success' :
                          farm.integration_status === 'error' ? 'error' :
                          farm.integration_status === 'inactive' ? 'warning' : 'default'
                        }
                        icon={
                          farm.integration_status === 'active' ? <CheckCircle /> :
                          farm.integration_status === 'error' ? <Error /> :
                          farm.integration_status === 'inactive' ? <Warning /> : <Settings />
                        }
                        size="small"
                        sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                      />
                    )}
                  </Box>
                  
                  <Box display="flex" gap={1} mt="auto" flexWrap="wrap">
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<HomeIcon />}
                      onClick={() => handleFarmClick(farm)}
                      sx={{ 
                        fontSize: { xs: '0.75rem', sm: '0.875rem' },
                        minHeight: { xs: 40, sm: 32 }
                      }}
                    >
                      View Dashboard
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<Settings />}
                      onClick={() => handleConfigureIntegration(farm.id)}
                      sx={{ 
                        fontSize: { xs: '0.75rem', sm: '0.875rem' },
                        minHeight: { xs: 40, sm: 32 }
                      }}
                    >
                      Configure
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Box textAlign="center" py={4}>
          <Typography variant="h6" color="textSecondary" gutterBottom>
            No farms found
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Click &quot;Add Farm&quot; to create your first farm
          </Typography>
        </Box>
      )}

      {/* Enhanced Farm Form Dialog */}
      <EnhancedFarmForm
        open={dialogOpen}
        onClose={handleCloseDialog}
        onSubmit={handleSubmit}
        editingFarm={editingFarm}
        loading={formLoading}
      />

      {/* Farm Dashboard Dialog */}
      {selectedFarm && (
        <Dialog
          open={!!selectedFarm}
          onClose={() => setSelectedFarm(null)}
          maxWidth="lg"
          fullWidth
          PaperProps={{
            sx: {
              maxHeight: '90vh',
              minHeight: '70vh'
            }
          }}
        >
          <UnifiedFarmDashboard
            farm={selectedFarm}
            onRefresh={fetchFarms}
            onConfigureIntegration={handleConfigureIntegration}
            onSyncData={handleSyncData}
          />
        </Dialog>
      )}

      {/* Integration Management Dialog */}
      {selectedFarm && (
        <IntegrationManagement
          open={integrationDialogOpen}
          onClose={() => setIntegrationDialogOpen(false)}
          farm={selectedFarm}
          onUpdateIntegration={handleUpdateIntegration}
          onTestConnection={handleTestConnection}
          onSyncData={handleSyncData}
        />
      )}
    </Box>
  );
};

export default FarmList;
