import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  InputAdornment,
  Select,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Pets as PoultryIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useFlock } from '../../contexts/FlockContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import { Flock } from '../../types';
import dayjs from 'dayjs';

const ProfessionalFlockList: React.FC = () => {
  const navigate = useNavigate();
  const {
    flocks = [],
    breeds = [],
    loading,
    error,
    fetchFlocks,
    fetchBreeds,
    deleteFlock,
  } = useFlock();
  const { currentOrganization } = useOrganization();

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [breedFilter, setBreedFilter] = useState<string>('all');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedFlock, setSelectedFlock] = useState<Flock | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  useEffect(() => {
    // Fetch flocks - organization filter is optional
    const params = currentOrganization ? { organization_id: currentOrganization.id } : {};
    console.log('ProfessionalFlockList: Fetching flocks with params:', params);
    fetchFlocks(params);
    fetchBreeds();
  }, [currentOrganization, fetchFlocks, fetchBreeds]);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, flock: Flock) => {
    setAnchorEl(event.currentTarget);
    setSelectedFlock(flock);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedFlock(null);
  };

  const handleViewFlock = (flock: Flock) => {
    navigate(`/flocks/${flock.id}`);
    handleMenuClose();
  };

  const handleEditFlock = (flock: Flock) => {
    navigate(`/flocks/${flock.id}/edit`);
    handleMenuClose();
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    handleMenuClose();
  };

  const handleDeleteConfirm = async () => {
    if (selectedFlock) {
      await deleteFlock(selectedFlock.id);
      setDeleteDialogOpen(false);
      setSelectedFlock(null);
    }
  };

  const filteredFlocks = (flocks || []).filter((flock) => {
    const matchesSearch =
      flock.batch_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      flock.flock_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      flock.house_name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || flock.status === statusFilter;
    const matchesBreed = breedFilter === 'all' || flock.breed?.toString() === breedFilter;

    return matchesSearch && matchesStatus && matchesBreed;
  });

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

  if (loading && flocks.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2, textAlign: 'center' }}>Loading flocks...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
            Flock Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Track and manage chicken flocks across your organization
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/flocks/new')}
          sx={{ borderRadius: 2 }}
        >
          New Flock
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                size="small"
                placeholder="Search flocks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="all">All Statuses</MenuItem>
                  <MenuItem value="setup">Setup</MenuItem>
                  <MenuItem value="arrival">Arrival</MenuItem>
                  <MenuItem value="growing">Growing</MenuItem>
                  <MenuItem value="production">Production</MenuItem>
                  <MenuItem value="harvesting">Harvesting</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Breed</InputLabel>
                <Select
                  value={breedFilter}
                  onChange={(e) => setBreedFilter(e.target.value)}
                  label="Breed"
                >
                  <MenuItem value="all">All Breeds</MenuItem>
                  {breeds.map((breed) => (
                    <MenuItem key={breed.id} value={breed.id.toString()}>
                      {breed.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<FilterIcon />}
                size="small"
                onClick={() => {
                  setSearchTerm('');
                  setStatusFilter('all');
                  setBreedFilter('all');
                }}
              >
                Clear
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Batch Number</TableCell>
                  <TableCell>Flock Code</TableCell>
                  <TableCell>House</TableCell>
                  <TableCell>Breed</TableCell>
                  <TableCell>Arrival Date</TableCell>
                  <TableCell>Age (Days)</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Count</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredFlocks.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                      <PoultryIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                      <Typography variant="body1" color="text.secondary">
                        No flocks found
                      </Typography>
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => navigate('/flocks/new')}
                        sx={{ mt: 2 }}
                      >
                        Create Your First Flock
                      </Button>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredFlocks.map((flock) => (
                    <TableRow key={flock.id} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {flock.batch_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {flock.flock_code}
                        </Typography>
                      </TableCell>
                      <TableCell>{flock.house_name || `House ${flock.house}`}</TableCell>
                      <TableCell>{flock.breed_name || 'N/A'}</TableCell>
                      <TableCell>
                        {flock.arrival_date
                          ? dayjs(flock.arrival_date).format('MMM DD, YYYY')
                          : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${flock.current_age_days || 0} days`}
                          size="small"
                          color="info"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={flock.status}
                          size="small"
                          color={getStatusColor(flock.status) as any}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2">
                            {flock.current_chicken_count || flock.initial_chicken_count}
                          </Typography>
                          {flock.mortality_rate !== undefined && (
                            <Chip
                              label={`${flock.mortality_rate.toFixed(1)}%`}
                              size="small"
                              color={
                                flock.mortality_rate > 5 ? 'error' : flock.mortality_rate > 3 ? 'warning' : 'success'
                              }
                              sx={{ height: 20, fontSize: '0.7rem' }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, flock)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => selectedFlock && handleViewFlock(selectedFlock)}>
          <ViewIcon sx={{ mr: 1, fontSize: 20 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={() => selectedFlock && handleEditFlock(selectedFlock)}>
          <EditIcon sx={{ mr: 1, fontSize: 20 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1, fontSize: 20 }} />
          Delete
        </MenuItem>
      </Menu>

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Flock</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete flock {selectedFlock?.batch_number}? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProfessionalFlockList;

