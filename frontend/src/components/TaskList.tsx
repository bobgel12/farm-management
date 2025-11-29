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
import { useTask } from '../contexts/TaskContext';
import api from '../services/api';
import logger from '../utils/logger';

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
      <Box mb={{ xs: 2, sm: 3 }}>
        <Typography 
          variant="h4" 
          gutterBottom
          sx={{ 
            fontSize: { xs: '1.5rem', sm: '2.125rem' },
            fontWeight: 600,
            mb: { xs: 2, sm: 3 }
          }}
        >
          {house.farm_name} - House {house.house_number} Tasks
        </Typography>
        
        <Box 
          display="flex" 
          gap={{ xs: 1, sm: 2 }} 
          mb={{ xs: 2, sm: 3 }}
          flexWrap="wrap"
        >
          <Chip
            label={house.status}
            color={getStatusColor(house.status) as any}
            sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
          />
          {(house.age_days ?? house.current_day) !== null && (
            <Chip
              label={`Day ${house.age_days ?? house.current_day}`}
              variant="outlined"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            />
          )}
        </Box>
      </Box>

      {sortedDays.map((day) => (
        <Card key={day} sx={{ mb: { xs: 2, sm: 3 } }}>
          <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
            <Box 
              display="flex" 
              alignItems="center" 
              justifyContent="space-between"
              mb={{ xs: 2, sm: 3 }}
              flexWrap="wrap"
              gap={1}
            >
              <Typography 
                variant="h6" 
                sx={{ 
                  fontSize: { xs: '1.1rem', sm: '1.25rem' },
                  fontWeight: 600
                }}
              >
                Day {day}
              </Typography>
              {day === (house.age_days ?? house.current_day) && (
                <Chip 
                  label="Today" 
                  color="primary" 
                  size="small" 
                  sx={{ 
                    fontSize: { xs: '0.75rem', sm: '0.875rem' },
                    ml: { xs: 0, sm: 2 }
                  }} 
                />
              )}
            </Box>
            
            <Grid container spacing={{ xs: 1.5, sm: 2 }}>
              {tasksByDay[day].map((task) => (
                <Grid item xs={12} sm={6} md={6} key={task.id}>
                  <Card 
                    variant="outlined" 
                    sx={{ 
                      height: '100%',
                      '&:hover': {
                        boxShadow: 2
                      }
                    }}
                  >
                    <CardContent sx={{ p: { xs: 2, sm: 2.5 } }}>
                      <Box 
                        display="flex" 
                        alignItems="flex-start" 
                        justifyContent="space-between"
                        flexDirection={{ xs: 'column', sm: 'row' }}
                        gap={{ xs: 2, sm: 1 }}
                      >
                        <Box flexGrow={1} width="100%">
                          <Typography 
                            variant="subtitle1" 
                            gutterBottom
                            sx={{ 
                              fontSize: { xs: '0.9rem', sm: '1rem' },
                              fontWeight: 600
                            }}
                          >
                            {task.task_name}
                          </Typography>
                          <Typography 
                            variant="body2" 
                            color="textSecondary" 
                            gutterBottom
                            sx={{ 
                              fontSize: { xs: '0.8rem', sm: '0.875rem' },
                              mb: 2
                            }}
                          >
                            {task.description}
                          </Typography>
                          <Box 
                            display="flex" 
                            gap={1} 
                            mb={2}
                            flexWrap="wrap"
                          >
                            <Chip
                              label={task.task_type}
                              size="small"
                              color={getTaskTypeColor(task.task_type) as any}
                              variant="outlined"
                              sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                            />
                            {task.is_completed && (
                              <Chip
                                label="Completed"
                                size="small"
                                color="success"
                                icon={<CheckCircleIcon sx={{ fontSize: { xs: 14, sm: 16 } }} />}
                                sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                              />
                            )}
                          </Box>
                          {task.is_completed && task.completed_at && (
                            <Typography 
                              variant="caption" 
                              color="textSecondary"
                              sx={{ 
                                fontSize: { xs: '0.7rem', sm: '0.75rem' },
                                display: 'block'
                              }}
                            >
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
                            sx={{ 
                              minWidth: { xs: '100%', sm: 'auto' },
                              fontSize: { xs: '0.75rem', sm: '0.875rem' },
                              minHeight: { xs: 40, sm: 32 }
                            }}
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
      <Dialog 
        open={completeDialogOpen} 
        onClose={() => setCompleteDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
        fullScreen={false}
        sx={{
          '& .MuiDialog-paper': {
            m: { xs: 1, sm: 2 },
            maxHeight: { xs: '95vh', sm: '90vh' }
          }
        }}
      >
        <DialogTitle sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' }, fontWeight: 600 }}>
          Complete Task
        </DialogTitle>
        <DialogContent sx={{ p: { xs: 2, sm: 3 } }}>
          {selectedTask && (
            <Box>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ 
                  fontSize: { xs: '1rem', sm: '1.25rem' },
                  fontWeight: 600
                }}
              >
                {selectedTask.task_name}
              </Typography>
              <Typography 
                variant="body2" 
                color="textSecondary" 
                gutterBottom
                sx={{ 
                  fontSize: { xs: '0.875rem', sm: '1rem' },
                  mb: 2
                }}
              >
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
                InputProps={{
                  sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
                }}
                InputLabelProps={{
                  sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
                }}
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
                InputProps={{
                  sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
                }}
                InputLabelProps={{
                  sx: { fontSize: { xs: '0.875rem', sm: '1rem' } }
                }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ p: { xs: 2, sm: 3 }, gap: 1 }}>
          <Button 
            onClick={() => setCompleteDialogOpen(false)}
            sx={{ 
              fontSize: { xs: '0.875rem', sm: '0.875rem' },
              minHeight: { xs: 44, sm: 36 }
            }}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleSubmitCompletion} 
            variant="contained"
            sx={{ 
              fontSize: { xs: '0.875rem', sm: '0.875rem' },
              minHeight: { xs: 44, sm: 36 }
            }}
          >
            Complete Task
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaskList;
