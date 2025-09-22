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
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Assignment as TaskIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Person as PersonIcon,
  Notes as NotesIcon,
  Search as SearchIcon,
  Info as InfoIcon,
  Today as TodayIcon,
  Upcoming as UpcomingIcon,
} from '@mui/icons-material';
import { useTask } from '../../contexts/TaskContext';
import api from '../../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`task-tabpanel-${index}`}
    aria-labelledby={`task-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const ProfessionalTaskList: React.FC = () => {
  const { houseId } = useParams<{ houseId: string }>();
  const [house, setHouse] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [completeDialogOpen, setCompleteDialogOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [completedBy, setCompletedBy] = useState('');
  const [notes, setNotes] = useState('');
  const { tasks, todayTasks, upcomingTasks, fetchTasks, fetchTodayTasks, fetchUpcomingTasks, completeTask } = useTask();

  const fetchHouseDetails = useCallback(async () => {
    try {
      const response = await api.get(`/houses/${houseId}/`);
      setHouse(response.data);
    } catch (err) {
      setError('Failed to fetch house details');
    } finally {
      setLoading(false);
    }
  }, [houseId]);

  useEffect(() => {
    if (houseId) {
      fetchHouseDetails();
      fetchTasks(parseInt(houseId));
      fetchTodayTasks(parseInt(houseId));
      fetchUpcomingTasks(parseInt(houseId), 7);
    }
  }, [houseId, fetchHouseDetails, fetchTasks, fetchTodayTasks, fetchUpcomingTasks]);


  const handleCompleteTask = (task: any) => {
    setSelectedTask(task);
    setCompletedBy('');
    setNotes('');
    setCompleteDialogOpen(true);
  };

  const handleSubmitCompletion = async () => {
    if (selectedTask) {
      const success = await completeTask(selectedTask.id, completedBy, notes);
      if (success) {
        setCompleteDialogOpen(false);
        // Refresh tasks
        if (houseId) {
          fetchTasks(parseInt(houseId));
          fetchTodayTasks(parseInt(houseId));
          fetchUpcomingTasks(parseInt(houseId), 7);
        }
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'pending': return 'warning';
      case 'overdue': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const filteredTasks = (taskList: any[]) => {
    return taskList.filter(task => {
      const matchesSearch = task.task_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           task.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = filterStatus === 'all' || 
                           (filterStatus === 'completed' && task.is_completed) ||
                           (filterStatus === 'pending' && !task.is_completed);
      return matchesSearch && matchesStatus;
    });
  };

  const TaskCard: React.FC<{ task: any; showActions?: boolean }> = ({ task, showActions = true }) => (
    <Card 
      sx={{ 
        mb: 2,
        border: task.is_completed ? '1px solid' : '1px solid',
        borderColor: task.is_completed ? 'success.main' : 'divider',
        opacity: task.is_completed ? 0.7 : 1,
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          boxShadow: 2,
          transform: 'translateY(-1px)',
        }
      }}
    >
      <CardContent sx={{ p: 2 }}>
        <Box display="flex" alignItems="flex-start" justifyContent="space-between">
          <Box flex={1}>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <TaskIcon fontSize="small" color={task.is_completed ? 'success' : 'primary'} />
              <Typography variant="h6" fontWeight={600} color={task.is_completed ? 'text.secondary' : 'text.primary'}>
                {task.task_name}
              </Typography>
              <Chip 
                size="small" 
                label={task.is_completed ? 'Completed' : 'Pending'}
                color={getStatusColor(task.is_completed ? 'completed' : 'pending')}
                variant="outlined"
              />
            </Box>
            
            <Typography variant="body2" color="text.secondary" mb={2}>
              {task.description}
            </Typography>

            <Box display="flex" alignItems="center" gap={2} mb={2}>
              <Box display="flex" alignItems="center" gap={0.5}>
                <ScheduleIcon fontSize="small" color="action" />
                <Typography variant="caption" color="text.secondary">
                  Day {task.day_offset}
                </Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={0.5}>
                <Chip 
                  size="small" 
                  label={task.task_type}
                  color={getPriorityColor(task.task_type)}
                  variant="outlined"
                />
              </Box>
            </Box>

            {task.completed_by && (
              <Box display="flex" alignItems="center" gap={0.5} mb={1}>
                <PersonIcon fontSize="small" color="action" />
                <Typography variant="caption" color="text.secondary">
                  Completed by: {task.completed_by}
                </Typography>
              </Box>
            )}

            {task.notes && (
              <Box display="flex" alignItems="flex-start" gap={0.5}>
                <NotesIcon fontSize="small" color="action" />
                <Typography variant="caption" color="text.secondary">
                  {task.notes}
                </Typography>
              </Box>
            )}
          </Box>

          {showActions && !task.is_completed && (
            <Box ml={2}>
              <Button
                variant="contained"
                size="small"
                startIcon={<CheckCircleIcon />}
                onClick={() => handleCompleteTask(task)}
                sx={{ minWidth: 120 }}
              >
                Complete
              </Button>
            </Box>
          )}
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
          Task Management
        </Typography>
        {house && (
          <Typography variant="body1" color="text.secondary">
            {house.farm_name} - {house.name}
          </Typography>
        )}
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search tasks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="all">All Tasks</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={12} md={5}>
              <Box display="flex" gap={1}>
                <Button
                  variant="outlined"
                  startIcon={<TodayIcon />}
                  onClick={() => setTabValue(0)}
                  color={tabValue === 0 ? 'primary' : 'inherit'}
                >
                  Today ({filteredTasks(todayTasks).length})
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<UpcomingIcon />}
                  onClick={() => setTabValue(1)}
                  color={tabValue === 1 ? 'primary' : 'inherit'}
                >
                  Upcoming ({filteredTasks(upcomingTasks).length})
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<TaskIcon />}
                  onClick={() => setTabValue(2)}
                  color={tabValue === 2 ? 'primary' : 'inherit'}
                >
                  All ({filteredTasks(tasks).length})
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Task Lists */}
      <Box>
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" fontWeight={600} mb={3} color="primary">
            Today&apos;s Tasks
          </Typography>
          {filteredTasks(todayTasks).length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <InfoIcon color="action" sx={{ fontSize: 48, mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No tasks for today
              </Typography>
              <Typography variant="body2" color="text.secondary">
                All caught up! Check back tomorrow for new tasks.
              </Typography>
            </Paper>
          ) : (
            filteredTasks(todayTasks).map((task) => (
              <TaskCard key={task.id} task={task} />
            ))
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" fontWeight={600} mb={3} color="primary">
            Upcoming Tasks (Next 7 Days)
          </Typography>
          {filteredTasks(upcomingTasks).length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <InfoIcon color="action" sx={{ fontSize: 48, mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No upcoming tasks
              </Typography>
              <Typography variant="body2" color="text.secondary">
                No tasks scheduled for the next 7 days.
              </Typography>
            </Paper>
          ) : (
            filteredTasks(upcomingTasks).map((task) => (
              <TaskCard key={task.id} task={task} showActions={false} />
            ))
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" fontWeight={600} mb={3} color="primary">
            All Tasks
          </Typography>
          {filteredTasks(tasks).length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <InfoIcon color="action" sx={{ fontSize: 48, mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No tasks found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchTerm || filterStatus !== 'all' 
                  ? 'Try adjusting your search or filter criteria.'
                  : 'No tasks have been generated for this house yet.'
                }
              </Typography>
            </Paper>
          ) : (
            filteredTasks(tasks).map((task) => (
              <TaskCard key={task.id} task={task} />
            ))
          )}
        </TabPanel>
      </Box>

      {/* Complete Task Dialog */}
      <Dialog open={completeDialogOpen} onClose={() => setCompleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Complete Task</DialogTitle>
        <DialogContent>
          {selectedTask && (
            <Box mb={3}>
              <Typography variant="h6" gutterBottom>
                {selectedTask.task_name}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {selectedTask.description}
              </Typography>
            </Box>
          )}
          <TextField
            fullWidth
            label="Completed By"
            value={completedBy}
            onChange={(e) => setCompletedBy(e.target.value)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Notes (Optional)"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            margin="normal"
            multiline
            rows={3}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleSubmitCompletion} 
            variant="contained"
            disabled={!completedBy.trim()}
          >
            Complete Task
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProfessionalTaskList;
