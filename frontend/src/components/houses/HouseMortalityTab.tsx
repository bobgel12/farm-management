import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { MortalityEntryForm, MortalityHistory, MortalityChart } from '../mortality';
import api from '../../services/api';
import { Flock } from '../../types';

interface HouseMortalityTabProps {
  houseId: number;
  house: any;
}

const HouseMortalityTab: React.FC<HouseMortalityTabProps> = ({ houseId, house }) => {
  const [showEntryForm, setShowEntryForm] = useState(false);
  const [flocks, setFlocks] = useState<Flock[]>([]);
  const [selectedFlockId, setSelectedFlockId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFlocks();
  }, [houseId]);

  const loadFlocks = async () => {
    try {
      setLoading(true);
      const response = await api.get('/flocks/', { params: { house_id: houseId } });
      const flocksData = response.data.results || response.data || [];
      setFlocks(flocksData);
      
      // Auto-select active flock (growing or production status)
      const activeFlock = flocksData.find((f: Flock) => 
        f.is_active || f.status === 'growing' || f.status === 'production'
      );
      if (activeFlock) {
        setSelectedFlockId(activeFlock.id);
      } else if (flocksData.length > 0) {
        setSelectedFlockId(flocksData[0].id);
      }
    } catch (error) {
      console.error('Failed to load flocks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordSuccess = () => {
    setShowEntryForm(false);
    setRefreshKey(prev => prev + 1);
  };

  if (!selectedFlockId && flocks.length === 0 && !loading) {
    return (
      <Alert severity="info">
        No flock is currently in this house. Add a flock to start tracking mortality.
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h6">Mortality Tracking</Typography>
          <Typography variant="body2" color="text.secondary">
            Record and monitor mortality for House {house.house_number}
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {flocks.length > 1 && (
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Select Flock</InputLabel>
              <Select
                value={selectedFlockId || ''}
                onChange={(e) => setSelectedFlockId(e.target.value as number)}
                label="Select Flock"
              >
                {flocks.map((flock) => (
                  <MenuItem key={flock.id} value={flock.id}>
                    {flock.batch_number || flock.flock_code} 
                    {flock.is_active && ' (Active)'}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          
          <Button
            variant="contained"
            color="error"
            startIcon={<AddIcon />}
            onClick={() => setShowEntryForm(true)}
            disabled={!selectedFlockId}
          >
            Record Mortality
          </Button>
        </Box>
      </Box>

      {selectedFlockId && (
        <Grid container spacing={3}>
          {/* Chart */}
          <Grid item xs={12}>
            <MortalityChart
              flockId={selectedFlockId}
              houseId={houseId}
              days={30}
              refresh={refreshKey}
            />
          </Grid>

          {/* History */}
          <Grid item xs={12}>
            <MortalityHistory
              flockId={selectedFlockId}
              houseId={houseId}
              refresh={refreshKey}
              showActions={true}
            />
          </Grid>
        </Grid>
      )}

      {/* Entry Form Dialog */}
      <Dialog
        open={showEntryForm}
        onClose={() => setShowEntryForm(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Record Mortality
          <IconButton onClick={() => setShowEntryForm(false)}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedFlockId && (
            <MortalityEntryForm
              flockId={selectedFlockId}
              houseId={houseId}
              onSuccess={handleRecordSuccess}
              onCancel={() => setShowEntryForm(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default HouseMortalityTab;

