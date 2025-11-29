import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Skeleton,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Business as BusinessIcon,
  Settings as SettingsIcon,
  Delete as DeleteIcon,
  SwapHoriz as SwitchIcon,
  People as PeopleIcon,
  Agriculture as FarmIcon,
  Home as HouseIcon,
} from '@mui/icons-material';
import { useOrganization } from '../../contexts/OrganizationContext';
import { OrganizationMembership } from '../../types';

const OrganizationList: React.FC = () => {
  const navigate = useNavigate();
  const {
    organizations,
    currentOrganization,
    setCurrentOrganization,
    deleteOrganization,
    loading,
    error,
  } = useOrganization();

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedOrg, setSelectedOrg] = useState<OrganizationMembership | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, org: OrganizationMembership) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setSelectedOrg(org);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedOrg(null);
  };

  const handleSwitchTo = (org: OrganizationMembership) => {
    setCurrentOrganization(org.organization);
    handleMenuClose();
  };

  const handleSettings = (org: OrganizationMembership) => {
    setCurrentOrganization(org.organization);
    navigate('/organization/settings');
    handleMenuClose();
  };

  const handleDeleteClick = () => {
    setDeleteDialogOpen(true);
    setAnchorEl(null);
  };

  const handleDeleteConfirm = async () => {
    if (!selectedOrg) return;
    
    setDeleting(true);
    try {
      await deleteOrganization(selectedOrg.organization.id);
      setDeleteDialogOpen(false);
      setSelectedOrg(null);
    } catch (err) {
      // Error is handled by context
    } finally {
      setDeleting(false);
    }
  };

  const getRoleBadgeColor = (role: string): 'primary' | 'secondary' | 'default' | 'success' | 'info' => {
    switch (role) {
      case 'owner':
        return 'primary';
      case 'admin':
        return 'secondary';
      case 'manager':
        return 'success';
      case 'worker':
        return 'info';
      default:
        return 'default';
    }
  };

  const getTierBadgeColor = (tier: string): 'default' | 'primary' | 'secondary' | 'success' | 'warning' => {
    switch (tier) {
      case 'enterprise':
        return 'primary';
      case 'premium':
        return 'secondary';
      case 'standard':
        return 'success';
      case 'basic':
        return 'default';
      default:
        return 'warning';
    }
  };

  if (loading && organizations.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" sx={{ mb: 3 }}>Organizations</Typography>
        <Grid container spacing={3}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2 }} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
            Organizations
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage your organizations and memberships
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/organizations/new')}
        >
          New Organization
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {organizations.length === 0 ? (
        <Card sx={{ p: 4, textAlign: 'center' }}>
          <BusinessIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No Organizations Yet
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first organization to get started managing your farms.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/organizations/new')}
          >
            Create Organization
          </Button>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {organizations.map((membership) => {
            const org = membership.organization;
            const isCurrentOrg = currentOrganization?.id === org.id;

            return (
              <Grid item xs={12} sm={6} md={4} key={org.id}>
                <Card 
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    border: isCurrentOrg ? 2 : 1,
                    borderColor: isCurrentOrg ? 'primary.main' : 'divider',
                    position: 'relative',
                    transition: 'all 0.2s',
                    '&:hover': {
                      boxShadow: 4,
                    },
                  }}
                >
                  {isCurrentOrg && (
                    <Chip 
                      label="Current" 
                      size="small" 
                      color="primary" 
                      sx={{ 
                        position: 'absolute', 
                        top: 12, 
                        left: 12,
                        fontWeight: 600,
                      }} 
                    />
                  )}
                  
                  <CardContent sx={{ flexGrow: 1, pt: isCurrentOrg ? 5 : 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <BusinessIcon sx={{ color: 'primary.main' }} />
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {org.name}
                        </Typography>
                      </Box>
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, membership)}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                      <Chip
                        label={membership.role}
                        size="small"
                        color={getRoleBadgeColor(membership.role)}
                        sx={{ textTransform: 'capitalize' }}
                      />
                      <Chip
                        label={org.subscription_tier}
                        size="small"
                        color={getTierBadgeColor(org.subscription_tier)}
                        variant="outlined"
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </Box>

                    {org.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {org.description.length > 100 
                          ? `${org.description.substring(0, 100)}...` 
                          : org.description}
                      </Typography>
                    )}

                    <Box sx={{ display: 'flex', gap: 3, mt: 'auto' }}>
                      <Tooltip title="Total Farms">
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <FarmIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {org.total_farms || 0}
                          </Typography>
                        </Box>
                      </Tooltip>
                      <Tooltip title="Total Users">
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <PeopleIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {org.total_users || 0}
                          </Typography>
                        </Box>
                      </Tooltip>
                      <Tooltip title="Total Houses">
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          <HouseIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {org.total_houses || 0}
                          </Typography>
                        </Box>
                      </Tooltip>
                    </Box>
                  </CardContent>

                  <CardActions sx={{ borderTop: 1, borderColor: 'divider', px: 2 }}>
                    {!isCurrentOrg && (
                      <Button 
                        size="small" 
                        startIcon={<SwitchIcon />}
                        onClick={() => handleSwitchTo(membership)}
                      >
                        Switch to
                      </Button>
                    )}
                    <Button 
                      size="small" 
                      startIcon={<SettingsIcon />}
                      onClick={() => handleSettings(membership)}
                    >
                      Settings
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {selectedOrg && currentOrganization?.id !== selectedOrg.organization.id && (
          <MenuItem onClick={() => handleSwitchTo(selectedOrg)}>
            <ListItemIcon>
              <SwitchIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Switch to this organization</ListItemText>
          </MenuItem>
        )}
        <MenuItem onClick={() => selectedOrg && handleSettings(selectedOrg)}>
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>
        {selectedOrg?.is_owner && (
          <MenuItem onClick={handleDeleteClick} sx={{ color: 'error.main' }}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Delete Organization</ListItemText>
          </MenuItem>
        )}
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Organization?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete <strong>{selectedOrg?.organization.name}</strong>? 
            This action cannot be undone. All farms, houses, and data associated with this 
            organization will be permanently deleted.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={deleting}>
            Cancel
          </Button>
          <Button 
            onClick={handleDeleteConfirm} 
            color="error" 
            variant="contained"
            disabled={deleting}
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OrganizationList;

