import React, { useEffect, useState } from 'react';
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
  Checkbox,
  FormControlLabel,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Assignment as TaskIcon, CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { useTask } from '../contexts/TaskContext.tsx';
import api from '../services/api.ts';

const TaskList: React.FC = () => {
  const { houseId } = useParams<{ houseId: string }>();
  const [house, setHouse] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completeDialogOpen, setCompleteDialogOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [completedBy, setCompletedBy] = useState('');
  const [notes, setNotes] = useState('');
  const { tasks, fetchTasks, completeTask } = useTask();

  useEffect(() => {
    if (houseId) {
      fetchHouseDetails();
      fetchTasks(parseInt(houseId));
    }
  }, [houseId]);

  const fetchHouseDetails = async () => {
    try {
      const response = await api.get(`/houses/${houseId}/`);
      setHouse(response.data);
    } catch (err) {
      setError('Failed to fetch house details');
      console.error('Error fetching house details:', err);
    } finally {
      setLoading(false);
    }
  };

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
        fetchTasks(parseInt(houseId!));
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'setup': return 'warning';
      case 'arrival': return 'info';
      case 'early_care': return 'primary';
      case 'growth': return 'success';
      case 'maturation': return 'secondary';
      case 'production': return 'default';
      case 'pre_exit': return 'warning';
      case 'cleanup': return 'error';
      default: return 'default';
    }
  };

  const getTaskTypeColor = (taskType: string) => {
    switch (taskType) {
      case 'setup': return 'warning';
      case 'daily': return 'primary';
      case 'weekly': return 'info';
      case 'special': return 'secondary';
      case 'exit': return 'error';
      case 'cleanup': return 'default';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
      </Alert>
    );
  }

  if (!house) {
    return (
      <Alert severity="warning">
        House not found
      </Alert>
    );
  }

  // Group tasks by day
  const tasksByDay = tasks.reduce((acc, task) => {
    const day = task.day_offset;
    if (!acc[day]) {
      acc[day] = [];
    }
    acc[day].push(task);
    return acc;
  }, {} as Record<number, any[]>);

  const sortedDays = Object.keys(tasksByDay).map(Number).sort((a, b) => a - b);

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          {house.farm_name} - House {house.house_number} Tasks
        </Typography>
        
        <Box display="flex" gap={2} mb={3}>
          <Chip
            label={house.status}
            color={getStatusColor(house.status) as any}
          />
          {house.current_day !== null && (
            <Chip
              label={`Day ${house.current_day}`}
              variant="outlined"
            />
          )}
        </Box>
      </Box>

      {sortedDays.map((day) => (
        <Card key={day} sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Day {day}
              {day === house.current_day && (
                <Chip label="Today" color="primary" size="small" sx={{ ml: 2 }} />
              )}
            </Typography>
            
            <Grid container spacing={2}>
              {tasksByDay[day].map((task) => (
                <Grid item xs={12} md={6} key={task.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box display="flex" alignItems="flex-start" justifyContent="space-between">
                        <Box flexGrow={1}>
                          <Typography variant="subtitle1" gutterBottom>
                            {task.task_name}
                          </Typography>
                          <Typography variant="body2" color="textSecondary" gutterBottom>
                            {task.description}
                          </Typography>
                          <Box display="flex" gap={1} mb={2}>
                            <Chip
                              label={task.task_type}
                              size="small"
                              color={getTaskTypeColor(task.task_type) as any}
                              variant="outlined"
                            />
                            {task.is_completed && (
                              <Chip
                                label="Completed"
                                size="small"
                                color="success"
                                icon={<CheckCircleIcon />}
                              />
                            )}
                          </Box>
                          {task.is_completed && task.completed_at && (
                            <Typography variant="caption" color="textSecondary">
                              Completed on {new Date(task.completed_at).toLocaleString()}
                              {task.completed_by && ` by ${task.completed_by}`}
                            </Typography>
                          )}
                        </Box>
                        
                        {!task.is_completed && (
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => handleCompleteTask(task)}
                          >
                            Complete
                          </Button>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      ))}

      {/* Complete Task Dialog */}
      <Dialog open={completeDialogOpen} onClose={() => setCompleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Complete Task</DialogTitle>
        <DialogContent>
          {selectedTask && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedTask.task_name}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                {selectedTask.description}
              </Typography>
              
              <TextField
                autoFocus
                margin="dense"
                label="Completed By"
                fullWidth
                variant="outlined"
                value={completedBy}
                onChange={(e) => setCompletedBy(e.target.value)}
                sx={{ mt: 2 }}
              />
              
              <TextField
                margin="dense"
                label="Notes"
                fullWidth
                variant="outlined"
                multiline
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                sx={{ mt: 2 }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCompleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmitCompletion} variant="contained">
            Complete Task
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaskList;
