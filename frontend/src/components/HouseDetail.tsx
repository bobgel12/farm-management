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
} from '@mui/material';
import { Assignment as TaskIcon } from '@mui/icons-material';
import { useTask } from '../contexts/TaskContext';
import EmailManager from './EmailManager';
import api from '../services/api';

const HouseDetail: React.FC = () => {
  const { houseId, farmId } = useParams<{ houseId: string; farmId?: string }>();
  const [house, setHouse] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { todayTasks, upcomingTasks, fetchTodayTasks, fetchUpcomingTasks, generateTasks } = useTask();

  const fetchHouseDetails = useCallback(async () => {
    try {
      const url = farmId ? `/farms/${farmId}/houses/${houseId}/` : `/houses/${houseId}/`;
      const response = await api.get(url);
      setHouse(response.data);
    } catch (err) {
      setError('Failed to fetch house details');
      // Error fetching house details
    } finally {
      setLoading(false);
    }
  }, [houseId, farmId]);

  useEffect(() => {
    if (houseId) {
      fetchHouseDetails();
      fetchTodayTasks(parseInt(houseId));
      fetchUpcomingTasks(parseInt(houseId), 7);
    }
  }, [houseId, fetchHouseDetails, fetchTodayTasks, fetchUpcomingTasks]);

  const handleGenerateTasks = async () => {
    if (houseId) {
      const success = await generateTasks(parseInt(houseId));
      if (success) {
        fetchTodayTasks(parseInt(houseId));
        fetchUpcomingTasks(parseInt(houseId), 7);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'setup': return 'warning';
      case 'arrival': return 'info';
      case 'early_care': return 'primary';
      case 'growth': return 'success';
      case 'maturation': return 'warning'; // Changed from secondary to warning for better contrast
      case 'production': return 'success';
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
          {house.farm_name} - House {house.house_number}
        </Typography>
        
        <Grid container spacing={{ xs: 1.5, sm: 2 }} mb={{ xs: 2, sm: 3 }}>
          <Grid item xs={6} sm={6} md={3}>
            <Card sx={{ height: '100%', minHeight: { xs: 100, sm: 120 } }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography 
                  color="textSecondary" 
                  gutterBottom
                  sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                >
                  Status
                </Typography>
                <Chip
                  label={house.status}
                  color={getStatusColor(house.status) as any}
                  variant="filled"
                  sx={{ 
                    fontSize: { xs: '0.75rem', sm: '0.875rem' },
                    fontWeight: 600,
                    textTransform: 'capitalize',
                    '&.MuiChip-colorSecondary': {
                      backgroundColor: '#ff9800',
                      color: 'white',
                      '&:hover': {
                        backgroundColor: '#f57c00',
                      }
                    },
                    '&.MuiChip-colorSuccess': {
                      backgroundColor: '#4caf50',
                      color: 'white',
                    },
                    '&.MuiChip-colorWarning': {
                      backgroundColor: '#ff9800',
                      color: 'white',
                    },
                    '&.MuiChip-colorInfo': {
                      backgroundColor: '#2196f3',
                      color: 'white',
                    },
                    '&.MuiChip-colorPrimary': {
                      backgroundColor: '#2e7d32',
                      color: 'white',
                    },
                    '&.MuiChip-colorError': {
                      backgroundColor: '#f44336',
                      color: 'white',
                    }
                  }}
                />
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={6} sm={6} md={3}>
            <Card sx={{ height: '100%', minHeight: { xs: 100, sm: 120 } }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography 
                  color="textSecondary" 
                  gutterBottom
                  sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                >
                  Current Day
                </Typography>
                <Typography 
                  variant="h6"
                  sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' }, fontWeight: 600 }}
                >
                  {(house.age_days ?? house.current_day) !== null ? `Day ${house.age_days ?? house.current_day}` : 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={6} sm={6} md={3}>
            <Card sx={{ height: '100%', minHeight: { xs: 100, sm: 120 } }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography 
                  color="textSecondary" 
                  gutterBottom
                  sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                >
                  Chicken In Date
                </Typography>
                <Typography 
                  variant="h6"
                  sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, fontWeight: 600 }}
                >
                  {new Date(house.chicken_in_date).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={6} sm={6} md={3}>
            <Card sx={{ height: '100%', minHeight: { xs: 100, sm: 120 } }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography 
                  color="textSecondary" 
                  gutterBottom
                  sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                >
                  Chicken Out Date
                </Typography>
                <Typography 
                  variant="h6"
                  sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, fontWeight: 600 }}
                >
                  {house.chicken_out_date 
                    ? new Date(house.chicken_out_date).toLocaleDateString()
                    : 'Not set'
                  }
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Email Management for this house */}
      <Box mb={4}>
        <EmailManager farmId={farmId ? parseInt(farmId) : house?.farm_id} farmName={house?.farm_name} />
      </Box>

      <Box 
        display="flex" 
        justifyContent="space-between" 
        alignItems={{ xs: 'flex-start', sm: 'center' }} 
        mb={{ xs: 2, sm: 3 }}
        flexDirection={{ xs: 'column', sm: 'row' }}
        gap={{ xs: 2, sm: 0 }}
      >
        <Typography 
          variant="h5"
          sx={{ 
            fontSize: { xs: '1.25rem', sm: '1.5rem' },
            fontWeight: 600
          }}
        >
          Tasks
        </Typography>
        <Button
          variant="contained"
          startIcon={<TaskIcon />}
          onClick={handleGenerateTasks}
          sx={{
            minHeight: { xs: 48, sm: 36 },
            fontSize: { xs: '0.875rem', sm: '0.875rem' },
            width: { xs: '100%', sm: 'auto' }
          }}
        >
          Generate Tasks
        </Button>
      </Box>

      <Grid container spacing={{ xs: 2, sm: 3 }}>
        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ 
                  fontSize: { xs: '1.1rem', sm: '1.25rem' },
                  fontWeight: 600,
                  mb: { xs: 2, sm: 3 }
                }}
              >
                Today&apos;s Tasks
              </Typography>
              {todayTasks.length > 0 ? (
                <Box>
                  {todayTasks.map((task) => (
                    <Box 
                      key={task.id} 
                      mb={2} 
                      p={{ xs: 1.5, sm: 2 }} 
                      border="1px solid #e0e0e0" 
                      borderRadius={1}
                      sx={{ backgroundColor: 'grey.50' }}
                    >
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
                          mb: 1
                        }}
                      >
                        {task.description}
                      </Typography>
                      <Chip
                        label={task.task_type}
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                      />
                    </Box>
                  ))}
                </Box>
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

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ 
                  fontSize: { xs: '1.1rem', sm: '1.25rem' },
                  fontWeight: 600,
                  mb: { xs: 2, sm: 3 }
                }}
              >
                Upcoming Tasks (Next 7 Days)
              </Typography>
              {upcomingTasks.length > 0 ? (
                <Box>
                  {upcomingTasks.slice(0, 5).map((task) => (
                    <Box 
                      key={task.id} 
                      mb={2} 
                      p={{ xs: 1.5, sm: 2 }} 
                      border="1px solid #e0e0e0" 
                      borderRadius={1}
                      sx={{ backgroundColor: 'grey.50' }}
                    >
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
                          mb: 1
                        }}
                      >
                        Day {task.day_offset} - {task.description}
                      </Typography>
                      <Chip
                        label={task.task_type}
                        size="small"
                        color="secondary"
                        variant="outlined"
                        sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}
                      />
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography 
                  color="textSecondary"
                  sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                >
                  No upcoming tasks
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HouseDetail;
