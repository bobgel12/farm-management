import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Email as EmailIcon,
  Person as PersonIcon,
  Phone as PhoneIcon,
  Work as WorkIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { useWorker } from '../contexts/WorkerContext';
import WorkerForm from './WorkerForm';

interface WorkerListProps {
  farmId: number;
  farmName: string;
}

const WorkerList: React.FC<WorkerListProps> = ({ farmId, farmName }) => {
  const { workers, loading, error, fetchWorkers, deleteWorker } = useWorker();
  const [formOpen, setFormOpen] = useState(false);
  const [editingWorker, setEditingWorker] = useState<any>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [workerToDelete, setWorkerToDelete] = useState<any>(null);
  const fetchingRef = useRef(false);

  // Ensure workers is always an array
  const safeWorkers = Array.isArray(workers) ? workers : [];

  useEffect(() => {
    if (farmId && !fetchingRef.current) {
      fetchingRef.current = true;
      fetchWorkers(farmId).finally(() => {
        fetchingRef.current = false;
      });
    }
  }, [farmId, fetchWorkers]);

  const handleAddWorker = () => {
    setEditingWorker(null);
    setFormOpen(true);
  };

  const handleEditWorker = (worker: any) => {
    setEditingWorker(worker);
    setFormOpen(true);
  };

  const handleDeleteWorker = (worker: any) => {
    setWorkerToDelete(worker);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (workerToDelete) {
      const success = await deleteWorker(workerToDelete.id);
      if (success) {
        setDeleteDialogOpen(false);
        setWorkerToDelete(null);
      }
    }
  };

  const handleFormSuccess = () => {
    fetchWorkers(farmId);
  };

  const getRoleColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'manager':
        return 'primary';
      case 'supervisor':
        return 'secondary';
      case 'worker':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive ? 'success' : 'error';
  };

  if (loading && safeWorkers.length === 0) {
    return (
      <Box display="flex" justifyContent="center" py={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h6" gutterBottom>
              👥 Workers - {farmName}
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddWorker}
              size="small"
            >
              Add Worker
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {safeWorkers.length === 0 ? (
            <Box textAlign="center" py={4}>
              <PersonIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="body1" color="text.secondary" gutterBottom>
                No workers found for this farm
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Add workers to enable daily task email notifications
              </Typography>
              <Button
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={handleAddWorker}
                sx={{ mt: 2 }}
              >
                Add First Worker
              </Button>
            </Box>
          ) : (
            <List>
              {safeWorkers.map((worker, index) => (
                <React.Fragment key={worker.id}>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          <Typography variant="subtitle1" fontWeight={600}>
                            {worker.name}
                          </Typography>
                          <Chip
                            label={worker.is_active ? 'Active' : 'Inactive'}
                            color={getStatusColor(worker.is_active) as any}
                            size="small"
                          />
                          {worker.role && (
                            <Chip
                              label={worker.role}
                              color={getRoleColor(worker.role) as any}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                            <EmailIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {worker.email}
                            </Typography>
                          </Box>
                          {worker.phone && (
                            <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                              <PhoneIcon fontSize="small" color="action" />
                              <Typography variant="body2" color="text.secondary">
                                {worker.phone}
                              </Typography>
                            </Box>
                          )}
                          <Box display="flex" alignItems="center" gap={1}>
                            <WorkIcon fontSize="small" color="action" />
                            <Typography variant="body2" color="text.secondary">
                              {worker.role || 'Worker'}
                            </Typography>
                            {worker.receive_daily_tasks && (
                              <Chip
                                icon={<CheckCircleIcon />}
                                label="Receives Emails"
                                color="success"
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box display="flex" gap={0.5}>
                        <Tooltip title="Edit Worker">
                          <IconButton
                            size="small"
                            onClick={() => handleEditWorker(worker)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Worker">
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteWorker(worker)}
                            color="error"
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < safeWorkers.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}

          {safeWorkers.length > 0 && (
            <Box mt={2}>
              <Typography variant="body2" color="text.secondary">
                {safeWorkers.filter(w => w.is_active).length} active workers • {' '}
                {safeWorkers.filter(w => w.receive_daily_tasks).length} receive daily emails
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Worker Form Dialog */}
      <WorkerForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        farmId={farmId}
        farmName={farmName}
        worker={editingWorker}
        onSuccess={handleFormSuccess}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Worker</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete <strong>{workerToDelete?.name}</strong>?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmDelete}
            color="error"
            variant="contained"
            disabled={loading}
          >
            {loading ? <CircularProgress size={20} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WorkerList;
