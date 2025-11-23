import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Button,
  CircularProgress,
  Alert,
  ToggleButton,
  ToggleButtonGroup,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Refresh,
  ArrowUpward,
  ArrowDownward,
  Star,
  StarBorder,
  Warning,
  CheckCircle,
  Error,
  ArrowBack,
  Home,
} from '@mui/icons-material';
import api from '../../services/api';
import { useFarm } from '../../contexts/FarmContext';

interface HouseComparison {
  house_id: number;
  house_number: number;
  farm_id: number;
  farm_name: string;
  current_day: number | null;
  status: string;
  is_full_house: boolean;
  last_update_time: string | null;
  average_temperature: number | null;
  static_pressure: number | null;
  inside_humidity: number | null;
  tunnel_temperature: number | null;
  outside_temperature: number | null;
  ventilation_mode: string | null;
  is_connected: boolean;
  has_alarms: boolean;
  alarm_status: string;
}

interface ComparisonResponse {
  count: number;
  houses: HouseComparison[];
}

type SortField = 'house_number' | 'current_day' | 'average_temperature' | 'static_pressure' | 'inside_humidity' | 'tunnel_temperature' | 'outside_temperature' | 'last_update_time';
type SortDirection = 'asc' | 'desc';
type ViewMode = 'house' | 'schedule';

