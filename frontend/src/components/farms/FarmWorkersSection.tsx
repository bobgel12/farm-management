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
import { useNavigate } from 'react-router-dom';
import { Worker } from '../../types';

interface FarmWorkersSectionProps {
  farmId: number;
  workers: Worker[];
}

const FarmWorkersSection: React.FC<FarmWorkersSectionProps> = ({
  farmId,
  workers,
}) => {
  const navigate = useNavigate();

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Workers ({workers?.length || 0})
          </Typography>
          <Button
            variant="outlined"
            onClick={() => navigate(`/farms/${farmId}/workers`)}
            size="small"
          >
            Manage Workers
          </Button>
        </Box>
        
        <Grid container spacing={2}>
          {(workers || []).map((worker) => (
            <Grid item xs={12} sm={6} md={4} key={worker.id}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {worker.name}
                  </Typography>
                  <Typography color="textSecondary" variant="body2" gutterBottom>
                    {worker.role}
                  </Typography>
                  <Typography color="textSecondary" variant="body2" gutterBottom>
                    {worker.email}
                  </Typography>
                  {worker.phone && (
                    <Typography color="textSecondary" variant="body2" gutterBottom>
                      {worker.phone}
                    </Typography>
                  )}
                  <Chip
                    label={worker.is_active ? 'Active' : 'Inactive'}
                    color={worker.is_active ? 'success' : 'default'}
                    size="small"
                  />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default memo(FarmWorkersSection);

