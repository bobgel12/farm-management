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
} from '@mui/material';
import { Assignment as TaskIcon } from '@mui/icons-material';
import { useTask } from '../contexts/TaskContext.tsx';
import api from '../services/api.ts';

const HouseDetail: React.FC = () => {
  const { houseId } = useParams<{ houseId: string }>();
  const [house, setHouse] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { todayTasks, upcomingTasks, fetchTodayTasks, fetchUpcomingTasks, generateTasks } = useTask();

  useEffect(() => {
    if (houseId) {
      fetchHouseDetails();
      fetchTodayTasks(parseInt(houseId));
      fetchUpcomingTasks(parseInt(houseId), 7);
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
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          {house.farm_name} - House {house.house_number}
        </Typography>
        
        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Status
                </Typography>
                <Chip
                  label={house.status}
                  color={getStatusColor(house.status) as any}
                />
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Current Day
                </Typography>
                <Typography variant="h6">
                  {house.current_day !== null ? `Day ${house.current_day}` : 'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Chicken In Date
                </Typography>
                <Typography variant="h6">
                  {new Date(house.chicken_in_date).toLocaleDateString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Chicken Out Date
                </Typography>
                <Typography variant="h6">
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

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Tasks</Typography>
        <Button
          variant="contained"
          startIcon={<TaskIcon />}
          onClick={handleGenerateTasks}
        >
          Generate Tasks
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Today's Tasks
              </Typography>
              {todayTasks.length > 0 ? (
                <Box>
                  {todayTasks.map((task) => (
                    <Box key={task.id} mb={2} p={2} border="1px solid #e0e0e0" borderRadius={1}>
                      <Typography variant="subtitle1" gutterBottom>
                        {task.task_name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        {task.description}
                      </Typography>
                      <Chip
                        label={task.task_type}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography color="textSecondary">
                  No tasks for today
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Upcoming Tasks (Next 7 Days)
              </Typography>
              {upcomingTasks.length > 0 ? (
                <Box>
                  {upcomingTasks.slice(0, 5).map((task) => (
                    <Box key={task.id} mb={2} p={2} border="1px solid #e0e0e0" borderRadius={1}>
                      <Typography variant="subtitle1" gutterBottom>
                        {task.task_name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Day {task.day_offset} - {task.description}
                      </Typography>
                      <Chip
                        label={task.task_type}
                        size="small"
                        color="secondary"
                        variant="outlined"
                      />
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography color="textSecondary">
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
