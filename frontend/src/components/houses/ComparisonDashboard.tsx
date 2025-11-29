import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
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
  Tabs,
  Tab,
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
  Thermostat,
  Water,
  Air,
  Restaurant,
} from '@mui/icons-material';
import api from '../../services/api';
import { useFarm } from '../../contexts/FarmContext';

interface HouseComparison {
  house_id: number;
  house_number: number;
  farm_id: number;
  farm_name: string;
  current_day: number | null;
  age_days?: number | null;
  current_age_days?: number;
  is_integrated?: boolean;
  status: string;
  is_full_house: boolean;
  last_update_time: string | null;
  // Temperature
  average_temperature: number | null;
  outside_temperature: number | null;
  tunnel_temperature: number | null;
  target_temperature: number | null;
  // Environment
  static_pressure: number | null;
  inside_humidity: number | null;
  ventilation_mode: string | null;
  ventilation_level: number | null;
  airflow_cfm: number | null;
  // Consumption
  water_consumption: number | null;
  feed_consumption: number | null;
  // Bird Status
  bird_count: number | null;
  livability: number | null;
  growth_day: number | null;
  // Status
  is_connected: boolean;
  has_alarms: boolean;
  alarm_status: string;
}

interface ComparisonResponse {
  count: number;
  houses: HouseComparison[];
}

type SortField = 'house_number' | 'current_day' | 'average_temperature' | 'static_pressure' | 'inside_humidity' | 'water_consumption' | 'feed_consumption' | 'bird_count' | 'livability';
type SortDirection = 'asc' | 'desc';

