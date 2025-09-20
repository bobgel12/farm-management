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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import { useFarm } from '../contexts/FarmContext.tsx';

const FarmList: React.FC = () => {
  const navigate = useNavigate();
  const { farms, loading, error, fetchFarms, createFarm, updateFarm, deleteFarm } = useFarm();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingFarm, setEditingFarm] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
  });

  useEffect(() => {
    fetchFarms();
  }, []);

  const handleOpenDialog = (farm?: any) => {
    if (farm) {
      setEditingFarm(farm);
      setFormData({
        name: farm.name,
        location: farm.location,
        contact_person: farm.contact_person,
        contact_phone: farm.contact_phone,
        contact_email: farm.contact_email,
      });
    } else {
      setEditingFarm(null);
      setFormData({
        name: '',
        location: '',
        contact_person: '',
        contact_phone: '',
        contact_email: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingFarm(null);
    setFormData({
      name: '',
      location: '',
      contact_person: '',
      contact_phone: '',
      contact_email: '',
    });
  };

  const handleSubmit = async () => {
    if (editingFarm) {
      const success = await updateFarm(editingFarm.id, formData);
      if (success) {
        handleCloseDialog();
      }
    } else {
      const success = await createFarm(formData);
      if (success) {
        handleCloseDialog();
      }
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Farms</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
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
        <Grid container spacing={3}>
          {farms.map((farm) => (
            <Grid item xs={12} sm={6} md={4} key={farm.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" component="div">
                      {farm.name}
                    </Typography>
                    <Box>
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(farm)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(farm.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Box>
                  
                  <Typography color="textSecondary" gutterBottom>
                    {farm.location}
                  </Typography>
                  
                  <Box display="flex" gap={1} mb={2}>
                    <Chip
                      label={`${farm.active_houses || 0} Active`}
                      color="primary"
                      size="small"
                    />
                    <Chip
                      label={`${farm.total_houses || 0} Total`}
                      variant="outlined"
                      size="small"
                    />
                  </Box>
                  
                  <Box display="flex" gap={1}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<HomeIcon />}
                      onClick={() => navigate(`/farms/${farm.id}`)}
                    >
                      View Houses
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
            Click "Add Farm" to create your first farm
          </Typography>
        </Box>
      )}

      {/* Add/Edit Farm Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingFarm ? 'Edit Farm' : 'Add New Farm'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Farm Name"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Location"
            fullWidth
            variant="outlined"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Contact Person"
            fullWidth
            variant="outlined"
            value={formData.contact_person}
            onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Contact Phone"
            fullWidth
            variant="outlined"
            value={formData.contact_phone}
            onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Contact Email"
            fullWidth
            variant="outlined"
            type="email"
            value={formData.contact_email}
            onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingFarm ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FarmList;
