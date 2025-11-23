import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Save as SaveIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useOrganization } from '../../contexts/OrganizationContext';
import { Organization, OrganizationUser } from '../../types';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const OrganizationSettings: React.FC = () => {
  const {
    currentOrganization,
    members,
    loading,
    error,
    fetchMembers,
    updateOrganization,
    addMember,
    removeMember,
    isOwner,
    isAdmin,
  } = useOrganization();

  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState<Partial<Organization>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [addMemberDialogOpen, setAddMemberDialogOpen] = useState(false);
  const [newMemberData, setNewMemberData] = useState({
    user_id: '',
    role: 'worker' as const,
    can_manage_farms: false,
    can_manage_users: false,
    can_view_reports: true,
    can_export_data: false,
  });

  useEffect(() => {
    if (currentOrganization) {
      setFormData({
        name: currentOrganization.name,
        description: currentOrganization.description || '',
        contact_email: currentOrganization.contact_email,
        contact_phone: currentOrganization.contact_phone || '',
        website: currentOrganization.website || '',
        address: currentOrganization.address || '',
      });
      fetchMembers(currentOrganization.id);
    }
  }, [currentOrganization, fetchMembers]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrganization) return;

    setSubmitError(null);
    setSubmitting(true);

    try {
      await updateOrganization(currentOrganization.id, formData);
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to update organization');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddMember = async () => {
    if (!currentOrganization) return;

    try {
      await addMember(
        currentOrganization.id,
        parseInt(newMemberData.user_id),
        newMemberData.role
      );
      setAddMemberDialogOpen(false);
      setNewMemberData({
        user_id: '',
        role: 'worker',
        can_manage_farms: false,
        can_manage_users: false,
        can_view_reports: true,
        can_export_data: false,
      });
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to add member');
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!currentOrganization) return;
    if (!window.confirm('Are you sure you want to remove this member?')) return;

    try {
      await removeMember(currentOrganization.id, userId);
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to remove member');
    }
  };

  if (!currentOrganization) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>No organization selected</Typography>
      </Box>
    );
  }

  if (!isOwner && !isAdmin) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          You do not have permission to manage organization settings.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
          Organization Settings
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage organization details and members
        </Typography>
      </Box>

      {(error || submitError) && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {submitError || error}
        </Alert>
      )}

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            <Tab label="Details" icon={<BusinessIcon />} iconPosition="start" />
            <Tab label="Members" icon={<PeopleIcon />} iconPosition="start" />
            <Tab label="Settings" icon={<SettingsIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        <CardContent>
          <TabPanel value={activeTab} index={0}>
            <form onSubmit={handleSubmit}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    required
                    label="Organization Name"
                    value={formData.name || ''}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Slug"
                    value={currentOrganization.slug}
                    disabled
                    helperText="Slug cannot be changed"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Description"
                    multiline
                    rows={3}
                    value={formData.description || ''}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    required
                    label="Contact Email"
                    type="email"
                    value={formData.contact_email || ''}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Contact Phone"
                    value={formData.contact_phone || ''}
                    onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Website"
                    value={formData.website || ''}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Address"
                    multiline
                    rows={2}
                    value={formData.address || ''}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button
                      type="submit"
                      variant="contained"
                      startIcon={submitting ? <CircularProgress size={20} /> : <SaveIcon />}
                      disabled={submitting}
                    >
                      {submitting ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </form>
          </TabPanel>

          <TabPanel value={activeTab} index={1}>
            <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">Organization Members</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setAddMemberDialogOpen(true)}
              >
                Add Member
              </Button>
            </Box>

            <List>
              {members.map((member) => (
                <React.Fragment key={member.id}>
                  <ListItem>
                    <ListItemText
                      primary={member.user.username}
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                          <Chip label={member.role} size="small" color="primary" variant="outlined" />
                          {member.can_manage_farms && <Chip label="Manage Farms" size="small" />}
                          {member.can_manage_users && <Chip label="Manage Users" size="small" />}
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      {member.role !== 'owner' && (isOwner || isAdmin) && (
                        <IconButton
                          edge="end"
                          onClick={() => handleRemoveMember(member.user.id)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      )}
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </TabPanel>

          <TabPanel value={activeTab} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Subscription
                    </Typography>
                    <Chip
                      label={currentOrganization.subscription_tier}
                      color="primary"
                      sx={{ mt: 1 }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      Status: {currentOrganization.subscription_status}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="subtitle1" gutterBottom>
                      Usage Limits
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Farms: {currentOrganization.total_farms || 0} / {currentOrganization.max_farms}
                    </Typography>
                    <Typography variant="body2">
                      Users: {currentOrganization.total_users || 0} / {currentOrganization.max_users}
                    </Typography>
                    <Typography variant="body2">
                      Houses per Farm: {currentOrganization.max_houses_per_farm}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>

      {/* Add Member Dialog */}
      <Dialog open={addMemberDialogOpen} onClose={() => setAddMemberDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Organization Member</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="User ID"
              type="number"
              value={newMemberData.user_id}
              onChange={(e) => setNewMemberData({ ...newMemberData, user_id: e.target.value })}
              sx={{ mb: 2 }}
            />
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Role</InputLabel>
              <Select
                value={newMemberData.role}
                onChange={(e) => setNewMemberData({ ...newMemberData, role: e.target.value as any })}
                label="Role"
              >
                <MenuItem value="worker">Worker</MenuItem>
                <MenuItem value="manager">Manager</MenuItem>
                <MenuItem value="admin">Administrator</MenuItem>
                {isOwner && <MenuItem value="owner">Owner</MenuItem>}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddMemberDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddMember} variant="contained">
            Add Member
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OrganizationSettings;

