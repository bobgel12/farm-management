import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Agriculture as FarmIcon,
  Home as HomeIcon,
  Assignment as TaskIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { useFarm } from '../contexts/FarmContext.tsx';
import { useTask } from '../contexts/TaskContext.tsx';
import api from '../services/api.ts';

interface DashboardData {
  total_farms: number;
  total_houses: number;
  active_houses: number;
  farms: Array<{
    id: number;
    name: string;
    total_houses: number;
    active_houses: number;
  }>;
}

interface TaskDashboardData {
  total_incomplete_tasks: number;
  today_tasks: Array<{
    id: number;
    house_name: string;
    farm_name: string;
    task_name: string;
    description: string;
    task_type: string;
  }>;
  overdue_tasks: Array<{
    id: number;
    house_name: string;
    farm_name: string;
    task_name: string;
    description: string;
    day_offset: number;
    days_overdue: number;
  }>;
  overdue_count: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { farms, loading: farmLoading } = useFarm();
  const { completeTask } = useTask();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [taskData, setTaskData] = useState<TaskDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [farmResponse, taskResponse] = await Promise.all([
        api.get('/dashboard/'),
        api.get('/tasks/dashboard/')
      ]);
      setDashboardData(farmResponse.data);
      setTaskData(taskResponse.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteTask = async (taskId: number) => {
    const success = await completeTask(taskId, 'Dashboard');
    if (success) {
      fetchDashboardData(); // Refresh data
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
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Overview Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <FarmIcon color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Farms
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData?.total_farms || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <HomeIcon color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Houses
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData?.total_houses || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUpIcon color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Houses
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData?.active_houses || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TaskIcon color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Incomplete Tasks
                  </Typography>
                  <Typography variant="h4">
                    {taskData?.total_incomplete_tasks || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Overdue Tasks Alert */}
        {taskData && taskData.overdue_count > 0 && (
          <Grid item xs={12}>
            <Alert severity="warning" icon={<WarningIcon />}>
              <Typography variant="h6">
                {taskData.overdue_count} Overdue Task{taskData.overdue_count > 1 ? 's' : ''}
              </Typography>
              <Typography variant="body2">
                Please review and complete overdue tasks to maintain proper chicken care schedule.
              </Typography>
            </Alert>
          </Grid>
        )}

        {/* Today's Tasks */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Today's Tasks
              </Typography>
              {taskData && taskData.today_tasks.length > 0 ? (
                <List>
                  {taskData.today_tasks.slice(0, 5).map((task) => (
                    <ListItem key={task.id} divider>
                      <ListItemText
                        primary={task.task_name}
                        secondary={`${task.farm_name} - ${task.house_name}`}
                      />
                      <ListItemSecondaryAction>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleCompleteTask(task.id)}
                        >
                          Complete
                        </Button>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">
                  No tasks for today
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Farms Overview */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Farms Overview
              </Typography>
              {dashboardData && dashboardData.farms.length > 0 ? (
                <List>
                  {dashboardData.farms.map((farm) => (
                    <ListItem key={farm.id} divider>
                      <ListItemText
                        primary={farm.name}
                        secondary={`${farm.active_houses} active houses`}
                      />
                      <ListItemSecondaryAction>
                        <Button
                          size="small"
                          onClick={() => navigate(`/farms/${farm.id}`)}
                        >
                          View
                        </Button>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">
                  No farms available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Button
                  variant="contained"
                  startIcon={<FarmIcon />}
                  onClick={() => navigate('/farms')}
                >
                  Manage Farms
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<HomeIcon />}
                  onClick={() => navigate('/farms')}
                >
                  View Houses
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<TaskIcon />}
                  onClick={() => navigate('/farms')}
                >
                  View Tasks
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
