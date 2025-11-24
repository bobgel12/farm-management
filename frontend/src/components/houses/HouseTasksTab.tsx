import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Grid,
  Button,
} from '@mui/material';
import {
  CheckCircle,
  Pending,
  Schedule,
  Assignment,
} from '@mui/icons-material';

interface Task {
  id: number;
  day_offset: number;
  task_name: string;
  description: string;
  task_type: string;
  is_completed: boolean;
  completed_at?: string;
  completed_by?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface HouseTasksTabProps {
  tasks: {
    all: Task[];
    today: Task[];
    upcoming: Task[];
    past: Task[];
    completed: Task[];
    total: number;
    completed_count: number;
    pending_count: number;
  };
  currentDay?: number | null;
  loading?: boolean;
}

const HouseTasksTab: React.FC<HouseTasksTabProps> = ({ tasks, currentDay, loading }) => {
  const [tabValue, setTabValue] = useState(0);

  const getTaskTypeColor = (taskType: string) => {
    switch (taskType?.toLowerCase()) {
      case 'setup': return 'primary';
      case 'daily': return 'success';
      case 'exit': return 'warning';
      case 'cleanup': return 'default';
      case 'special': return 'info';
      default: return 'default';
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const renderTaskRow = (task: Task) => (
    <TableRow key={task.id} hover>
      <TableCell>
        <Box display="flex" alignItems="center" gap={1}>
          {task.is_completed ? (
            <CheckCircle color="success" fontSize="small" />
          ) : (
            <Pending color="action" fontSize="small" />
          )}
          <Typography variant="body2" fontWeight={task.is_completed ? 'normal' : 600}>
            Day {task.day_offset}
          </Typography>
        </Box>
      </TableCell>
      <TableCell>
        <Typography variant="body2" fontWeight={500}>
          {task.task_name}
        </Typography>
        {task.description && task.description !== task.task_name && (
          <Typography variant="caption" color="textSecondary">
            {task.description}
          </Typography>
        )}
      </TableCell>
      <TableCell>
        <Chip
          label={task.task_type || 'daily'}
          color={getTaskTypeColor(task.task_type)}
          size="small"
        />
      </TableCell>
      <TableCell>
        {task.is_completed ? (
          <Chip
            label="Completed"
            color="success"
            size="small"
            icon={<CheckCircle />}
          />
        ) : (
          <Chip
            label="Pending"
            color="default"
            size="small"
            icon={<Pending />}
          />
        )}
      </TableCell>
      <TableCell>
        {task.completed_at ? (
          <Box>
            <Typography variant="caption" display="block">
              {formatDate(task.completed_at)}
            </Typography>
            {task.completed_by && (
              <Typography variant="caption" color="textSecondary">
                by {task.completed_by}
              </Typography>
            )}
          </Box>
        ) : (
          <Typography variant="caption" color="textSecondary">
            Not completed
          </Typography>
        )}
      </TableCell>
      <TableCell>
        {task.notes && (
          <Typography variant="caption" color="textSecondary" noWrap>
            {task.notes}
          </Typography>
        )}
      </TableCell>
    </TableRow>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const tabs = [
    { label: 'All Tasks', count: tasks.total, icon: <Assignment /> },
    { label: 'Today', count: tasks.today.length, icon: <Schedule /> },
    { label: 'Upcoming', count: tasks.upcoming.length, icon: <Schedule /> },
    { label: 'Past', count: tasks.past.length, icon: <Schedule /> },
    { label: 'Completed', count: tasks.completed_count, icon: <CheckCircle /> },
  ];

  const getTasksForTab = () => {
    switch (tabValue) {
      case 0: return tasks.all;
      case 1: return tasks.today;
      case 2: return tasks.upcoming;
      case 3: return tasks.past;
      case 4: return tasks.completed;
      default: return tasks.all;
    }
  };

  const displayTasks = getTasksForTab();

  return (
    <Box>
      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="textSecondary" display="block">
                Total Tasks
              </Typography>
              <Typography variant="h4">
                {tasks.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="textSecondary" display="block">
                Completed
              </Typography>
              <Typography variant="h4" color="success.main">
                {tasks.completed_count}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="textSecondary" display="block">
                Pending
              </Typography>
              <Typography variant="h4" color="warning.main">
                {tasks.pending_count}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="caption" color="textSecondary" display="block">
                Today&apos;s Tasks
              </Typography>
              <Typography variant="h4" color="primary.main">
                {tasks.today.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Current Day Info */}
      {currentDay !== null && currentDay !== undefined && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            <strong>Current Day:</strong> Day {currentDay} of the program
          </Typography>
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs
          value={tabValue}
          onChange={(_, newValue) => setTabValue(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {tabs.map((tab, index) => (
            <Tab
              key={index}
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  {tab.icon}
                  <span>{tab.label}</span>
                  {tab.count > 0 && (
                    <Chip
                      label={tab.count}
                      size="small"
                      sx={{ ml: 0.5, height: 20, minWidth: 20 }}
                    />
                  )}
                </Box>
              }
            />
          ))}
        </Tabs>
      </Paper>

      {/* Tasks Table */}
      {displayTasks.length === 0 ? (
        <Alert severity="info">
          <Typography variant="body2">
            No tasks found for this category. Tasks are generated based on the farm&apos;s assigned program.
          </Typography>
        </Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Day</TableCell>
                <TableCell>Task Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Completed</TableCell>
                <TableCell>Notes</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {displayTasks.map(renderTaskRow)}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default HouseTasksTab;

