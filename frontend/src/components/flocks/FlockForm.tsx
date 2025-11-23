import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { useFlock } from '../../contexts/FlockContext';
import { useFarm } from '../../contexts/FarmContext';
import { Flock, Breed, House } from '../../types';
import rotemApi from '../../services/rotemApi';
import dayjs from 'dayjs';

const FlockForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const { houses, farms, fetchFarms, fetchHouses, loading: farmsLoading } = useFarm();
  const {
    breeds = [],
    currentFlock,
    loading,
    error,
    fetchBreeds,
    fetchFlock,
    createFlock,
    updateFlock,
  } = useFlock();

  const [selectedFarmId, setSelectedFarmId] = useState<number | undefined>(undefined);
  const [filteredHouses, setFilteredHouses] = useState<House[]>([]);

  const [formData, setFormData] = useState<Partial<Flock>>({
    house: undefined,
    breed: undefined,
    batch_number: '',
    arrival_date: dayjs().format('YYYY-MM-DD'),
    expected_harvest_date: dayjs().add(40, 'days').format('YYYY-MM-DD'),
    initial_chicken_count: 5000,
    current_chicken_count: 5000,
    supplier: '',
    notes: '',
  });

  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loadingRotemData, setLoadingRotemData] = useState(false);
  const [rotemPrefilled, setRotemPrefilled] = useState(false);

  useEffect(() => {
    console.log('FlockForm useEffect - id:', id, 'is new:', id === 'new');
    fetchBreeds();
    // Always fetch farms for new flocks (needed for farm selection)
    // Also fetch farms if not loaded yet
    if (id === 'new' && farms.length === 0) {
      console.log('FlockForm: Fetching farms for new flock...');
      fetchFarms().catch(err => {
        console.error('FlockForm: Error fetching farms:', err);
      });
    }
  }, [fetchBreeds, id, fetchFarms, farms.length]);

  // Debug: Log farms when they change
  useEffect(() => {
    if (id === 'new') {
      console.log('Farms in FlockForm:', farms.length, farms);
      console.log('Active farms:', farms.filter(f => f.is_active));
    }
  }, [farms, id]);

  // Fetch houses when farm is selected
  useEffect(() => {
    if (selectedFarmId) {
      console.log('Fetching houses for farm:', selectedFarmId);
      fetchHouses(selectedFarmId).then(() => {
        console.log('Houses fetched:', houses.length, houses);
      });
      // Reset house selection when farm changes
      setFormData((prev) => ({ ...prev, house: undefined }));
    } else {
      setFilteredHouses([]);
      setFormData((prev) => ({ ...prev, house: undefined }));
    }
  }, [selectedFarmId, fetchHouses]);

  // Update filtered houses when houses are fetched (since we fetch by farm, all houses belong to that farm)
  useEffect(() => {
    if (selectedFarmId) {
      // Since we're fetching houses for a specific farm, all returned houses are for that farm
      // But we might still need to filter if the context keeps all houses
      // For safety, check farm_id if available, otherwise use all houses
      const housesForFarm = houses.filter((h) => {
        // If house has farm_id, filter by it, otherwise assume all houses are for selected farm
        return h.farm_id ? h.farm_id === selectedFarmId : true;
      });
      console.log('Filtered houses for farm', selectedFarmId, ':', housesForFarm.length, housesForFarm);
      // Type assertion: houses from FarmContext have house_number, but House type from types/index.ts expects different fields
      // Using double assertion through 'unknown' as TypeScript suggests
      setFilteredHouses(housesForFarm as unknown as House[]);
    } else {
      setFilteredHouses([]);
    }
  }, [selectedFarmId, houses]);

  useEffect(() => {
    if (id && id !== 'new') {
      fetchFlock(parseInt(id));
    }
  }, [id, fetchFlock]);

  useEffect(() => {
    if (currentFlock && id !== 'new') {
      // Find the house to get the farm_id
      const house = houses.find((h) => h.id === currentFlock.house);
      if (house) {
        setSelectedFarmId(house.farm_id);
      }
      setFormData({
        house: currentFlock.house,
        breed: currentFlock.breed,
        batch_number: currentFlock.batch_number,
        arrival_date: currentFlock.arrival_date,
        expected_harvest_date: currentFlock.expected_harvest_date,
        initial_chicken_count: currentFlock.initial_chicken_count,
        current_chicken_count: currentFlock.current_chicken_count || currentFlock.initial_chicken_count,
        supplier: currentFlock.supplier || '',
        notes: currentFlock.notes || '',
      });
    }
  }, [currentFlock, id, houses]);

  // Fetch and prefill data from Rotem when house is selected (only for new flocks)
  useEffect(() => {
    const prefetchRotemData = async () => {
      // Only prefill for new flocks
      if (id !== 'new' || !formData.house || loadingRotemData || rotemPrefilled) {
        return;
      }

      // Wait for farms and houses to be loaded
      if (farms.length === 0 || houses.length === 0) {
        return;
      }

      try {
        const selectedHouse = filteredHouses.find((h) => h.id === formData.house);
        if (!selectedHouse) {
          console.log('No house found with id:', formData.house);
          return;
        }

        // Find the farm for this house (should match selectedFarmId)
        const farm = farms.find((f) => f.id === (selectedFarmId || selectedHouse.farm_id));
        if (!farm) {
          console.log('No farm found for house farm_id:', selectedHouse.farm_id);
          return;
        }

        if (farm.integration_type !== 'rotem' || !farm.rotem_farm_id) {
          console.log('Farm does not have Rotem integration:', {
            integration_type: farm.integration_type,
            rotem_farm_id: farm.rotem_farm_id,
          });
          return;
        }

        console.log('Fetching Rotem data for farm:', farm.rotem_farm_id, 'house:', selectedHouse.house_number);
        setLoadingRotemData(true);
        
        // Get house number from house - it should be in the House interface
        const houseNumber = selectedHouse.house_number || 1;

        // Fetch Rotem data for this house
        const rotemData = await rotemApi.getHouseSensorData(farm.rotem_farm_id, houseNumber);

        console.log('Rotem data received:', rotemData);

        if (rotemData && rotemData.growth_day > 0) {
          // Calculate arrival date from growth_day (current date - growth_day days)
          const arrivalDate = dayjs().subtract(rotemData.growth_day, 'days').format('YYYY-MM-DD');
          
          // Calculate expected harvest date (typically 40 days after arrival, or based on breed)
          const expectedHarvestDate = dayjs(arrivalDate).add(40, 'days').format('YYYY-MM-DD');
          
          console.log('Prefilling form with Rotem data:', {
            arrivalDate,
            expectedHarvestDate,
            bird_count: rotemData.bird_count,
            growth_day: rotemData.growth_day,
          });
          
          // Prefill form with Rotem data
          setFormData((prev) => ({
            ...prev,
            arrival_date: arrivalDate,
            expected_harvest_date: expectedHarvestDate,
            initial_chicken_count: rotemData.bird_count || prev.initial_chicken_count || 0,
            current_chicken_count: rotemData.bird_count || prev.current_chicken_count || 0,
            notes: `Synced from Rotem system (Age: ${rotemData.growth_day} days)${prev.notes ? `\n${prev.notes}` : ''}`,
          }));
          
          setRotemPrefilled(true);
        } else {
          console.log('No valid Rotem data (growth_day must be > 0):', rotemData);
        }
      } catch (error) {
        console.error('Error fetching Rotem data:', error);
        // Show error in console but don't interrupt user experience
      } finally {
        setLoadingRotemData(false);
      }
    };

    prefetchRotemData();
  }, [formData.house, id, filteredHouses, farms, selectedFarmId, loadingRotemData, rotemPrefilled]);

  // Reset prefilled flag when house changes
  useEffect(() => {
    setRotemPrefilled(false);
  }, [formData.house]);

  const handleChange = (field: keyof Flock, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitting(true);

    try {
      // Validate required fields
      if (!formData.house || formData.house === 0) {
        setSubmitError('Please select a house');
        setSubmitting(false);
        return;
      }

      if (!formData.batch_number) {
        setSubmitError('Batch number is required');
        setSubmitting(false);
        return;
      }

      // Prepare data for API - convert breed to breed_id for backend
      const submitData: any = {
        ...formData,
        breed_id: formData.breed || null,
      };
      // Remove breed field as backend expects breed_id
      delete submitData.breed;

      if (id && id !== 'new' && currentFlock) {
        await updateFlock(currentFlock.id, submitData);
      } else {
        await createFlock(submitData);
      }
      navigate('/flocks');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to save flock';
      setSubmitError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && id !== 'new') {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/flocks')}
        >
          Back
        </Button>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          {id === 'new' ? 'Create New Flock' : 'Edit Flock'}
        </Typography>
      </Box>

      {(error || submitError) && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {submitError || error}
        </Alert>
      )}

      {loadingRotemData && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Loading flock information from Rotem system...
        </Alert>
      )}

      <Card>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>Farm</InputLabel>
                  <Select
                    value={selectedFarmId?.toString() || ''}
                    onChange={(e) => {
                      const farmId = e.target.value ? parseInt(e.target.value) : undefined;
                      setSelectedFarmId(farmId);
                    }}
                    label="Farm"
                    required
                  >
                    <MenuItem value="">
                      <em>Select a farm</em>
                    </MenuItem>
                    {farmsLoading ? (
                      <MenuItem disabled>Loading farms...</MenuItem>
                    ) : farms && farms.length > 0 ? (
                      farms.filter(f => f.is_active).map((farm) => (
                        <MenuItem key={farm.id} value={farm.id}>
                          {farm.name}
                        </MenuItem>
                      ))
                    ) : (
                      <MenuItem disabled>No farms available. Please create a farm first.</MenuItem>
                    )}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>House</InputLabel>
                  <Select
                    value={formData.house?.toString() || ''}
                    onChange={(e) => handleChange('house', e.target.value ? parseInt(e.target.value) : undefined)}
                    label="House"
                    disabled={!selectedFarmId || filteredHouses.length === 0}
                    required
                  >
                    {!selectedFarmId ? (
                      <MenuItem disabled>Please select a farm first</MenuItem>
                    ) : filteredHouses.length === 0 ? (
                      <MenuItem disabled>No houses available for this farm. Please create a house first.</MenuItem>
                    ) : (
                      filteredHouses.map((house) => (
                        <MenuItem key={house.id} value={house.id}>
                          {house.name || `House ${house.house_number || house.id}`}
                        </MenuItem>
                      ))
                    )}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Breed</InputLabel>
                  <Select
                    value={formData.breed?.toString() || ''}
                    onChange={(e) => handleChange('breed', e.target.value ? parseInt(e.target.value) : null)}
                    label="Breed"
                  >
                    <MenuItem value="">None</MenuItem>
                    {(breeds || []).map((breed) => (
                      <MenuItem key={breed.id} value={breed.id}>
                        {breed.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Batch Number"
                  value={formData.batch_number}
                  onChange={(e) => handleChange('batch_number', e.target.value)}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Arrival Date"
                  type="date"
                  value={formData.arrival_date}
                  onChange={(e) => handleChange('arrival_date', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Expected Harvest Date"
                  type="date"
                  value={formData.expected_harvest_date || ''}
                  onChange={(e) => handleChange('expected_harvest_date', e.target.value || null)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Supplier"
                  value={formData.supplier || ''}
                  onChange={(e) => handleChange('supplier', e.target.value)}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Initial Chicken Count"
                  type="number"
                  value={formData.initial_chicken_count || ''}
                  onChange={(e) => handleChange('initial_chicken_count', parseInt(e.target.value) || 0)}
                  inputProps={{ min: 0 }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Current Chicken Count"
                  type="number"
                  value={formData.current_chicken_count || ''}
                  onChange={(e) => handleChange('current_chicken_count', parseInt(e.target.value) || null)}
                  inputProps={{ min: 0 }}
                  helperText="Leave empty to use initial count"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Notes"
                  multiline
                  rows={4}
                  value={formData.notes || ''}
                  onChange={(e) => handleChange('notes', e.target.value)}
                  placeholder="Additional notes about this flock..."
                />
              </Grid>

              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                  <Button
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={() => navigate('/flocks')}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={submitting ? <CircularProgress size={20} /> : <SaveIcon />}
                    disabled={submitting}
                  >
                    {submitting ? 'Saving...' : 'Save'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default FlockForm;

