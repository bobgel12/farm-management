import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Avatar,
  ListItemIcon,
  ListItemText,
  Divider,
  Paper,
  Menu,
  MenuItem as MenuItemComponent,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Agriculture as FarmIcon,
  LocationOn as LocationIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Visibility as ViewIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useFarm } from '../../contexts/FarmContext';
import { useProgram } from '../../contexts/ProgramContext';

interface FarmCardProps {
  farm: any;
  onEdit: (_farm: any) => void;
  onDelete: (_farm: any) => void;
  onView: (_farm: any) => void;
}

const FarmCard: React.FC<FarmCardProps> = ({ farm, onEdit, onDelete, onView }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleViewDetails = () => {
    onView(farm);
    handleMenuClose();
  };

  const handleEdit = () => {
    onEdit(farm);
    handleMenuClose();
  };

  const handleDelete = () => {
    onDelete(farm);
    handleMenuClose();
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* Status Badge */}
      <Box position="absolute" top={16} right={16}>
        <Chip
          icon={farm.is_active ? <CheckCircleIcon /> : <WarningIcon />}
          label={farm.is_active ? 'Active' : 'Inactive'}
          color={farm.is_active ? 'success' : 'default'}
          size="small"
        />
      </Box>

      <CardContent sx={{ flexGrow: 1, pb: 1 }}>
        {/* Farm Header */}
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
            <FarmIcon />
          </Avatar>
          <Box flex={1}>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              {farm.name}
            </Typography>
            <Box display="flex" alignItems="center" gap={1}>
              <LocationIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                {farm.location}
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Contact Info */}
        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Contact Person
          </Typography>
          <Typography variant="body1" fontWeight={500} gutterBottom>
            {farm.contact_person}
          </Typography>
          <Box display="flex" alignItems="center" gap={1} mb={0.5}>
            <PhoneIcon fontSize="small" color="action" />
            <Typography variant="body2" color="text.secondary">
              {farm.contact_phone}
            </Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <EmailIcon fontSize="small" color="action" />
            <Typography variant="body2" color="text.secondary">
              {farm.contact_email}
            </Typography>
          </Box>
        </Box>

        {/* Statistics */}
        <Box display="flex" gap={2} mb={2}>
          <Box textAlign="center" flex={1}>
            <Typography variant="h6" fontWeight={600} color="primary">
              {farm.total_houses}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Houses
            </Typography>
          </Box>
          <Box textAlign="center" flex={1}>
            <Typography variant="h6" fontWeight={600} color="secondary">
              {farm.active_houses}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Active
            </Typography>
          </Box>
          <Box textAlign="center" flex={1}>
            <Typography variant="h6" fontWeight={600} color="success">
              {farm.workers?.length || 0}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Workers
            </Typography>
          </Box>
        </Box>

        {/* Program Info */}
        {farm.program && (
          <Box mb={2}>
            <Chip
              icon={<ScheduleIcon />}
              label={farm.program.name}
              size="small"
              variant="outlined"
              color="info"
            />
          </Box>
        )}
      </CardContent>

      {/* Actions */}
      <Box sx={{ p: 2, pt: 0 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Button
            variant="outlined"
            size="small"
            startIcon={<ViewIcon />}
            onClick={() => onView(farm)}
            sx={{ textTransform: 'none' }}
          >
            View Details
          </Button>
          
          <IconButton onClick={handleMenuOpen} size="small">
            <MoreVertIcon />
          </IconButton>
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <MenuItemComponent onClick={handleViewDetails}>
            <ListItemIcon>
              <ViewIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>View Details</ListItemText>
          </MenuItemComponent>
          <MenuItemComponent onClick={handleEdit}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Edit Farm</ListItemText>
          </MenuItemComponent>
          <Divider />
          <MenuItemComponent onClick={handleDelete} sx={{ color: 'error.main' }}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Delete Farm</ListItemText>
          </MenuItemComponent>
        </Menu>
      </Box>
    </Card>
  );
};

const ProfessionalFarmList: React.FC = () => {
  const { farms, loading, error, fetchFarms, createFarm, updateFarm, deleteFarm } = useFarm();
  const { programs, fetchPrograms } = useProgram();
  const navigate = useNavigate();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingFarm, setEditingFarm] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    program_id: '',
    is_active: true,
  });

  useEffect(() => {
    fetchFarms();
    fetchPrograms();
  }, [fetchFarms, fetchPrograms]);

  const handleOpenDialog = (farm?: any) => {
    if (farm) {
      setEditingFarm(farm);
      setFormData({
        name: farm.name,
        location: farm.location,
        contact_person: farm.contact_person,
        contact_phone: farm.contact_phone,
        contact_email: farm.contact_email,
        program_id: farm.program?.id || '',
        is_active: farm.is_active,
      });
    } else {
      setEditingFarm(null);
      setFormData({
        name: '',
        location: '',
        contact_person: '',
        contact_phone: '',
        contact_email: '',
        program_id: '',
        is_active: true,
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingFarm(null);
  };

  const handleSubmit = async () => {
    const success = editingFarm
      ? await updateFarm(editingFarm.id, formData)
      : await createFarm(formData);

    if (success) {
      handleCloseDialog();
      fetchFarms();
    }
  };

  const handleDelete = async (farm: any) => {
    if (window.confirm(`Are you sure you want to delete "${farm.name}"?`)) {
      const success = await deleteFarm(farm.id);
      if (success) {
        fetchFarms();
      }
    }
  };

  const handleView = (farm: any) => {
    navigate(`/farms/${farm.id}`);
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
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" fontWeight={700} color="text.primary" gutterBottom>
            Farm Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your farms, houses, and operations
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
          sx={{ textTransform: 'none' }}
        >
          Add New Farm
        </Button>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Farms Grid */}
      {farms.length === 0 ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Avatar sx={{ bgcolor: 'grey.100', width: 64, height: 64, mx: 'auto', mb: 2 }}>
            <FarmIcon fontSize="large" color="action" />
          </Avatar>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No farms found
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Get started by adding your first farm to the system.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ textTransform: 'none' }}
          >
            Add Your First Farm
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {farms.map((farm) => (
            <Grid item xs={12} sm={6} lg={4} key={farm.id}>
              <FarmCard
                farm={farm}
                onEdit={handleOpenDialog}
                onDelete={handleDelete}
                onView={handleView}
              />
            </Grid>
          ))}
        </Grid>
      )}

      {/* Farm Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingFarm ? 'Edit Farm' : 'Add New Farm'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Farm Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Location"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Contact Person"
                value={formData.contact_person}
                onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.contact_phone}
                onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.contact_email}
                onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Task Program</InputLabel>
                <Select
                  value={formData.program_id}
                  onChange={(e) => setFormData({ ...formData, program_id: e.target.value })}
                >
                  <MenuItem value="">No Program</MenuItem>
                  {programs.map((program) => (
                    <MenuItem key={program.id} value={program.id}>
                      {program.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                }
                label="Active Farm"
              />
            </Grid>
          </Grid>
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

export default ProfessionalFarmList;
