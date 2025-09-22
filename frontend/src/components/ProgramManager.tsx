import React, { useState, useEffect } from 'react';
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
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useProgram, Program, ProgramTask } from '../contexts/ProgramContext';

const ProgramManager: React.FC = () => {
  const {
    programs,
    loading,
    error,
    fetchPrograms,
    createProgram,
    updateProgram,
    deleteProgram,
    copyProgram,
  } = useProgram();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingProgram, setEditingProgram] = useState<Program | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    duration_days: 40,
    is_active: true,
    is_default: false,
  });

  useEffect(() => {
    fetchPrograms();
  }, [fetchPrograms]);

  const handleOpenDialog = (program?: Program) => {
    if (program) {
      setEditingProgram(program);
      setFormData({
        name: program.name,
        description: program.description,
        duration_days: program.duration_days,
        is_active: program.is_active,
        is_default: program.is_default,
      });
    } else {
      setEditingProgram(null);
      setFormData({
        name: '',
        description: '',
        duration_days: 40,
        is_active: true,
        is_default: false,
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingProgram(null);
    setFormData({
      name: '',
      description: '',
      duration_days: 40,
      is_active: true,
      is_default: false,
    });
  };

  const handleSubmit = async () => {
    const success = editingProgram
      ? await updateProgram(editingProgram.id, formData)
      : await createProgram(formData);

    if (success) {
      handleCloseDialog();
      fetchPrograms();
    }
  };

  const handleDelete = async (program: Program) => {
    if (window.confirm(`Are you sure you want to delete "${program.name}"?`)) {
      const success = await deleteProgram(program.id);
      if (success) {
        fetchPrograms();
      }
    }
  };

  const handleCopy = async (program: Program) => {
    const newName = prompt(`Enter name for copy of "${program.name}":`, `${program.name} (Copy)`);
    if (newName) {
      const success = await copyProgram(program.id, newName);
      if (success) {
        fetchPrograms();
      }
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Task Programs
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Create Program
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {programs.map((program) => (
          <Grid item xs={12} md={6} lg={4} key={program.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" component="h2">
                    {program.name}
                  </Typography>
                  <Box>
                    {program.is_default && (
                      <Chip
                        label="Default"
                        color="primary"
                        size="small"
                        icon={<CheckIcon />}
                        sx={{ mb: 1 }}
                      />
                    )}
                    <Chip
                      label={program.is_active ? 'Active' : 'Inactive'}
                      color={program.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" paragraph>
                  {program.description}
                </Typography>

                <Box display="flex" gap={1} mb={2}>
                  <Chip
                    icon={<ScheduleIcon />}
                    label={`${program.duration_days} days`}
                    variant="outlined"
                    size="small"
                  />
                  <Chip
                    label={`${program.total_tasks} tasks`}
                    variant="outlined"
                    size="small"
                  />
                </Box>

                <Divider sx={{ my: 2 }} />

                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="caption" color="text.secondary">
                    Created: {new Date(program.created_at).toLocaleDateString()}
                  </Typography>
                  <Box>
                    <Tooltip title="View Details">
                      <IconButton size="small" onClick={() => handleOpenDialog(program)}>
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => handleOpenDialog(program)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Copy">
                      <IconButton size="small" onClick={() => handleCopy(program)}>
                        <CopyIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton 
                        size="small" 
                        onClick={() => handleDelete(program)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingProgram ? 'Edit Program' : 'Create New Program'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Program Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Duration (days)"
                type="number"
                value={formData.duration_days}
                onChange={(e) => setFormData({ ...formData, duration_days: parseInt(e.target.value) || 40 })}
                inputProps={{ min: 1, max: 365 }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.is_active ? 'active' : 'inactive'}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'active' })}
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_default}
                    onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                  />
                }
                label="Set as default program for new farms"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingProgram ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProgramManager;
