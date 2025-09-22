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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Badge,
  Tabs,
  Tab,
  Paper,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckIcon,
  Schedule as ScheduleIcon,
  ExpandMore as ExpandMoreIcon,
  Task as TaskIcon,
  Add as AddTaskIcon,
  Edit as EditTaskIcon,
  Delete as DeleteTaskIcon,
  AccessTime as TimeIcon,
  Repeat as RepeatIcon,
} from '@mui/icons-material';
import { useProgram, Program, ProgramTask } from '../contexts/ProgramContext';
import ProgramChangeDialog from './ProgramChangeDialog';

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
    handleProgramChange,
    getProgramTasks,
    createProgramTask,
    updateProgramTask,
    deleteProgramTask,
  } = useProgram();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingProgram, setEditingProgram] = useState<Program | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [programTasks, setProgramTasks] = useState<ProgramTask[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [openTaskDialog, setOpenTaskDialog] = useState(false);
  const [editingTask, setEditingTask] = useState<ProgramTask | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [expandedProgram, setExpandedProgram] = useState<number | false>(false);
  const [changeDialogOpen, setChangeDialogOpen] = useState(false);
  const [changeData, setChangeData] = useState<any>(null);
  const [changeLoading, setChangeLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    duration_days: 40,
    is_active: true,
    is_default: false,
  });

  const [taskFormData, setTaskFormData] = useState({
    day: 0,
    task_type: 'daily' as 'daily' | 'weekly' | 'one_time' | 'recurring',
    title: '',
    description: '',
    instructions: '',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'critical',
    estimated_duration: 30,
    is_required: true,
    requires_confirmation: false,
    recurring_days: [] as number[],
  });

  useEffect(() => {
    fetchPrograms();
  }, [fetchPrograms]);

  const loadProgramTasks = async (program: Program) => {
    setTasksLoading(true);
    try {
      const tasks = await getProgramTasks(program.id);
      setProgramTasks(tasks);
    } catch (err) {
      // Error loading program tasks
    } finally {
      setTasksLoading(false);
    }
  };

  const handleProgramSelect = (program: Program) => {
    setSelectedProgram(program);
    setTabValue(0);
    loadProgramTasks(program);
  };

  const handleOpenTaskDialog = (program: Program, task?: ProgramTask) => {
    if (task) {
      setEditingTask(task);
      setTaskFormData({
        day: task.day,
        task_type: task.task_type,
        title: task.title,
        description: task.description,
        instructions: task.instructions,
        priority: task.priority,
        estimated_duration: task.estimated_duration,
        is_required: task.is_required,
        requires_confirmation: task.requires_confirmation,
        recurring_days: task.recurring_days,
      });
    } else {
      setEditingTask(null);
      setTaskFormData({
        day: 0,
        task_type: 'daily',
        title: '',
        description: '',
        instructions: '',
        priority: 'medium',
        estimated_duration: 30,
        is_required: true,
        requires_confirmation: false,
        recurring_days: [],
      });
    }
    setOpenTaskDialog(true);
  };

  const handleTaskSubmit = async () => {
    if (!selectedProgram) return;

    const success = editingTask
      ? await updateProgramTask(editingTask.id, taskFormData)
      : await createProgramTask(selectedProgram.id, taskFormData);

    if (success) {
      setOpenTaskDialog(false);
      loadProgramTasks(selectedProgram);
    }
  };

  const handleTaskDelete = async (task: ProgramTask) => {
    if (window.confirm(`Are you sure you want to delete "${task.title}"?`)) {
      const success = await deleteProgramTask(task.id);
      if (success && selectedProgram) {
        loadProgramTasks(selectedProgram);
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

  const getTaskTypeIcon = (taskType: string) => {
    switch (taskType) {
      case 'recurring': return <RepeatIcon />;
      case 'daily': return <ScheduleIcon />;
      case 'weekly': return <ScheduleIcon />;
      case 'one_time': return <TaskIcon />;
      default: return <TaskIcon />;
    }
  };

  const groupTasksByDay = (tasks: ProgramTask[]) => {
    const grouped: { [key: number]: ProgramTask[] } = {};
    tasks.forEach(task => {
      if (!grouped[task.day]) {
        grouped[task.day] = [];
      }
      grouped[task.day].push(task);
    });
    return grouped;
  };

  const handleChangeDialogClose = () => {
    setChangeDialogOpen(false);
    setChangeData(null);
  };

  const handleChangeChoice = async (choice: 'retroactive' | 'next_flock') => {
    if (!changeData?.change_log_id) return;

    setChangeLoading(true);
    try {
      const success = await handleProgramChange(changeData.change_log_id, choice);
      if (success) {
        handleChangeDialogClose();
        // Refresh programs to show updated data
        fetchPrograms();
      }
    } catch (error) {
      // Error handling program change
    } finally {
      setChangeLoading(false);
    }
  };

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
    if (editingProgram) {
      const result = await updateProgram(editingProgram.id, formData);
      if (result.success) {
        handleCloseDialog();
        fetchPrograms();
        
        // Check if there are program changes that need user decision
        if (result.changeData) {
          setChangeData(result.changeData);
          setChangeDialogOpen(true);
        }
      }
    } else {
      const success = await createProgram(formData);
      if (success) {
        handleCloseDialog();
        fetchPrograms();
      }
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

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Programs Overview" />
          {selectedProgram && <Tab label={`Tasks - ${selectedProgram.name}`} />}
        </Tabs>
      </Box>

      {tabValue === 0 && (
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
                      <Tooltip title="View Tasks">
                        <IconButton size="small" onClick={() => handleProgramSelect(program)}>
                          <TaskIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit Program">
                        <IconButton size="small" onClick={() => handleOpenDialog(program)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Copy Program">
                        <IconButton size="small" onClick={() => handleCopy(program)}>
                          <CopyIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete Program">
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
      )}

      {tabValue === 1 && selectedProgram && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">
              Tasks for {selectedProgram.name}
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddTaskIcon />}
              onClick={() => handleOpenTaskDialog(selectedProgram)}
            >
              Add Task
            </Button>
          </Box>

          {tasksLoading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <Box>
              {programTasks.length === 0 ? (
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No tasks found
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    This program doesn&apos;t have any tasks yet. Add some tasks to get started.
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddTaskIcon />}
                    onClick={() => handleOpenTaskDialog(selectedProgram)}
                  >
                    Add First Task
                  </Button>
                </Paper>
              ) : (
                <Box>
                  {Object.entries(groupTasksByDay(programTasks))
                    .sort(([a], [b]) => parseInt(a) - parseInt(b))
                    .map(([day, tasks]) => (
                      <Accordion key={day} expanded={expandedProgram === parseInt(day)} onChange={() => setExpandedProgram(expandedProgram === parseInt(day) ? false : parseInt(day))}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Box display="flex" alignItems="center" gap={2} width="100%">
                            <Typography variant="h6">
                              Day {day === '-1' ? 'Setup' : day}
                            </Typography>
                            <Badge badgeContent={tasks.length} color="primary">
                              <TaskIcon />
                            </Badge>
                            <Box flexGrow={1} />
                            <Typography variant="body2" color="text.secondary">
                              {tasks.length} task{tasks.length !== 1 ? 's' : ''}
                            </Typography>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <List>
                            {tasks.map((task) => (
                              <ListItem key={task.id} divider>
                                <ListItemText
                                  primary={
                                    <Box display="flex" alignItems="center" gap={1}>
                                      {getTaskTypeIcon(task.task_type)}
                                      <Typography variant="subtitle1">
                                        {task.title}
                                      </Typography>
                                      <Chip
                                        label={task.priority}
                                        color={getPriorityColor(task.priority)}
                                        size="small"
                                      />
                                      {task.is_recurring && (
                                        <Chip
                                          icon={<RepeatIcon />}
                                          label="Recurring"
                                          size="small"
                                          variant="outlined"
                                        />
                                      )}
                                    </Box>
                                  }
                                  secondary={
                                    <Box>
                                      <Typography variant="body2" color="text.secondary" paragraph>
                                        {task.description}
                                      </Typography>
                                      <Box display="flex" gap={1} alignItems="center">
                                        <Chip
                                          icon={<TimeIcon />}
                                          label={`${task.estimated_duration} min`}
                                          size="small"
                                          variant="outlined"
                                        />
                                        {task.is_required && (
                                          <Chip
                                            label="Required"
                                            size="small"
                                            color="error"
                                            variant="outlined"
                                          />
                                        )}
                                        {task.requires_confirmation && (
                                          <Chip
                                            label="Confirmation Required"
                                            size="small"
                                            color="warning"
                                            variant="outlined"
                                          />
                                        )}
                                      </Box>
                                    </Box>
                                  }
                                />
                                <ListItemSecondaryAction>
                                  <Box>
                                    <Tooltip title="Edit Task">
                                      <IconButton
                                        size="small"
                                        onClick={() => handleOpenTaskDialog(selectedProgram, task)}
                                      >
                                        <EditTaskIcon />
                                      </IconButton>
                                    </Tooltip>
                                    <Tooltip title="Delete Task">
                                      <IconButton
                                        size="small"
                                        onClick={() => handleTaskDelete(task)}
                                        color="error"
                                      >
                                        <DeleteTaskIcon />
                                      </IconButton>
                                    </Tooltip>
                                  </Box>
                                </ListItemSecondaryAction>
                              </ListItem>
                            ))}
                          </List>
                        </AccordionDetails>
                      </Accordion>
                    ))}
                </Box>
              )}
            </Box>
          )}
        </Box>
      )}

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

      {/* Task Dialog */}
      <Dialog open={openTaskDialog} onClose={() => setOpenTaskDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingTask ? 'Edit Task' : 'Add New Task'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Task Title"
                value={taskFormData.title}
                onChange={(e) => setTaskFormData({ ...taskFormData, title: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Day"
                type="number"
                value={taskFormData.day}
                onChange={(e) => setTaskFormData({ ...taskFormData, day: parseInt(e.target.value) || 0 })}
                inputProps={{ min: -1, max: 365 }}
                helperText="-1 for setup day, 0+ for program days"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Task Type</InputLabel>
                <Select
                  value={taskFormData.task_type}
                  onChange={(e) => setTaskFormData({ ...taskFormData, task_type: e.target.value as any })}
                >
                  <MenuItem value="daily">Daily</MenuItem>
                  <MenuItem value="weekly">Weekly</MenuItem>
                  <MenuItem value="one_time">One Time</MenuItem>
                  <MenuItem value="recurring">Recurring</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={taskFormData.priority}
                  onChange={(e) => setTaskFormData({ ...taskFormData, priority: e.target.value as any })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={taskFormData.description}
                onChange={(e) => setTaskFormData({ ...taskFormData, description: e.target.value })}
                multiline
                rows={2}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Instructions"
                value={taskFormData.instructions}
                onChange={(e) => setTaskFormData({ ...taskFormData, instructions: e.target.value })}
                multiline
                rows={3}
                placeholder="Step-by-step instructions for this task..."
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Estimated Duration (minutes)"
                type="number"
                value={taskFormData.estimated_duration}
                onChange={(e) => setTaskFormData({ ...taskFormData, estimated_duration: parseInt(e.target.value) || 30 })}
                inputProps={{ min: 1, max: 480 }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={taskFormData.is_required}
                      onChange={(e) => setTaskFormData({ ...taskFormData, is_required: e.target.checked })}
                    />
                  }
                  label="Required Task"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={taskFormData.requires_confirmation}
                      onChange={(e) => setTaskFormData({ ...taskFormData, requires_confirmation: e.target.checked })}
                    />
                  }
                  label="Requires Confirmation"
                />
              </Box>
            </Grid>
            {taskFormData.task_type === 'recurring' && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Recurring Days (0=Monday, 6=Sunday)
                </Typography>
                <Box display="flex" gap={1} flexWrap="wrap">
                  {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].map((day, index) => (
                    <Chip
                      key={day}
                      label={day}
                      color={taskFormData.recurring_days.includes(index) ? 'primary' : 'default'}
                      onClick={() => {
                        const newDays = taskFormData.recurring_days.includes(index)
                          ? taskFormData.recurring_days.filter(d => d !== index)
                          : [...taskFormData.recurring_days, index];
                        setTaskFormData({ ...taskFormData, recurring_days: newDays });
                      }}
                      variant={taskFormData.recurring_days.includes(index) ? 'filled' : 'outlined'}
                    />
                  ))}
                </Box>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenTaskDialog(false)}>Cancel</Button>
          <Button onClick={handleTaskSubmit} variant="contained">
            {editingTask ? 'Update Task' : 'Add Task'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Program Change Dialog */}
      <ProgramChangeDialog
        open={changeDialogOpen}
        onClose={handleChangeDialogClose}
        changeData={changeData || { change_detected: false }}
        onHandleChange={handleChangeChoice}
        loading={changeLoading}
      />
    </Box>
  );
};

export default ProgramManager;
