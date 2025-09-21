import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Assignment as TaskIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  Today as TodayIcon,
  TouchApp as ClickIcon,
} from '@mui/icons-material';
import { useFarm } from '../contexts/FarmContext';
import EmailManager from './EmailManager';
import WorkerList from './WorkerList';
import api from '../services/api';

const FarmDetail: React.FC = () => {
  const { farmId } = useParams<{ farmId: string }>();
  const navigate = useNavigate();
  const { houses, farmTaskSummary, loading, error, fetchHouses, fetchFarmTaskSummary, completeTask, createHouse, deleteHouse } = useFarm();
  const [farm, setFarm] = useState<any>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingHouse, setEditingHouse] = useState<any>(null);
  const [formData, setFormData] = useState({
    house_number: '',
    chicken_in_date: '',
    chicken_out_day: 40,
  });
  const [taskCompletionDialog, setTaskCompletionDialog] = useState(false);
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [completionNotes, setCompletionNotes] = useState('');

  useEffect(() => {
    if (farmId) {
      fetchFarmDetails();
      fetchHouses(parseInt(farmId));
      fetchFarmTaskSummary(parseInt(farmId));
    }
  }, [farmId]);

  const fetchFarmDetails = async () => {
    try {
      const response = await api.get(`/farms/${farmId}/`);
      setFarm(response.data);
    } catch (error) {
      console.error('Error fetching farm details:', error);
    }
  };

  const handleOpenDialog = (house?: any) => {
    if (house) {
      setEditingHouse(house);
      setFormData({
        house_number: house.house_number.toString(),
        chicken_in_date: house.chicken_in_date,
        chicken_out_day: house.chicken_out_day,
      });
    } else {
      setEditingHouse(null);
      setFormData({
        house_number: '',
        chicken_in_date: '',
        chicken_out_day: 40,
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingHouse(null);
    setFormData({
      house_number: '',
      chicken_in_date: '',
      chicken_out_day: 40,
    });
  };

  const handleSubmit = async () => {
    if (editingHouse) {
      // Update house logic would go here
      handleCloseDialog();
    } else {
      const success = await createHouse({
        ...formData,
        farm_id: parseInt(farmId!),
        house_number: parseInt(formData.house_number),
      });
      if (success) {
        handleCloseDialog();
        fetchHouses(parseInt(farmId!));
      }
    }
  };

  const handleDelete = async (houseId: number) => {
    if (window.confirm('Are you sure you want to delete this house?')) {
      const success = await deleteHouse(houseId);
      if (success) {
        fetchHouses(parseInt(farmId!));
      }
    }
  };

  const handleTaskClick = (task: any) => {
    setSelectedTask(task);
    setCompletionNotes('');
    setTaskCompletionDialog(true);
  };

  const handleCompleteTask = async () => {
    if (selectedTask) {
      const success = await completeTask(selectedTask.id, 'user', completionNotes);
      if (success) {
        setTaskCompletionDialog(false);
        setSelectedTask(null);
        setCompletionNotes('');
        // Refresh the task summary
        if (farmId) {
          await fetchFarmTaskSummary(parseInt(farmId));
        }
      }
    }
  };

  const handleCloseTaskDialog = () => {
    setTaskCompletionDialog(false);
    setSelectedTask(null);
    setCompletionNotes('');
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

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {farm && (
        <Box mb={3}>
          <Typography variant="h4" gutterBottom>
            {farm.name}
          </Typography>
          <Typography color="textSecondary" gutterBottom>
            {farm.location}
          </Typography>
          <Box display="flex" gap={1} mb={2}>
            <Chip label={`${farm.active_houses} Active Houses`} color="primary" />
            <Chip label={`${farm.total_houses} Total Houses`} variant="outlined" />
          </Box>
        </Box>
      )}

      {/* Task Overview Section */}
      {farmTaskSummary && farmTaskSummary.houses.length > 0 && (
        <Box mb={4}>
          <Typography variant="h5" gutterBottom>
            Task Overview
          </Typography>
          
          {farmTaskSummary.houses.map((house) => {
            const completionRate = house.tasks.total > 0 
              ? (house.tasks.completed / house.tasks.total) * 100 
              : 0;
            
            return (
              <Accordion key={house.id} defaultExpanded sx={{ mb: 2 }}>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  sx={{ 
                    backgroundColor: 'primary.light',
                    color: 'primary.contrastText',
                    '&:hover': {
                      backgroundColor: 'primary.main',
                    }
                  }}
                >
                  <Box display="flex" alignItems="center" gap={2} width="100%">
                    <Typography variant="h6">
                      House {house.house_number}
                    </Typography>
                    
                    <Box display="flex" gap={1} alignItems="center">
                      {house.current_day !== null ? (
                        <Chip 
                          label={`Day ${house.current_day}`} 
                          size="small" 
                          color="secondary" 
                          variant="filled"
                        />
                      ) : (
                        <Chip 
                          label="Inactive" 
                          size="small" 
                          color="default" 
                          variant="filled"
                        />
                      )}
                      
                      <Chip 
                        label={house.status} 
                        size="small" 
                        color={getStatusColor(house.status) as any}
                        variant="outlined"
                      />
                      
                      {house.tasks.today > 0 && (
                        <Chip 
                          icon={<TodayIcon />}
                          label={`${house.tasks.today} Today`} 
                          size="small" 
                          color="warning" 
                          variant="filled"
                        />
                      )}
                      
                      {house.tasks.overdue > 0 && (
                        <Chip 
                          icon={<WarningIcon />}
                          label={`${house.tasks.overdue} Overdue`} 
                          size="small" 
                          color="error" 
                          variant="filled"
                        />
                      )}
                    </Box>
                    
                    <Box display="flex" alignItems="center" gap={1} ml="auto">
                      <LinearProgress 
                        variant="determinate" 
                        value={completionRate} 
                        sx={{ width: 80, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption">
                        {Math.round(completionRate)}%
                      </Typography>
                    </Box>
                  </Box>
                </AccordionSummary>
                
                <AccordionDetails>
                  <Box>
                    <Box display="flex" gap={2} mb={2} flexWrap="wrap">
                      <Chip 
                        icon={<CheckCircleIcon />}
                        label="Completed" 
                        color="success" 
                        variant="outlined"
                      />
                      <Chip 
                        icon={<ScheduleIcon />}
                        label="Pending" 
                        color="info" 
                        variant="outlined"
                      />
                      <Typography variant="body2" color="textSecondary">
                        In: {new Date(house.chicken_in_date).toLocaleDateString()}
                      </Typography>
                      {house.chicken_out_date && (
                        <Typography variant="body2" color="textSecondary">
                          Out: {new Date(house.chicken_out_date).toLocaleDateString()}
                        </Typography>
                      )}
                    </Box>
                    
                    {house.pending_tasks.length > 0 ? (
                      <Box>
                        {/* Today's and Tomorrow's Tasks */}
                        {(() => {
                          const todayTasks = house.pending_tasks.filter(task => task.is_today);
                          const tomorrowTasks = house.pending_tasks.filter(task => 
                            task.day_offset === (house.current_day || 0) + 1
                          );
                          const otherTasks = house.pending_tasks.filter(task => 
                            !task.is_today && task.day_offset !== (house.current_day || 0) + 1
                          );
                          
                          return (
                            <>
                              {/* Today's Tasks */}
                              {todayTasks.length > 0 && (
                                <Box mb={2}>
                                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                                    <Typography variant="subtitle1" color="warning.main">
                                      Today&apos;s Tasks ({todayTasks.length})
                                    </Typography>
                                    <ClickIcon fontSize="small" color="action" />
                                    <Typography variant="caption" color="textSecondary">
                                      Click to complete
                                    </Typography>
                                  </Box>
                                  <List dense>
                                    {todayTasks.map((task, index) => (
                                      <React.Fragment key={task.id}>
                                        <ListItem 
                                          sx={{ 
                                            backgroundColor: 'warning.light',
                                            borderRadius: 1,
                                            mb: 0.5,
                                            cursor: 'pointer',
                                            '&:hover': {
                                              backgroundColor: 'warning.main',
                                              color: 'warning.contrastText'
                                            }
                                          }}
                                          onClick={() => handleTaskClick(task)}
                                        >
                                          <ListItemIcon>
                                            <TodayIcon color="warning" />
                                          </ListItemIcon>
                                          <ListItemText
                                            primary={
                                              <Box display="flex" alignItems="center" gap={1}>
                                                <Typography variant="body2" fontWeight="bold">
                                                  {task.task_name}
                                                </Typography>
                                                <Chip 
                                                  label={`Day ${task.day_offset}`} 
                                                  size="small" 
                                                  color="warning"
                                                  variant="outlined"
                                                />
                                                <Chip 
                                                  label={task.task_type} 
                                                  size="small" 
                                                  color="primary"
                                                  variant="outlined"
                                                />
                                              </Box>
                                            }
                                            secondary={task.description}
                                          />
                                        </ListItem>
                                        {index < todayTasks.length - 1 && <Divider />}
                                      </React.Fragment>
                                    ))}
                                  </List>
                                </Box>
                              )}
                              
                              {/* Tomorrow's Tasks */}
                              {tomorrowTasks.length > 0 && (
                                <Box mb={2}>
                                  <Box display="flex" alignItems="center" gap={1} mb={1}>
                                    <Typography variant="subtitle1" color="info.main">
                                      Tomorrow&apos;s Tasks ({tomorrowTasks.length})
                                    </Typography>
                                    <ClickIcon fontSize="small" color="action" />
                                    <Typography variant="caption" color="textSecondary">
                                      Click to complete
                                    </Typography>
                                  </Box>
                                  <List dense>
                                    {tomorrowTasks.map((task, index) => (
                                      <React.Fragment key={task.id}>
                                        <ListItem 
                                          sx={{ 
                                            backgroundColor: 'info.light',
                                            borderRadius: 1,
                                            mb: 0.5,
                                            cursor: 'pointer',
                                            '&:hover': {
                                              backgroundColor: 'info.main',
                                              color: 'info.contrastText'
                                            }
                                          }}
                                          onClick={() => handleTaskClick(task)}
                                        >
                                          <ListItemIcon>
                                            <ScheduleIcon color="info" />
                                          </ListItemIcon>
                                          <ListItemText
                                            primary={
                                              <Box display="flex" alignItems="center" gap={1}>
                                                <Typography variant="body2" fontWeight="bold">
                                                  {task.task_name}
                                                </Typography>
                                                <Chip 
                                                  label={`Day ${task.day_offset}`} 
                                                  size="small" 
                                                  color="info"
                                                  variant="outlined"
                                                />
                                                <Chip 
                                                  label={task.task_type} 
                                                  size="small" 
                                                  color="primary"
                                                  variant="outlined"
                                                />
                                              </Box>
                                            }
                                            secondary={task.description}
                                          />
                                        </ListItem>
                                        {index < tomorrowTasks.length - 1 && <Divider />}
                                      </React.Fragment>
                                    ))}
                                  </List>
                                </Box>
                              )}
                              
                              {/* Other Pending Tasks (Collapsed by default) */}
                              {otherTasks.length > 0 && (
                                <Accordion defaultExpanded={false} sx={{ mt: 2 }}>
                                  <AccordionSummary
                                    expandIcon={<ExpandMoreIcon />}
                                    sx={{ 
                                      backgroundColor: 'grey.100',
                                      '&:hover': {
                                        backgroundColor: 'grey.200',
                                      }
                                    }}
                                  >
                                    <Box display="flex" alignItems="center" gap={1}>
                                      <Typography variant="subtitle2">
                                        Other Pending Tasks ({otherTasks.length})
                                      </Typography>
                                      <ClickIcon fontSize="small" color="action" />
                                      <Typography variant="caption" color="textSecondary">
                                        Click to complete
                                      </Typography>
                                    </Box>
                                  </AccordionSummary>
                                  <AccordionDetails>
                                    <List dense>
                                      {otherTasks.map((task, index) => (
                                        <React.Fragment key={task.id}>
                                          <ListItem 
                                            sx={{ 
                                              backgroundColor: 'transparent',
                                              borderRadius: 1,
                                              mb: 0.5,
                                              cursor: 'pointer',
                                              '&:hover': {
                                                backgroundColor: 'action.hover'
                                              }
                                            }}
                                            onClick={() => handleTaskClick(task)}
                                          >
                                            <ListItemIcon>
                                              <ScheduleIcon color="action" />
                                            </ListItemIcon>
                                            <ListItemText
                                              primary={
                                                <Box display="flex" alignItems="center" gap={1}>
                                                  <Typography variant="body2">
                                                    {task.task_name}
                                                  </Typography>
                                                  <Chip 
                                                    label={`Day ${task.day_offset}`} 
                                                    size="small" 
                                                    color="default"
                                                    variant="outlined"
                                                  />
                                                  <Chip 
                                                    label={task.task_type} 
                                                    size="small" 
                                                    color="primary"
                                                    variant="outlined"
                                                  />
                                                </Box>
                                              }
                                              secondary={task.description}
                                            />
                                          </ListItem>
                                          {index < otherTasks.length - 1 && <Divider />}
                                        </React.Fragment>
                                      ))}
                                    </List>
                                  </AccordionDetails>
                                </Accordion>
                              )}
                            </>
                          );
                        })()}
                      </Box>
                    ) : (
                      <Box textAlign="center" py={2}>
                        <CheckCircleIcon color="success" sx={{ fontSize: 48, mb: 1 }} />
                        <Typography variant="h6" color="success.main">
                          All tasks completed!
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          No pending tasks for this house.
                        </Typography>
                      </Box>
                    )}
                  </Box>
                </AccordionDetails>
              </Accordion>
            );
          })}
        </Box>
      )}

      {/* Email Management for this farm */}
      <Box mb={4}>
        <EmailManager farmId={farm?.id} farmName={farm?.name} />
      </Box>

      {/* Worker Management for this farm */}
      <Box mb={4}>
        <WorkerList farmId={farm?.id} farmName={farm?.name} />
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Houses</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add House
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {houses.map((house) => (
          <Grid item xs={12} sm={6} md={4} key={house.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                  <Typography variant="h6" component="div">
                    House {house.house_number}
                  </Typography>
                  <Box>
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(house)}
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(house.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Box>
                </Box>
                
                <Box display="flex" gap={1} mb={2}>
                  <Chip
                    label={house.status}
                    color={getStatusColor(house.status) as any}
                    size="small"
                  />
                  {house.current_day !== null && (
                    <Chip
                      label={`Day ${house.current_day}`}
                      variant="outlined"
                      size="small"
                    />
                  )}
                </Box>
                
                <Typography color="textSecondary" gutterBottom>
                  In: {new Date(house.chicken_in_date).toLocaleDateString()}
                </Typography>
                
                {house.chicken_out_date && (
                  <Typography color="textSecondary" gutterBottom>
                    Out: {new Date(house.chicken_out_date).toLocaleDateString()}
                  </Typography>
                )}
                
                <Box display="flex" gap={1} mt={2}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<TaskIcon />}
                    onClick={() => navigate(`/houses/${house.id}/tasks`)}
                  >
                    View Tasks
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => navigate(`/houses/${house.id}`)}
                  >
                    Details
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Add/Edit House Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingHouse ? 'Edit House' : 'Add New House'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="House Number"
            fullWidth
            variant="outlined"
            type="number"
            value={formData.house_number}
            onChange={(e) => setFormData({ ...formData, house_number: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Chicken In Date"
            fullWidth
            variant="outlined"
            type="date"
            InputLabelProps={{ shrink: true }}
            value={formData.chicken_in_date}
            onChange={(e) => setFormData({ ...formData, chicken_in_date: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Chicken Out Day"
            fullWidth
            variant="outlined"
            type="number"
            value={formData.chicken_out_day}
            onChange={(e) => setFormData({ ...formData, chicken_out_day: parseInt(e.target.value) })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingHouse ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Task Completion Dialog */}
      <Dialog open={taskCompletionDialog} onClose={handleCloseTaskDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          Complete Task
        </DialogTitle>
        <DialogContent>
          {selectedTask && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedTask.task_name}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                {selectedTask.description}
              </Typography>
              <Box display="flex" gap={1} mb={2}>
                <Chip 
                  label={`Day ${selectedTask.day_offset}`} 
                  size="small" 
                  color="primary"
                  variant="outlined"
                />
                <Chip 
                  label={selectedTask.task_type} 
                  size="small" 
                  color="secondary"
                  variant="outlined"
                />
              </Box>
              <TextField
                autoFocus
                margin="dense"
                label="Completion Notes (Optional)"
                fullWidth
                multiline
                rows={3}
                variant="outlined"
                value={completionNotes}
                onChange={(e) => setCompletionNotes(e.target.value)}
                placeholder="Add any notes about task completion..."
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseTaskDialog}>Cancel</Button>
          <Button onClick={handleCompleteTask} variant="contained" color="success">
            Mark as Complete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FarmDetail;
