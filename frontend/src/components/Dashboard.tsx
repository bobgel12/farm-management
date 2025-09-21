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
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { useFarm } from '../contexts/FarmContext';
import { useTask } from '../contexts/TaskContext';
import EmailManager from './EmailManager';
import api from '../services/api';

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
      <Typography 
        variant="h4" 
        gutterBottom
        sx={{ 
          fontSize: { xs: '1.75rem', sm: '2.125rem' },
          fontWeight: 600,
          mb: { xs: 2, sm: 3 }
        }}
      >
        Dashboard
      </Typography>
      
      <Grid container spacing={{ xs: 2, sm: 3 }}>
        {/* Overview Cards */}
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ height: '100%', minHeight: { xs: 120, sm: 140 } }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Box display="flex" alignItems="center" flexDirection={{ xs: 'column', sm: 'row' }} textAlign={{ xs: 'center', sm: 'left' }}>
                <FarmIcon color="primary" sx={{ mr: { xs: 0, sm: 1 }, mb: { xs: 1, sm: 0 }, fontSize: { xs: 32, sm: 40 } }} />
                <Box>
                  <Typography 
                    color="textSecondary" 
                    gutterBottom
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    Total Farms
                  </Typography>
                  <Typography 
                    variant="h4"
                    sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' }, fontWeight: 600 }}
                  >
                    {dashboardData?.total_farms || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ height: '100%', minHeight: { xs: 120, sm: 140 } }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Box display="flex" alignItems="center" flexDirection={{ xs: 'column', sm: 'row' }} textAlign={{ xs: 'center', sm: 'left' }}>
                <HomeIcon color="primary" sx={{ mr: { xs: 0, sm: 1 }, mb: { xs: 1, sm: 0 }, fontSize: { xs: 32, sm: 40 } }} />
                <Box>
                  <Typography 
                    color="textSecondary" 
                    gutterBottom
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    Total Houses
                  </Typography>
                  <Typography 
                    variant="h4"
                    sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' }, fontWeight: 600 }}
                  >
                    {dashboardData?.total_houses || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ height: '100%', minHeight: { xs: 120, sm: 140 } }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Box display="flex" alignItems="center" flexDirection={{ xs: 'column', sm: 'row' }} textAlign={{ xs: 'center', sm: 'left' }}>
                <TrendingUpIcon color="primary" sx={{ mr: { xs: 0, sm: 1 }, mb: { xs: 1, sm: 0 }, fontSize: { xs: 32, sm: 40 } }} />
                <Box>
                  <Typography 
                    color="textSecondary" 
                    gutterBottom
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    Active Houses
                  </Typography>
                  <Typography 
                    variant="h4"
                    sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' }, fontWeight: 600 }}
                  >
                    {dashboardData?.active_houses || 0}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={6} sm={6} md={3}>
          <Card sx={{ height: '100%', minHeight: { xs: 120, sm: 140 } }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Box display="flex" alignItems="center" flexDirection={{ xs: 'column', sm: 'row' }} textAlign={{ xs: 'center', sm: 'left' }}>
                <TaskIcon color="primary" sx={{ mr: { xs: 0, sm: 1 }, mb: { xs: 1, sm: 0 }, fontSize: { xs: 32, sm: 40 } }} />
                <Box>
                  <Typography 
                    color="textSecondary" 
                    gutterBottom
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    Incomplete Tasks
                  </Typography>
                  <Typography 
                    variant="h4"
                    sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' }, fontWeight: 600 }}
                  >
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
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' }, fontWeight: 600 }}
              >
                Today&apos;s Tasks
              </Typography>
              {taskData && taskData.today_tasks.length > 0 ? (
                <List sx={{ p: 0 }}>
                  {taskData.today_tasks.slice(0, 5).map((task) => (
                    <ListItem 
                      key={task.id} 
                      divider
                      sx={{ 
                        px: 0,
                        py: { xs: 1.5, sm: 2 },
                        flexDirection: { xs: 'column', sm: 'row' },
                        alignItems: { xs: 'flex-start', sm: 'center' }
                      }}
                    >
                      <ListItemText
                        primary={task.task_name}
                        secondary={`${task.farm_name} - ${task.house_name}`}
                        primaryTypographyProps={{
                          fontSize: { xs: '0.9rem', sm: '1rem' },
                          fontWeight: 500
                        }}
                        secondaryTypographyProps={{
                          fontSize: { xs: '0.75rem', sm: '0.875rem' }
                        }}
                        sx={{ mb: { xs: 1, sm: 0 } }}
                      />
                      <ListItemSecondaryAction sx={{ position: { xs: 'static', sm: 'absolute' }, right: { xs: 0, sm: 16 } }}>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleCompleteTask(task.id)}
                          sx={{ 
                            minWidth: { xs: '100%', sm: 'auto' },
                            fontSize: { xs: '0.75rem', sm: '0.875rem' }
                          }}
                        >
                          Complete
                        </Button>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography 
                  color="textSecondary"
                  sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                >
                  No tasks for today
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Farms Overview */}
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%', boxShadow: 2 }}>
            <CardContent sx={{ p: { xs: 2.5, sm: 3 } }}>
              <Box display="flex" alignItems="center" mb={2}>
                <FarmIcon color="primary" sx={{ mr: 1.5, fontSize: { xs: 24, sm: 28 } }} />
                <Typography 
                  variant="h6" 
                  sx={{ 
                    fontSize: { xs: '1.1rem', sm: '1.25rem' }, 
                    fontWeight: 600,
                    color: 'text.primary'
                  }}
                >
                  Farms Overview
                </Typography>
              </Box>
              {dashboardData && dashboardData.farms.length > 0 ? (
                <Box>
                  {dashboardData.farms.map((farm, index) => (
                    <Box
                      key={farm.id}
                      sx={{
                        p: { xs: 2, sm: 2.5 },
                        mb: index < dashboardData.farms.length - 1 ? 1.5 : 0,
                        borderRadius: 2,
                        border: '1px solid',
                        borderColor: 'divider',
                        backgroundColor: 'background.paper',
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': {
                          borderColor: 'primary.main',
                          boxShadow: 1,
                          transform: 'translateY(-1px)'
                        }
                      }}
                    >
                      <Box display="flex" alignItems="center" justifyContent="space-between">
                        <Box display="flex" alignItems="center" flex={1}>
                          <Box
                            sx={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              backgroundColor: 'success.main',
                              mr: 2,
                              flexShrink: 0
                            }}
                          />
                          <Box flex={1}>
                            <Typography 
                              variant="subtitle1"
                              sx={{ 
                                fontSize: { xs: '0.95rem', sm: '1rem' },
                                fontWeight: 600,
                                color: 'text.primary',
                                mb: 0.5
                              }}
                            >
                              {farm.name}
                            </Typography>
                            <Typography 
                              variant="body2"
                              sx={{ 
                                fontSize: { xs: '0.8rem', sm: '0.875rem' },
                                color: 'text.secondary',
                                display: 'flex',
                                alignItems: 'center'
                              }}
                            >
                              <HomeIcon sx={{ fontSize: 14, mr: 0.5 }} />
                              {farm.active_houses} active houses
                            </Typography>
                          </Box>
                        </Box>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => navigate(`/farms/${farm.id}`)}
                          startIcon={<ArrowForwardIcon sx={{ fontSize: 16 }} />}
                          sx={{ 
                            minWidth: { xs: 'auto', sm: 80 },
                            fontSize: { xs: '0.75rem', sm: '0.875rem' },
                            px: { xs: 1.5, sm: 2 },
                            py: { xs: 0.5, sm: 1 },
                            textTransform: 'none',
                            fontWeight: 500,
                            borderColor: 'primary.main',
                            color: 'primary.main',
                            '&:hover': {
                              backgroundColor: 'primary.main',
                              color: 'white',
                              borderColor: 'primary.main'
                            }
                          }}
                        >
                          View
                        </Button>
                      </Box>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Box 
                  textAlign="center" 
                  py={4}
                  sx={{
                    border: '2px dashed',
                    borderColor: 'divider',
                    borderRadius: 2,
                    backgroundColor: 'grey.50'
                  }}
                >
                  <FarmIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                  <Typography 
                    variant="h6"
                    color="text.secondary"
                    sx={{ fontSize: { xs: '0.95rem', sm: '1rem' }, fontWeight: 500, mb: 1 }}
                  >
                    No farms available
                  </Typography>
                  <Typography 
                    variant="body2"
                    color="text.disabled"
                    sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
                  >
                    Create your first farm to get started
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Email Management */}
        <Grid item xs={12}>
          <EmailManager />
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ fontSize: { xs: '1.1rem', sm: '1.25rem' }, fontWeight: 600 }}
              >
                Quick Actions
              </Typography>
              <Box 
                display="flex" 
                gap={{ xs: 1.5, sm: 2 }} 
                flexWrap="wrap"
                flexDirection={{ xs: 'column', sm: 'row' }}
              >
                <Button
                  variant="contained"
                  startIcon={<FarmIcon />}
                  onClick={() => navigate('/farms')}
                  sx={{ 
                    minHeight: { xs: 48, sm: 36 },
                    fontSize: { xs: '0.875rem', sm: '0.875rem' },
                    flex: { xs: '1', sm: '0 1 auto' }
                  }}
                >
                  Manage Farms
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<HomeIcon />}
                  onClick={() => navigate('/farms')}
                  sx={{ 
                    minHeight: { xs: 48, sm: 36 },
                    fontSize: { xs: '0.875rem', sm: '0.875rem' },
                    flex: { xs: '1', sm: '0 1 auto' }
                  }}
                >
                  View Houses
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<TaskIcon />}
                  onClick={() => navigate('/farms')}
                  sx={{ 
                    minHeight: { xs: 48, sm: 36 },
                    fontSize: { xs: '0.875rem', sm: '0.875rem' },
                    flex: { xs: '1', sm: '0 1 auto' }
                  }}
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
