import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Avatar,
  LinearProgress,
  Chip,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Agriculture as FarmIcon,
  Home as HouseIcon,
  People as WorkerIcon,
  Assignment as TaskIcon,
  Schedule as ProgramIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
import { useFarm } from '../../contexts/FarmContext';
import { useTask } from '../../contexts/TaskContext';
import { useWorker } from '../../contexts/WorkerContext';
import { useProgram } from '../../contexts/ProgramContext';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  trend?: {
    value: number;
    isPositive: boolean;
  };
  subtitle?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, color, trend, subtitle }) => (
  <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
    <CardContent>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Avatar sx={{ bgcolor: `${color}.main`, width: 48, height: 48 }}>
          {icon}
        </Avatar>
        {trend && (
          <Chip
            icon={<TrendingUpIcon />}
            label={`${trend.isPositive ? '+' : ''}${trend.value}%`}
            color={trend.isPositive ? 'success' : 'error'}
            size="small"
            variant="outlined"
          />
        )}
      </Box>
      <Typography variant="h4" fontWeight={700} color="text.primary" gutterBottom>
        {value}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {title}
      </Typography>
      {subtitle && (
        <Typography variant="caption" color="text.secondary">
          {subtitle}
        </Typography>
      )}
    </CardContent>
  </Card>
);

interface TaskProgressProps {
  title: string;
  completed: number;
  total: number;
  color: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
}

const TaskProgress: React.FC<TaskProgressProps> = ({ title, completed, total, color }) => {
  const percentage = total > 0 ? (completed / total) * 100 : 0;
  
  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="body2" fontWeight={500}>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {completed}/{total}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={percentage}
        color={color}
        sx={{ height: 8, borderRadius: 4 }}
      />
      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
        {percentage.toFixed(1)}% complete
      </Typography>
    </Box>
  );
};

const ProfessionalDashboard: React.FC = () => {
  const { farms, fetchFarms } = useFarm();
  const { tasks, fetchTasks } = useTask();
  const { workers, fetchWorkers } = useWorker();
  const { programs, fetchPrograms } = useProgram();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchFarms(),
          fetchTasks(),
          fetchWorkers(),
          fetchPrograms(),
        ]);
      } catch (error) {
        console.error('Error loading dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [fetchFarms, fetchTasks, fetchWorkers, fetchPrograms]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <LinearProgress sx={{ width: '100%' }} />
      </Box>
    );
  }

  // Calculate statistics
  const totalFarms = farms?.length || 0;
  const activeFarms = farms?.filter(farm => farm.is_active).length || 0;
  const totalHouses = farms?.reduce((sum, farm) => sum + farm.total_houses, 0) || 0;
  const activeHouses = farms?.reduce((sum, farm) => sum + farm.active_houses, 0) || 0;
  const totalWorkers = workers?.length || 0;
  const activeWorkers = workers?.filter(worker => worker.is_active).length || 0;
  const totalTasks = Array.isArray(tasks) ? tasks.length : 0;
  const completedTasks = Array.isArray(tasks) ? tasks.filter(task => task.is_completed).length : 0;
  const totalPrograms = programs?.length || 0;
  const activePrograms = programs?.filter(program => program.is_active).length || 0;

  // Recent activities (mock data for now)
  const recentActivities = [
    { id: 1, type: 'task', message: 'Task "Feed Check" completed for Farm A', time: '2 hours ago', icon: <CheckCircleIcon />, color: 'success' },
    { id: 2, type: 'farm', message: 'New farm "Green Valley" added', time: '4 hours ago', icon: <FarmIcon />, color: 'primary' },
    { id: 3, type: 'worker', message: 'Worker "John Smith" assigned to Farm B', time: '6 hours ago', icon: <WorkerIcon />, color: 'secondary' },
    { id: 4, type: 'program', message: 'Program "Standard 40-Day" updated', time: '1 day ago', icon: <ProgramIcon />, color: 'warning' },
  ];

  return (
    <Box>
      {/* Header */}
      <Box mb={4}>
        <Typography variant="h4" fontWeight={700} color="text.primary" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Here&apos;s what&apos;s happening with your farms today.
        </Typography>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Farms"
            value={totalFarms}
            icon={<FarmIcon />}
            color="primary"
            subtitle={`${activeFarms} active`}
            trend={{ value: 12, isPositive: true }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Houses"
            value={activeHouses}
            icon={<HouseIcon />}
            color="secondary"
            subtitle={`${totalHouses} total`}
            trend={{ value: 8, isPositive: true }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Workers"
            value={activeWorkers}
            icon={<WorkerIcon />}
            color="success"
            subtitle={`${totalWorkers} total`}
            trend={{ value: 5, isPositive: true }}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Task Programs"
            value={activePrograms}
            icon={<ProgramIcon />}
            color="warning"
            subtitle={`${totalPrograms} total`}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Task Progress */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Task Progress
              </Typography>
              <Box mb={3}>
                <TaskProgress
                  title="Completed Tasks"
                  completed={completedTasks}
                  total={totalTasks}
                  color="success"
                />
              </Box>
              <Box mb={3}>
                <TaskProgress
                  title="Pending Tasks"
                  completed={totalTasks - completedTasks}
                  total={totalTasks}
                  color="warning"
                />
              </Box>
              <Box>
                <TaskProgress
                  title="Program Completion"
                  completed={activePrograms}
                  total={totalPrograms}
                  color="primary"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activities */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6" fontWeight={600}>
                  Recent Activities
                </Typography>
                <Button size="small" color="primary">
                  View All
                </Button>
              </Box>
              <List>
                {recentActivities.map((activity, index) => (
                  <React.Fragment key={activity.id}>
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon sx={{ minWidth: 40 }}>
                        <Avatar sx={{ bgcolor: `${activity.color}.main`, width: 32, height: 32 }}>
                          {activity.icon}
                        </Avatar>
                      </ListItemIcon>
                      <ListItemText
                        primary={activity.message}
                        secondary={activity.time}
                        primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                    {index < recentActivities.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<FarmIcon />}
                    sx={{ py: 2, textTransform: 'none' }}
                  >
                    Add New Farm
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<ProgramIcon />}
                    sx={{ py: 2, textTransform: 'none' }}
                  >
                    Create Program
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<WorkerIcon />}
                    sx={{ py: 2, textTransform: 'none' }}
                  >
                    Add Worker
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<EmailIcon />}
                    sx={{ py: 2, textTransform: 'none' }}
                  >
                    Send Email
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProfessionalDashboard;
