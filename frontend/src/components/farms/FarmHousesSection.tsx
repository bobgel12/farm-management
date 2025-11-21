import React, { memo } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
} from '@mui/material';
import { Home } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { House } from '../../types';

interface HouseSensorData {
  status: string;
  sensors: {
    temperature?: {
      current: number;
      unit: string;
    };
    humidity?: {
      current: number;
      unit: string;
    };
    water?: {
      current: number;
      unit: string;
    };
    feed_consumption?: {
      current: number;
      unit: string;
    };
    growth_day?: {
      current: number;
      unit: string;
    };
  };
  last_updated: string;
}

// Extended House type with additional fields from API
interface ExtendedHouse extends House {
  house_number?: number;
  current_age_days?: number;
  is_integrated?: boolean;
  last_system_sync?: string;
}

interface FarmHousesSectionProps {
  farmId: number;
  houses: ExtendedHouse[];
  houseSensorData: { [key: string]: HouseSensorData };
  getHouseStatusColor: (house: ExtendedHouse) => 'success' | 'error' | 'warning' | 'default';
  formatLastSync: (lastSync?: string) => string;
}

const FarmHousesSection: React.FC<FarmHousesSectionProps> = ({
  farmId,
  houses,
  houseSensorData,
  getHouseStatusColor,
  formatLastSync,
}) => {
  const navigate = useNavigate();

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Houses ({houses?.length || 0})
          </Typography>
          <Button
            variant="outlined"
            startIcon={<Home />}
            onClick={() => {
              if (houses && houses.length > 0) {
                navigate(`/farms/${farmId}/houses/${houses[0].id}`);
              }
            }}
            size="small"
            disabled={!houses || houses.length === 0}
          >
            View Houses
          </Button>
        </Box>
        
        <Grid container spacing={2}>
          {(houses || []).map((house) => (
            <Grid item xs={12} sm={6} md={4} key={house.id}>
              <Card 
                variant="outlined" 
                sx={{ 
                  height: '100%',
                  cursor: 'pointer',
                  '&:hover': { boxShadow: 2 }
                }}
                onClick={() => navigate(`/farms/${farmId}/houses/${house.id}`)}
              >
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="h6">
                      House {house.house_number || house.name}
                    </Typography>
                    <Chip
                      label={house.is_integrated ? 'Integrated' : 'Manual'}
                      color={getHouseStatusColor(house)}
                      size="small"
                    />
                  </Box>
                  
                  <Typography color="textSecondary" variant="body2" gutterBottom>
                    Capacity: {house.capacity.toLocaleString()}
                  </Typography>
                  
                  {/* Show real-time sensor data if available */}
                  {house.house_number && houseSensorData[house.house_number.toString()]?.sensors ? (
                    <>
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Age: {houseSensorData[house.house_number.toString()].sensors.growth_day?.current || house.current_age_days || 'N/A'} days
                      </Typography>
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Temperature: {houseSensorData[house.house_number.toString()].sensors.temperature?.current || 'N/A'}°C
                      </Typography>
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Water: {houseSensorData[house.house_number.toString()].sensors.water?.current || 'N/A'}L
                      </Typography>
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Feed: {houseSensorData[house.house_number.toString()].sensors.feed_consumption?.current || 'N/A'}LB
                      </Typography>
                    </>
                  ) : (
                    <>
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Age: {house.current_age_days || 'N/A'} days
                      </Typography>
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Temperature: Loading...
                      </Typography>
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Water: Loading...
                      </Typography>
                      <Typography color="textSecondary" variant="body2" gutterBottom>
                        Feed: Loading...
                      </Typography>
                    </>
                  )}
                  
                  {house.is_integrated && house.last_system_sync && (
                    <Typography color="textSecondary" variant="body2">
                      Last Sync: {formatLastSync(house.last_system_sync)}
                    </Typography>
                  )}
                  
                  {!house.is_active && (
                    <Chip
                      label="Inactive"
                      color="default"
                      size="small"
                      sx={{ mt: 1 }}
                    />
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default memo(FarmHousesSection);

