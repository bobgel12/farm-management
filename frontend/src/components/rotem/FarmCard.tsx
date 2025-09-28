import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  IconButton,
  Menu,
  MenuItem,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  MoreVert,
  TrendingUp,
  Delete,
  Edit,
  Visibility,
} from '@mui/icons-material';
import { RotemFarm, FarmDataSummary } from '../../types/rotem';
import { useRotem } from '../../contexts/RotemContext';
import { useNavigate } from 'react-router-dom';

interface FarmCardProps {
  farm: RotemFarm;
  summary?: FarmDataSummary;
}

const FarmCard: React.FC<FarmCardProps> = ({ farm, summary }) => {
  const { scrapeFarm, deleteFarm } = useRotem();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [isScraping, setIsScraping] = useState(false);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleScrape = async () => {
    setIsScraping(true);
    try {
      await scrapeFarm(farm.farm_id);
    } finally {
      setIsScraping(false);
    }
    handleMenuClose();
  };

  const handleViewDetails = () => {
    navigate(`/rotem/farms/${farm.farm_id}`);
    handleMenuClose();
  };

  const handleEdit = () => {
    // TODO: Implement edit functionality
    handleMenuClose();
  };

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete ${farm.farm_name}?`)) {
      await deleteFarm(farm.farm_id);
    }
    handleMenuClose();
  };

  const getStatusColor = (isActive: boolean) => {
    return isActive ? 'success' : 'default';
  };

  const getStatusText = (isActive: boolean) => {
    return isActive ? 'Active' : 'Inactive';
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" component="h3" gutterBottom>
              {farm.farm_name}
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              {farm.gateway_alias}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              ID: {farm.farm_id}
            </Typography>
          </Box>
          <IconButton
            size="small"
            onClick={handleMenuOpen}
            aria-label="farm menu"
          >
            <MoreVert />
          </IconButton>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Chip
            label={getStatusText(farm.is_active)}
            color={getStatusColor(farm.is_active)}
            size="small"
          />
          <Chip
            label={farm.gateway_name}
            variant="outlined"
            size="small"
          />
        </Box>

        {summary && (
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="textSecondary">
                Data Points
              </Typography>
              <Typography variant="body2">
                {summary.total_data_points.toLocaleString()}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" color="textSecondary">
                Recent (24h)
              </Typography>
              <Typography variant="body2">
                {summary.recent_data_points.toLocaleString()}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="textSecondary">
                Controllers
              </Typography>
              <Typography variant="body2">
                {summary.controllers}
              </Typography>
            </Box>
          </Box>
        )}

        {isScraping && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="caption" color="textSecondary">
              Scraping data...
            </Typography>
          </Box>
        )}
      </CardContent>

      <CardActions sx={{ p: 2, pt: 0 }}>
        <Button
          size="small"
          startIcon={<Visibility />}
          onClick={handleViewDetails}
        >
          View Details
        </Button>
        <Button
          size="small"
          startIcon={<TrendingUp />}
          onClick={handleScrape}
          disabled={isScraping}
        >
          Scrape
        </Button>
      </CardActions>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
      >
        <MenuItem onClick={handleViewDetails}>
          <Visibility sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={handleScrape} disabled={isScraping}>
          <TrendingUp sx={{ mr: 1 }} />
          Scrape Data
        </MenuItem>
        <MenuItem onClick={handleEdit}>
          <Edit sx={{ mr: 1 }} />
          Edit Farm
        </MenuItem>
        <MenuItem onClick={handleDelete} sx={{ color: 'error.main' }}>
          <Delete sx={{ mr: 1 }} />
          Delete Farm
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default FarmCard;