const ComparisonDashboard: React.FC = () => {
  const { farmId } = useParams<{ farmId?: string }>();
  const navigate = useNavigate();
  const { farms } = useFarm();
  const [houses, setHouses] = useState<HouseComparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('house_number');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [farmFilter, setFarmFilter] = useState<number | 'all'>(farmId ? parseInt(farmId) : 'all');
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState(0);

  const currentFarm = farmId ? farms.find(f => f.id === parseInt(farmId)) : null;

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

      if (favoritesOnly) {
        data = data.filter(house => favorites.has(house.house_id));
      }

      data.sort((a, b) => {
        const aVal: any = a[sortField];
        const bVal: any = b[sortField];

        if (aVal === null || aVal === undefined) return 1;
        if (bVal === null || bVal === undefined) return -1;

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

  useEffect(() => {
    if (favorites.size > 0) {
      localStorage.setItem('houseComparisonFavorites', JSON.stringify(Array.from(favorites)));
    }
  }, [favorites]);

  useEffect(() => {
    if (farmId) {
      setFarmFilter(parseInt(farmId));
    }
  }, [farmId]);

  useEffect(() => {
    loadComparisonData();
  }, [farmFilter, favoritesOnly, sortField, sortDirection]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(loadComparisonData, 30000);
    return () => clearInterval(interval);
  }, [farmFilter, favoritesOnly]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
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

  const formatTemp = (temp: number | null): string => {
    if (temp === null || temp === undefined) return '---';
    return `${temp.toFixed(1)}°F`;
  };

  const formatHumidity = (humidity: number | null): string => {
    if (humidity === null || humidity === undefined) return '---';
    return `${Math.round(humidity)}%`;
  };

  const formatPressure = (pressure: number | null): string => {
    if (pressure === null || pressure === undefined) return '---';
    return pressure.toFixed(3);
  };

  const formatConsumption = (value: number | null, unit: string): string => {
    if (value === null || value === undefined) return '---';
    return `${value.toLocaleString()} ${unit}`;
  };

  const formatNumber = (value: number | null): string => {
    if (value === null || value === undefined) return '---';
    return value.toLocaleString();
  };

  const formatPercent = (value: number | null): string => {
    if (value === null || value === undefined) return '---';
    return `${value.toFixed(1)}%`;
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
      case 'normal': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ArrowUpward fontSize="small" /> : <ArrowDownward fontSize="small" />;
  };

  const handleHouseClick = (house: HouseComparison) => {
    if (farmId) {
      navigate(`/farms/${farmId}/houses/${house.house_id}`);
    } else {
      navigate(`/farms/${house.farm_id}/houses/${house.house_id}`);
    }
  };

  if (loading && houses.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  // Column header cell style
  const headerCellStyle = { 
    fontWeight: 'bold', 
    whiteSpace: 'nowrap' as const,
    backgroundColor: '#f5f5f5',
    position: 'sticky' as const,
    top: 0,
    zIndex: 1,
  };

  const cellStyle = { 
    whiteSpace: 'nowrap' as const,
    py: 1.5,
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Breadcrumbs */}
      {farmId && currentFarm && (
        <Breadcrumbs sx={{ mb: 2 }}>
          <Link component="button" variant="body1" onClick={() => navigate('/farms')} sx={{ display: 'flex', alignItems: 'center' }}>
            <Home sx={{ mr: 0.5, fontSize: 20 }} />
            Farms
          </Link>
          <Link component="button" variant="body1" onClick={() => navigate(`/farms/${farmId}`)}>
            {currentFarm.name}
          </Link>
          <Typography color="text.primary">House Comparison</Typography>
        </Breadcrumbs>
      )}

      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={2}>
        <Box>
          {farmId && currentFarm && (
            <Button startIcon={<ArrowBack />} onClick={() => navigate(`/farms/${farmId}`)} sx={{ mb: 1 }}>
              Back to {currentFarm.name}
            </Button>
          )}
          <Typography variant="h5" fontWeight="bold">
            House Comparison Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {houses.length} houses • Last updated: {new Date().toLocaleTimeString()}
          </Typography>
        </Box>
        <Box display="flex" gap={1} alignItems="center" flexWrap="wrap">
          {!farmId && farms.length > 0 && (
            <FormControl size="small" sx={{ minWidth: 150 }}>
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
                  <MenuItem key={farm.id} value={farm.id}>{farm.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <Button
            variant={favoritesOnly ? 'contained' : 'outlined'}
            startIcon={favoritesOnly ? <Star /> : <StarBorder />}
            onClick={() => setFavoritesOnly(!favoritesOnly)}
            size="small"
          >
            Favorites
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

      {/* View Tabs */}
      <Tabs value={activeTab} onChange={(_, val) => setActiveTab(val)} sx={{ mb: 2 }}>
        <Tab icon={<Thermostat />} label="Climate" iconPosition="start" />
        <Tab icon={<Water />} label="Consumption" iconPosition="start" />
        <Tab icon={<Air />} label="Environment" iconPosition="start" />
      </Tabs>

      {/* Table */}
      <Card>
        <TableContainer sx={{ maxHeight: 'calc(100vh - 350px)', overflow: 'auto' }}>
          <Table stickyHeader size="small">
            <TableHead>
              <TableRow>
                {/* Fixed columns */}
                <TableCell sx={{ ...headerCellStyle, minWidth: 60, position: 'sticky', left: 0, zIndex: 3, backgroundColor: '#f5f5f5' }}>
                  <IconButton size="small" onClick={() => handleSort('house_number')}>
                    <SortIcon field="house_number" />
                  </IconButton>
                  House
                </TableCell>
                <TableCell sx={{ ...headerCellStyle, minWidth: 80 }}>
                  <Box display="flex" alignItems="center" gap={0.5}>
                    <IconButton size="small" onClick={() => handleSort('current_day')}>
                      <SortIcon field="current_day" />
                    </IconButton>
                    Day
                  </Box>
                </TableCell>
                <TableCell sx={{ ...headerCellStyle, minWidth: 70 }}>Status</TableCell>
                <TableCell sx={{ ...headerCellStyle, minWidth: 60 }}>Time</TableCell>

                {/* Climate Tab */}
                {activeTab === 0 && (
                  <>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 90 }}>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <IconButton size="small" onClick={() => handleSort('average_temperature')}>
                          <SortIcon field="average_temperature" />
                        </IconButton>
                        Avg Temp
                      </Box>
                    </TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 80 }}>Target</TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 80 }}>Outside</TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 80 }}>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <IconButton size="small" onClick={() => handleSort('inside_humidity')}>
                          <SortIcon field="inside_humidity" />
                        </IconButton>
                        Humidity
                      </Box>
                    </TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 90 }}>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <IconButton size="small" onClick={() => handleSort('static_pressure')}>
                          <SortIcon field="static_pressure" />
                        </IconButton>
                        Pressure
                      </Box>
                    </TableCell>
                  </>
                )}

                {/* Consumption Tab */}
                {activeTab === 1 && (
                  <>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 100 }}>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <IconButton size="small" onClick={() => handleSort('water_consumption')}>
                          <SortIcon field="water_consumption" />
                        </IconButton>
                        💧 Water
                      </Box>
                    </TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 100 }}>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <IconButton size="small" onClick={() => handleSort('feed_consumption')}>
                          <SortIcon field="feed_consumption" />
                        </IconButton>
                        🌾 Feed
                      </Box>
                    </TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 100 }}>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <IconButton size="small" onClick={() => handleSort('bird_count')}>
                          <SortIcon field="bird_count" />
                        </IconButton>
                        🐔 Birds
                      </Box>
                    </TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 90 }}>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <IconButton size="small" onClick={() => handleSort('livability')}>
                          <SortIcon field="livability" />
                        </IconButton>
                        Livability
                      </Box>
                    </TableCell>
                  </>
                )}

                {/* Environment Tab */}
                {activeTab === 2 && (
                  <>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 100 }}>Vent Mode</TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 90 }}>Vent Level</TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 100 }}>Airflow (CFM)</TableCell>
                    <TableCell sx={{ ...headerCellStyle, minWidth: 90 }}>Tunnel Temp</TableCell>
                  </>
                )}

                <TableCell sx={{ ...headerCellStyle, minWidth: 60 }}>Alarm</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {houses.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={15} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No houses found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                houses.map((house) => (
                  <TableRow 
                    key={house.house_id} 
                    hover 
                    sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                    onClick={() => handleHouseClick(house)}
                  >
                    {/* Fixed columns */}
                    <TableCell sx={{ ...cellStyle, position: 'sticky', left: 0, backgroundColor: 'background.paper', zIndex: 1 }}>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <IconButton
                          size="small"
                          onClick={(e) => { e.stopPropagation(); toggleFavorite(house.house_id); }}
                          color={favorites.has(house.house_id) ? 'warning' : 'default'}
                        >
                          {favorites.has(house.house_id) ? <Star fontSize="small" /> : <StarBorder fontSize="small" />}
                        </IconButton>
                        <Typography variant="body2" fontWeight="medium">
                          {house.house_number}
                        </Typography>
                        {!house.is_connected && (
                          <Tooltip title="Disconnected">
                            <Error color="error" fontSize="small" />
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell sx={cellStyle}>
                      <Chip 
                        label={`Day ${house.age_days ?? house.current_day ?? '---'}`}
                        size="small"
                        color={house.is_full_house ? 'primary' : 'default'}
                        variant={house.is_full_house ? 'filled' : 'outlined'}
                      />
                    </TableCell>
                    <TableCell sx={cellStyle}>
                      <Chip 
                        label={house.status}
                        size="small"
                        color={house.is_full_house ? 'success' : 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell sx={cellStyle}>
                      <Typography variant="body2" color="text.secondary">
                        {formatTime(house.last_update_time)}
                      </Typography>
                    </TableCell>

                    {/* Climate Tab */}
                    {activeTab === 0 && (
                      <>
                        <TableCell sx={cellStyle}>
                          <Typography variant="body2" fontWeight="medium" color={
                            house.average_temperature && house.target_temperature
                              ? Math.abs(house.average_temperature - house.target_temperature) > 3 
                                ? 'error.main' 
                                : 'success.main'
                              : 'text.primary'
                          }>
                            {formatTemp(house.average_temperature)}
                          </Typography>
                        </TableCell>
                        <TableCell sx={cellStyle}>{formatTemp(house.target_temperature)}</TableCell>
                        <TableCell sx={cellStyle}>{formatTemp(house.outside_temperature)}</TableCell>
                        <TableCell sx={cellStyle}>{formatHumidity(house.inside_humidity)}</TableCell>
                        <TableCell sx={cellStyle}>{formatPressure(house.static_pressure)}</TableCell>
                      </>
                    )}

                    {/* Consumption Tab */}
                    {activeTab === 1 && (
                      <>
                        <TableCell sx={cellStyle}>
                          <Typography variant="body2" fontWeight="medium" color="info.main">
                            {formatConsumption(house.water_consumption, 'L')}
                          </Typography>
                        </TableCell>
                        <TableCell sx={cellStyle}>
                          <Typography variant="body2" fontWeight="medium" color="warning.main">
                            {formatConsumption(house.feed_consumption, 'lb')}
                          </Typography>
                        </TableCell>
                        <TableCell sx={cellStyle}>
                          <Typography variant="body2">
                            {formatNumber(house.bird_count)}
                          </Typography>
                        </TableCell>
                        <TableCell sx={cellStyle}>
                          <Typography variant="body2" color={
                            house.livability && house.livability < 95 ? 'error.main' : 'success.main'
                          }>
                            {formatPercent(house.livability)}
                          </Typography>
                        </TableCell>
                      </>
                    )}

                    {/* Environment Tab */}
                    {activeTab === 2 && (
                      <>
                        <TableCell sx={cellStyle}>
                          <Typography variant="body2" noWrap>
                            {house.ventilation_mode || '---'}
                          </Typography>
                        </TableCell>
                        <TableCell sx={cellStyle}>
                          {house.ventilation_level != null ? `${house.ventilation_level.toFixed(0)}%` : '---'}
                        </TableCell>
                        <TableCell sx={cellStyle}>
                          {house.airflow_cfm != null ? house.airflow_cfm.toLocaleString() : '---'}
                        </TableCell>
                        <TableCell sx={cellStyle}>{formatTemp(house.tunnel_temperature)}</TableCell>
                      </>
                    )}

                    <TableCell sx={cellStyle}>
                      {house.has_alarms ? (
                        <Chip
                          icon={<Warning />}
                          label={house.alarm_status}
                          size="small"
                          color={getStatusColor(house.alarm_status)}
                        />
                      ) : (
                        <Chip
                          icon={<CheckCircle />}
                          label="OK"
                          size="small"
                          color="success"
                          variant="outlined"
                        />
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Summary Cards */}
      <Box display="flex" gap={2} mt={2} flexWrap="wrap">
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">Avg Temperature</Typography>
            <Typography variant="h5">
              {houses.length > 0 
                ? `${(houses.reduce((sum, h) => sum + (h.average_temperature || 0), 0) / houses.filter(h => h.average_temperature).length).toFixed(1)}°F`
                : '---'}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">Total Water</Typography>
            <Typography variant="h5" color="info.main">
              {houses.reduce((sum, h) => sum + (h.water_consumption || 0), 0).toLocaleString()} L
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">Total Feed</Typography>
            <Typography variant="h5" color="warning.main">
              {houses.reduce((sum, h) => sum + (h.feed_consumption || 0), 0).toLocaleString()} lb
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">Total Birds</Typography>
            <Typography variant="h5">
              {houses.reduce((sum, h) => sum + (h.bird_count || 0), 0).toLocaleString()}
            </Typography>
          </CardContent>
        </Card>
        <Card sx={{ flex: 1, minWidth: 200 }}>
          <CardContent>
            <Typography variant="body2" color="text.secondary">Avg Livability</Typography>
            <Typography variant="h5" color="success.main">
              {houses.length > 0 && houses.some(h => h.livability)
                ? `${(houses.reduce((sum, h) => sum + (h.livability || 0), 0) / houses.filter(h => h.livability).length).toFixed(1)}%`
                : '---'}
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default ComparisonDashboard;
