import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  ListItemText,
  ListItemIcon,
  Divider,
  Avatar,
  IconButton,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Menu,
  MenuItem as MenuItemComponent,
} from '@mui/material';
import {
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Search as SearchIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { useWorker } from '../../contexts/WorkerContext';
import api from '../../services/api';

const ProfessionalWorkerList: React.FC = () => {
  const { farmId } = useParams<{ farmId: string }>();
  const [farm, setFarm] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [workerDialogOpen, setWorkerDialogOpen] = useState(false);
  const [editingWorker, setEditingWorker] = useState<any>(null);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedWorker, setSelectedWorker] = useState<any>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    role: '',
    is_active: true,
    receive_daily_tasks: true,
  });
  const { workers, fetchWorkers, createWorker, updateWorker, deleteWorker } = useWorker();

  const fetchFarmDetails = useCallback(async () => {
    if (farmId) {
      try {
        const response = await api.get(`/farms/${farmId}/`);
        setFarm(response.data);
      } catch (err) {
        setError('Failed to fetch farm details');
      }
    }
    setLoading(false);
  }, [farmId]);

  useEffect(() => {
    fetchFarmDetails();
    if (farmId) {
      fetchWorkers(parseInt(farmId));
    }
  }, [farmId, fetchFarmDetails, fetchWorkers]);

  const handleOpenDialog = (worker?: any) => {
    if (worker) {
      setEditingWorker(worker);
      setFormData({
        name: worker.name,
        email: worker.email,
        phone: worker.phone,
        role: worker.role,
        is_active: worker.is_active,
        receive_daily_tasks: worker.receive_daily_tasks,
      });
    } else {
      setEditingWorker(null);
      setFormData({
        name: '',
        email: '',
        phone: '',
        role: '',
        is_active: true,
        receive_daily_tasks: true,
      });
    }
    setWorkerDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setWorkerDialogOpen(false);
    setEditingWorker(null);
    setFormData({
      name: '',
      email: '',
      phone: '',
      role: '',
      is_active: true,
      receive_daily_tasks: true,
    });
  };

  const handleSubmit = async () => {
    try {
      if (editingWorker) {
        await updateWorker(editingWorker.id, formData);
      } else {
        await createWorker({ ...formData, farm: parseInt(farmId!) });
      }
      handleCloseDialog();
      if (farmId) {
        fetchWorkers(parseInt(farmId));
      }
    } catch (err) {
      // Error saving worker
    }
  };

  const handleDelete = async (worker: any) => {
    if (window.confirm(`Are you sure you want to delete ${worker.name}?`)) {
      try {
        await deleteWorker(worker.id);
        if (farmId) {
          fetchWorkers(parseInt(farmId));
        }
      } catch (err) {
        // Error deleting worker
      }
    }
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, worker: any) => {
    setMenuAnchor(event.currentTarget);
    setSelectedWorker(worker);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedWorker(null);
  };

  const getRoleColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'supervisor': return 'primary';
      case 'manager': return 'secondary';
      case 'worker': return 'success';
      case 'assistant': return 'info';
      default: return 'default';
    }
  };

  const filteredWorkers = workers.filter(worker => {
    const matchesSearch = worker.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         worker.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         worker.role.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = filterRole === 'all' || worker.role.toLowerCase() === filterRole.toLowerCase();
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'active' && worker.is_active) ||
                         (filterStatus === 'inactive' && !worker.is_active);
    return matchesSearch && matchesRole && matchesStatus;
  });

  const WorkerCard: React.FC<{ worker: any }> = ({ worker }) => (
    <Card 
      sx={{ 
        mb: 2,
        border: worker.is_active ? '1px solid' : '1px solid',
        borderColor: worker.is_active ? 'success.main' : 'divider',
        opacity: worker.is_active ? 1 : 0.7,
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          boxShadow: 2,
          transform: 'translateY(-1px)',
        }
      }}
    >
      <CardContent sx={{ p: 2 }}>
        <Box display="flex" alignItems="flex-start" justifyContent="space-between">
          <Box display="flex" alignItems="flex-start" gap={2} flex={1}>
            <Avatar 
              sx={{ 
                bgcolor: worker.is_active ? 'primary.main' : 'grey.400',
                width: 48, 
                height: 48 
              }}
            >
              <PersonIcon />
            </Avatar>
            
            <Box flex={1}>
              <Box display="flex" alignItems="center" gap={1} mb={1}>
                <Typography variant="h6" fontWeight={600}>
                  {worker.name}
                </Typography>
                <Chip 
                  size="small" 
                  label={worker.role}
                  color={getRoleColor(worker.role)}
                  variant="outlined"
                />
                <Chip 
                  size="small" 
                  label={worker.is_active ? 'Active' : 'Inactive'}
                  color={worker.is_active ? 'success' : 'default'}
                  variant="outlined"
                />
              </Box>

              <Box display="flex" alignItems="center" gap={0.5} mb={0.5}>
                <EmailIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {worker.email}
                </Typography>
              </Box>

              <Box display="flex" alignItems="center" gap={0.5} mb={1}>
                <PhoneIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {worker.phone}
                </Typography>
              </Box>

              {worker.receive_daily_tasks && (
                <Box display="flex" alignItems="center" gap={0.5}>
                  <AssignmentIcon fontSize="small" color="success" />
                  <Typography variant="caption" color="success.main">
                    Receives daily tasks
                  </Typography>
                </Box>
              )}
            </Box>
          </Box>

          <Box>
            <IconButton onClick={(e) => handleMenuOpen(e, worker)}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" fontWeight={700} color="text.primary" gutterBottom>
          Worker Management
        </Typography>
        {farm && (
          <Typography variant="body1" color="text.secondary">
            {farm.name}
          </Typography>
        )}
      </Box>

      {/* Filters and Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search workers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Role</InputLabel>
                <Select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  label="Role"
                >
                  <MenuItem value="all">All Roles</MenuItem>
                  <MenuItem value="supervisor">Supervisor</MenuItem>
                  <MenuItem value="manager">Manager</MenuItem>
                  <MenuItem value="worker">Worker</MenuItem>
                  <MenuItem value="assistant">Assistant</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
                fullWidth
                sx={{ height: '40px' }}
              >
                Add Worker
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Workers List */}
      <Box>
        {filteredWorkers.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <PersonIcon color="action" sx={{ fontSize: 48, mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No workers found
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={2}>
              {searchTerm || filterRole !== 'all' || filterStatus !== 'all'
                ? 'Try adjusting your search or filter criteria.'
                : 'No workers have been added to this farm yet.'
              }
            </Typography>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              Add First Worker
            </Button>
          </Paper>
        ) : (
          filteredWorkers.map((worker) => (
            <WorkerCard key={worker.id} worker={worker} />
          ))
        )}
      </Box>

      {/* Worker Dialog */}
      <Dialog open={workerDialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingWorker ? 'Edit Worker' : 'Add New Worker'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  label="Role"
                  required
                >
                  <MenuItem value="supervisor">Supervisor</MenuItem>
                  <MenuItem value="manager">Manager</MenuItem>
                  <MenuItem value="worker">Worker</MenuItem>
                  <MenuItem value="assistant">Assistant</MenuItem>
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
                label="Active"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.receive_daily_tasks}
                    onChange={(e) => setFormData({ ...formData, receive_daily_tasks: e.target.checked })}
                  />
                }
                label="Receive Daily Tasks"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={!formData.name.trim() || !formData.email.trim() || !formData.phone.trim() || !formData.role}
          >
            {editingWorker ? 'Update' : 'Add'} Worker
          </Button>
        </DialogActions>
      </Dialog>

      {/* Worker Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItemComponent onClick={() => { handleOpenDialog(selectedWorker); handleMenuClose(); }}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit Worker</ListItemText>
        </MenuItemComponent>
        <Divider />
        <MenuItemComponent 
          onClick={() => { handleDelete(selectedWorker); handleMenuClose(); }}
          sx={{ color: 'error.main' }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete Worker</ListItemText>
        </MenuItemComponent>
      </Menu>
    </Box>
  );
};

export default ProfessionalWorkerList;
