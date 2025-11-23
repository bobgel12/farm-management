import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  CheckCircle as CompleteIcon,
  Pets as PoultryIcon,
  TrendingUp as TrendingUpIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useFlock } from '../../contexts/FlockContext';
import { FlockPerformance } from '../../types';
import dayjs from 'dayjs';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const FlockDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentFlock,
    performanceRecords,
    loading,
    error,
    fetchFlock,
    fetchFlockPerformance,
    fetchFlockSummary,
    completeFlock,
  } = useFlock();

  const [activeTab, setActiveTab] = useState(0);
  const [summary, setSummary] = useState<any>(null);
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    if (id) {
      fetchFlock(parseInt(id));
      fetchFlockPerformance(parseInt(id));
      fetchFlockSummary(parseInt(id)).then(setSummary);
    }
  }, [id, fetchFlock, fetchFlockPerformance, fetchFlockSummary]);

  const handleComplete = async () => {
    if (!currentFlock) return;
    
    if (window.confirm(`Are you sure you want to complete flock ${currentFlock.batch_number}?`)) {
      setCompleting(true);
      try {
        await completeFlock(currentFlock.id);
        navigate('/flocks');
      } catch (err) {
        console.error('Error completing flock:', err);
      } finally {
        setCompleting(false);
      }
    }
  };

  if (loading && !currentFlock) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading flock details...</Typography>
      </Box>
    );
  }

  if (error || !currentFlock) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          {error || 'Flock not found'}
        </Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/flocks')}
          sx={{ mt: 2 }}
        >
          Back to Flocks
        </Button>
      </Box>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'growing':
      case 'production':
        return 'primary';
      case 'arrival':
        return 'info';
      case 'harvesting':
        return 'warning';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/flocks')}
          >
            Back
          </Button>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 600 }}>
              Flock: {currentFlock.batch_number}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {currentFlock.flock_code} • {currentFlock.house_name}
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/flocks/${id}/edit`)}
          >
            Edit
          </Button>
          {currentFlock.is_active && currentFlock.status !== 'completed' && (
            <Button
              variant="contained"
              color="success"
              startIcon={<CompleteIcon />}
              onClick={handleComplete}
              disabled={completing}
            >
              Complete Flock
            </Button>
          )}
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Status
              </Typography>
              <Chip
                label={currentFlock.status}
                color={getStatusColor(currentFlock.status) as any}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Age
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {currentFlock.current_age_days || 0} days
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Current Count
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {currentFlock.current_chicken_count || currentFlock.initial_chicken_count}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Mortality Rate
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                {currentFlock.mortality_rate !== undefined
                  ? `${currentFlock.mortality_rate.toFixed(2)}%`
                  : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            <Tab label="Overview" icon={<PoultryIcon />} iconPosition="start" />
            <Tab label="Performance" icon={<TrendingUpIcon />} iconPosition="start" />
            <Tab label="History" icon={<TimelineIcon />} iconPosition="start" />
            <Tab label="Summary" icon={<AssessmentIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        <CardContent>
          <TabPanel value={activeTab} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Basic Information
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Batch Number
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentFlock.batch_number}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Flock Code
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentFlock.flock_code}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    House
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentFlock.house_name}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Breed
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentFlock.breed_name || 'Not specified'}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Dates & Counts
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Arrival Date
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentFlock.arrival_date
                      ? dayjs(currentFlock.arrival_date).format('MMMM DD, YYYY')
                      : 'N/A'}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Expected Harvest
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentFlock.expected_harvest_date
                      ? dayjs(currentFlock.expected_harvest_date).format('MMMM DD, YYYY')
                      : 'N/A'}
                    {currentFlock.days_until_harvest !== undefined && (
                      <Chip
                        label={`${currentFlock.days_until_harvest} days remaining`}
                        size="small"
                        color="info"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Initial Count
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentFlock.initial_chicken_count.toLocaleString()}
                  </Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    Current Count
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {currentFlock.current_chicken_count?.toLocaleString() || currentFlock.initial_chicken_count.toLocaleString()}
                  </Typography>
                </Box>
              </Grid>
              {currentFlock.notes && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Notes
                  </Typography>
                  <Typography variant="body1">{currentFlock.notes}</Typography>
                </Grid>
              )}
            </Grid>
          </TabPanel>

          <TabPanel value={activeTab} index={1}>
            <Typography variant="h6" gutterBottom>
              Performance Metrics
            </Typography>
            {performanceRecords.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography color="text.secondary">
                  No performance records yet. Performance data will appear here once recorded.
                </Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Age (Days)</TableCell>
                      <TableCell>Count</TableCell>
                      <TableCell>Avg Weight (g)</TableCell>
                      <TableCell>FCR</TableCell>
                      <TableCell>Mortality Rate</TableCell>
                      <TableCell>Livability</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {performanceRecords.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell>
                          {dayjs(record.record_date).format('MMM DD, YYYY')}
                        </TableCell>
                        <TableCell>{record.flock_age_days}</TableCell>
                        <TableCell>{record.current_chicken_count.toLocaleString()}</TableCell>
                        <TableCell>
                          {record.average_weight_grams
                            ? `${record.average_weight_grams.toFixed(1)}`
                            : 'N/A'}
                        </TableCell>
                        <TableCell>
                          {record.feed_conversion_ratio
                            ? record.feed_conversion_ratio.toFixed(2)
                            : 'N/A'}
                        </TableCell>
                        <TableCell>
                          {record.mortality_rate
                            ? `${record.mortality_rate.toFixed(2)}%`
                            : 'N/A'}
                        </TableCell>
                        <TableCell>
                          {record.livability
                            ? `${record.livability.toFixed(2)}%`
                            : 'N/A'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </TabPanel>

          <TabPanel value={activeTab} index={2}>
            <Typography variant="h6" gutterBottom>
              Flock History
            </Typography>
            <Typography color="text.secondary">
              Historical timeline coming soon...
            </Typography>
          </TabPanel>

          <TabPanel value={activeTab} index={3}>
            <Typography variant="h6" gutterBottom>
              Summary Statistics
            </Typography>
            {summary ? (
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="subtitle2" color="text.secondary">
                        Performance Records
                      </Typography>
                      <Typography variant="h6">
                        {summary.performance_records_count || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                {summary.latest_fcr && (
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="text.secondary">
                          Latest FCR
                        </Typography>
                        <Typography variant="h6">
                          {summary.latest_fcr.toFixed(2)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                )}
              </Grid>
            ) : (
              <Typography color="text.secondary">
                Loading summary...
              </Typography>
            )}
          </TabPanel>
        </CardContent>
      </Card>
    </Box>
  );
};

export default FlockDetail;

