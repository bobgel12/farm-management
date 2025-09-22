import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
} from '@mui/material';
import {
  Warning as WarningIcon,
  Info as InfoIcon,
  Agriculture as FarmIcon,
  Task as TaskIcon,
} from '@mui/icons-material';

interface ProgramChangeDialogProps {
  open: boolean;
  onClose: () => void;
  changeData: {
    change_detected: boolean;
    change_log_id?: number;
    impact_analysis?: {
      affected_farms_count: number;
      active_houses_count: number;
      changes_count: number;
      critical_changes: number;
      moderate_changes: number;
      minor_changes: number;
      affected_farms: Array<{
        id: number;
        name: string;
        active_houses: number;
      }>;
    };
  };
  onHandleChange: (choice: 'retroactive' | 'next_flock') => Promise<void>;
  loading?: boolean;
}

const ProgramChangeDialog: React.FC<ProgramChangeDialogProps> = ({
  open,
  onClose,
  changeData,
  onHandleChange,
  loading = false,
}) => {
  const [selectedChoice, setSelectedChoice] = useState<'retroactive' | 'next_flock'>('retroactive');

  if (!changeData.change_detected || !changeData.impact_analysis) {
    return null;
  }

  const { impact_analysis } = changeData;

  const handleSubmit = async () => {
    await onHandleChange(selectedChoice);
  };

  const getSeverityColor = (count: number) => {
    if (count > 0) return 'error';
    return 'default';
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <WarningIcon color="warning" />
          <Typography variant="h6">
            Program Changes Detected
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            This program is currently being used by {impact_analysis.affected_farms_count} farm(s) with active houses. 
            You need to decide how to handle the existing farm tasks.
          </Typography>
        </Alert>

        {/* Impact Summary */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Impact Summary
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {impact_analysis.affected_farms_count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Affected Farms
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center">
                  <Typography variant="h4" color="secondary">
                    {impact_analysis.active_houses_count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Houses
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Box textAlign="center">
                  <Typography variant="h4" color="info.main">
                    {impact_analysis.changes_count}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Changes
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            <Box display="flex" gap={1} flexWrap="wrap">
              <Chip
                icon={<WarningIcon />}
                label={`${impact_analysis.critical_changes} Critical`}
                color={getSeverityColor(impact_analysis.critical_changes)}
                size="small"
              />
              <Chip
                icon={<InfoIcon />}
                label={`${impact_analysis.moderate_changes} Moderate`}
                color={impact_analysis.moderate_changes > 0 ? 'warning' : 'default'}
                size="small"
              />
              <Chip
                icon={<TaskIcon />}
                label={`${impact_analysis.minor_changes} Minor`}
                color="info"
                size="small"
              />
            </Box>
          </CardContent>
        </Card>

        {/* Affected Farms */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Affected Farms
            </Typography>
            <List dense>
              {impact_analysis.affected_farms.map((farm) => (
                <ListItem key={farm.id}>
                  <ListItemIcon>
                    <FarmIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={farm.name}
                    secondary={`${farm.active_houses} active house${farm.active_houses !== 1 ? 's' : ''}`}
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>

        {/* User Choice */}
        <Card>
          <CardContent>
            <FormControl component="fieldset">
              <FormLabel component="legend">
                <Typography variant="h6" gutterBottom>
                  How would you like to handle existing farm tasks?
                </Typography>
              </FormLabel>
              <RadioGroup
                value={selectedChoice}
                onChange={(e) => setSelectedChoice(e.target.value as 'retroactive' | 'next_flock')}
              >
                <FormControlLabel
                  value="retroactive"
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        Apply to Current Flock
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Update existing tasks for all active houses immediately. 
                        This will modify current farm operations.
                      </Typography>
                    </Box>
                  }
                />
                <FormControlLabel
                  value="next_flock"
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        Apply to Next Flock
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Keep current tasks unchanged. Changes will only apply to new flocks 
                        that start after this modification.
                      </Typography>
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>
          </CardContent>
        </Card>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Processing...' : 'Apply Changes'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProgramChangeDialog;