const ComparisonDashboard: React.FC = () => {
  const { farmId } = useParams<{ farmId?: string }>();
  const navigate = useNavigate();
  const { farms } = useFarm();
  const [houses, setHouses] = useState<HouseComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('house_number');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [viewMode, setViewMode] = useState<ViewMode>('house');
  const [farmFilter, setFarmFilter] = useState<number | 'all'>(farmId ? parseInt(farmId) : 'all');
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState<ReturnType<typeof setTimeout> | null>(null);

  // Get current farm info
  const currentFarm = farmId ? farms.find(f => f.id === parseInt(farmId)) : null;

  // Load comparison data
  const loadComparisonData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {};
      if (farmFilter !== 'all') {
        params.farm_id = farmFilter;
      }
      if (favoritesOnly && favorites.size > 0) {
        params.house_ids = Array.from(favorites);
      }

      const response = await api.get<ComparisonResponse>('/houses/comparison/', { params });
      let data = response.data.houses;

      // Apply favorites filter if enabled
      if (favoritesOnly) {
        data = data.filter(house => favorites.has(house.house_id));
      }

      // Sort data
      data.sort((a, b) => {
        let aVal: any = a[sortField];
        let bVal: any = b[sortField];

        // Handle null values
        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;

        // Handle string comparison for last_update_time
        if (sortField === 'last_update_time') {
          aVal = new Date(aVal).getTime();
          bVal = new Date(bVal).getTime();
        }

        if (sortDirection === 'asc') {
          return aVal > bVal ? 1 : -1;
        } else {
          return aVal < bVal ? 1 : -1;
        }
      });

      setHouses(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load comparison data');
      console.error('Error loading comparison data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load favorites from localStorage
  useEffect(() => {
    const savedFavorites = localStorage.getItem('houseComparisonFavorites');
    if (savedFavorites) {
      try {
        setFavorites(new Set(JSON.parse(savedFavorites)));
      } catch (e) {
        console.error('Error loading favorites:', e);
      }
    }
  }, []);

  // Save favorites to localStorage
  useEffect(() => {
    if (favorites.size > 0) {
      localStorage.setItem('houseComparisonFavorites', JSON.stringify(Array.from(favorites)));
    }
  }, [favorites]);

  // Update farmFilter when farmId changes
  useEffect(() => {
    if (farmId) {
      setFarmFilter(parseInt(farmId));
    }
  }, [farmId]);

  // Initial load
  useEffect(() => {
    loadComparisonData();
  }, [farmFilter, favoritesOnly]);

  // Auto-refresh setup
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadComparisonData();
      }, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);
      return () => {
        if (interval) clearInterval(interval);
      };
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }
  }, [autoRefresh]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
    loadComparisonData();
  };

  const toggleFavorite = (houseId: number) => {
    const newFavorites = new Set(favorites);
    if (newFavorites.has(houseId)) {
      newFavorites.delete(houseId);
    } else {
      newFavorites.add(houseId);
    }
    setFavorites(newFavorites);
  };

  const formatTemperature = (temp: number | null): string => {
    if (temp === null || temp === undefined) return '---';
    return `${temp.toFixed(1)} F°`;
  };

  const formatHumidity = (humidity: number | null): string => {
    if (humidity === null || humidity === undefined) return '---';
    return `${Math.round(humidity)} %`;
  };

  const formatPressure = (pressure: number | null): string => {
    if (pressure === null || pressure === undefined) return '0.000';
    return pressure.toFixed(3);
  };

  const formatTime = (time: string | null): string => {
    if (!time) return '---';
    try {
      const date = new Date(time);
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '---';
    }
  };

  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'normal':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getIconColor = (status: string): 'error' | 'primary' | 'secondary' | 'info' | 'success' | 'warning' | 'inherit' | 'disabled' | 'action' | undefined => {
    switch (status) {
      case 'normal':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'warning'; // Default to warning for unknown statuses
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />;
  };

  if (loading && houses.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const handleHouseClick = (house: HouseComparison) => {
    if (farmId) {
      navigate(`/farms/${farmId}/houses/${house.house_id}`);
    } else {
      navigate(`/farms/${house.farm_id}/houses/${house.house_id}`);
    }
  };

  return (
    <Box sx={{ width: '100%', maxWidth: '100%', overflow: 'hidden' }}>
      {/* Breadcrumbs */}
      {farmId && currentFarm && (
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/farms')}
            sx={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}
          >
            <Home sx={{ mr: 0.5, fontSize: 20 }} />
            Farms
          </Link>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate(`/farms/${farmId}`)}
            sx={{ textDecoration: 'none' }}
          >
            {currentFarm.name}
          </Link>
          <Typography color="text.primary">House Comparison</Typography>
        </Breadcrumbs>
      )}

      <Box 
        display="flex" 
        justifyContent="space-between" 
        alignItems="flex-start" 
        mb={3}
        sx={{ 
          flexDirection: { xs: 'column', md: 'row' },
          gap: { xs: 2, md: 0 }
        }}
      >
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {farmId && currentFarm && (
            <Button
              startIcon={<ArrowBack />}
              onClick={() => navigate(`/farms/${farmId}`)}
              sx={{ mb: 1 }}
            >
              Back to {currentFarm.name}
            </Button>
          )}
          <Typography variant="h4" component="h1" sx={{ wordBreak: 'break-word' }}>
            {farmId && currentFarm ? `${currentFarm.name} - House Comparison` : 'House Comparison'}
          </Typography>
          {farmId && currentFarm && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Comparing houses for {currentFarm.name}
            </Typography>
          )}
        </Box>
        <Box 
          display="flex" 
          gap={2} 
          alignItems="center"
          sx={{ 
            flexWrap: { xs: 'wrap', sm: 'nowrap' },
            mt: { xs: 2, md: 0 }
          }}
        >
          {!farmId && farms.length > 0 && (
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Farm</InputLabel>
              <Select
                value={farmFilter === 'all' ? 'all' : farmFilter}
                label="Farm"
                onChange={(e) => {
                  const value = e.target.value;
                  setFarmFilter(value === 'all' ? 'all' : parseInt(value as string));
                }}
              >
                <MenuItem value="all">All Farms</MenuItem>
                {farms.map((farm) => (
                  <MenuItem key={farm.id} value={farm.id}>
                    {farm.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            size="small"
          >
            <ToggleButton value="house">By House</ToggleButton>
            <ToggleButton value="schedule">By Sched.</ToggleButton>
          </ToggleButtonGroup>
          <Button
            variant="outlined"
            startIcon={favoritesOnly ? <Star /> : <StarBorder />}
            onClick={() => setFavoritesOnly(!favoritesOnly)}
            disabled={favorites.size === 0}
          >
            {favoritesOnly ? 'Favorites' : 'All'}
          </Button>
          <IconButton onClick={loadComparisonData} disabled={loading}>
            <Refresh />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Box sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer 
          component={Paper}
          sx={{ 
            width: '100%',
            overflowX: 'auto',
            overflowY: 'visible',
            '&::-webkit-scrollbar': {
              height: '8px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: 'rgba(0,0,0,0.1)',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: 'rgba(0,0,0,0.3)',
              borderRadius: '4px',
              '&:hover': {
                backgroundColor: 'rgba(0,0,0,0.5)',
              },
            },
          }}
        >
          <Table sx={{ minWidth: 1200, tableLayout: 'fixed', width: '100%' }}>
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: '15%', whiteSpace: 'nowrap' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton size="small" onClick={() => handleSort('house_number')}>
                    <SortIcon field="house_number" />
                  </IconButton>
                  House
                </Box>
              </TableCell>
              <TableCell sx={{ width: '12%', whiteSpace: 'nowrap' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton size="small" onClick={() => handleSort('current_day')}>
                    <SortIcon field="current_day" />
                  </IconButton>
                  Status
                </Box>
              </TableCell>
              <TableCell sx={{ width: '8%', whiteSpace: 'nowrap' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton size="small" onClick={() => handleSort('last_update_time')}>
                    <SortIcon field="last_update_time" />
                  </IconButton>
                  Time
                </Box>
              </TableCell>
              <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton size="small" onClick={() => handleSort('average_temperature')}>
                    <SortIcon field="average_temperature" />
                  </IconButton>
                  Avg. Temperature
                </Box>
              </TableCell>
              <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton size="small" onClick={() => handleSort('static_pressure')}>
                    <SortIcon field="static_pressure" />
                  </IconButton>
                  Static Pressure
                </Box>
              </TableCell>
              <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton size="small" onClick={() => handleSort('inside_humidity')}>
                    <SortIcon field="inside_humidity" />
                  </IconButton>
                  Inside Humidity
                </Box>
              </TableCell>
              <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton size="small" onClick={() => handleSort('tunnel_temperature')}>
                    <SortIcon field="tunnel_temperature" />
                  </IconButton>
                  Tunnel Temperature
                </Box>
              </TableCell>
              <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>
                <Box display="flex" alignItems="center" gap={1}>
                  <IconButton size="small" onClick={() => handleSort('outside_temperature')}>
                    <SortIcon field="outside_temperature" />
                  </IconButton>
                  Outside Temperature
                </Box>
              </TableCell>
              <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>Vent. Mode</TableCell>
              <TableCell sx={{ width: '5%', whiteSpace: 'nowrap' }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {houses.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No houses found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              houses.map((house) => (
                <TableRow 
                  key={house.house_id} 
                  hover 
                  sx={{ cursor: 'pointer' }}
                  onClick={() => handleHouseClick(house)}
                >
                  <TableCell sx={{ width: '15%', whiteSpace: 'nowrap' }}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleFavorite(house.house_id);
                        }}
                        color={favorites.has(house.house_id) ? 'primary' : 'default'}
                      >
                        {favorites.has(house.house_id) ? <Star /> : <StarBorder />}
                      </IconButton>
                      <Typography variant="body2" fontWeight="medium" noWrap>
                        House {house.house_number}
                      </Typography>
                      {!farmId && (
                        <Chip 
                          label={house.farm_name} 
                          size="small" 
                          variant="outlined"
                          sx={{ ml: 1 }}
                        />
                      )}
                      {!house.is_connected && (
                        <Tooltip title="Disconnected">
                          <Error color="error" fontSize="small" />
                        </Tooltip>
                      )}
                      {house.has_alarms && (
                        <Tooltip title={`Alarm: ${house.alarm_status}`}>
                          <Warning color={getIconColor(house.alarm_status)} fontSize="small" />
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell sx={{ width: '12%', whiteSpace: 'nowrap' }}>
                    <Box>
                      <Typography variant="body2" noWrap>
                        {house.current_day !== null ? `Day ${house.current_day}` : '---'}
                      </Typography>
                      <Chip
                        label={house.is_full_house ? 'Full House' : 'Empty'}
                        size="small"
                        color={house.is_full_house ? 'primary' : 'default'}
                      />
                    </Box>
                  </TableCell>
                  <TableCell sx={{ width: '8%', whiteSpace: 'nowrap' }}>{formatTime(house.last_update_time)}</TableCell>
                  <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>{formatTemperature(house.average_temperature)}</TableCell>
                  <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>{formatPressure(house.static_pressure)}</TableCell>
                  <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>{formatHumidity(house.inside_humidity)}</TableCell>
                  <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>{formatTemperature(house.tunnel_temperature)}</TableCell>
                  <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>{formatTemperature(house.outside_temperature)}</TableCell>
                  <TableCell sx={{ width: '10%', whiteSpace: 'nowrap' }}>
                    <Typography variant="body2" noWrap>
                      {house.ventilation_mode || '---'}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ width: '5%', whiteSpace: 'nowrap' }}>
                    <Chip
                      label={house.alarm_status}
                      size="small"
                      color={getStatusColor(house.alarm_status)}
                    />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        </TableContainer>
      </Box>
    </Box>
  );
};

export default ComparisonDashboard;

