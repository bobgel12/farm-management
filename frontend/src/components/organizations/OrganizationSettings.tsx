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
  FormControlLabel,
  Switch,
  Tooltip,
  Snackbar,
} from '@mui/material';
import {
  Save as SaveIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  Refresh as RefreshIcon,
  Cancel as CancelIcon,
  Mail as MailIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useOrganization } from '../../contexts/OrganizationContext';
import { Organization, OrganizationUser, OrganizationInvite } from '../../types';
import MemberEditDialog from './MemberEditDialog';

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
    pendingInvites,
    loading,
    error,
    fetchMembers,
    fetchPendingInvites,
    updateOrganization,
    updateMember,
    removeMember,
    sendInvite,
    resendInvite,
    cancelInvite,
    isOwner,
    isAdmin,
  } = useOrganization();

  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState<Partial<Organization>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Invite dialog state
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<string>('worker');
  const [invitePermissions, setInvitePermissions] = useState({
    can_manage_farms: false,
    can_manage_users: false,
    can_view_reports: true,
    can_export_data: false,
  });
  const [sendingInvite, setSendingInvite] = useState(false);
  
  // Member edit dialog state
  const [editMemberDialogOpen, setEditMemberDialogOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState<OrganizationUser | null>(null);

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
      fetchPendingInvites(currentOrganization.id);
    }
  }, [currentOrganization, fetchMembers, fetchPendingInvites]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrganization) return;

    setSubmitError(null);
    setSubmitting(true);

    try {
      await updateOrganization(currentOrganization.id, formData);
      setSuccessMessage('Organization updated successfully');
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to update organization');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendInvite = async () => {
    if (!currentOrganization || !inviteEmail) return;

    setSendingInvite(true);
    setSubmitError(null);

    try {
      await sendInvite(
        currentOrganization.id,
        inviteEmail,
        inviteRole,
        invitePermissions
      );
      setInviteDialogOpen(false);
      setInviteEmail('');
      setInviteRole('worker');
      setInvitePermissions({
        can_manage_farms: false,
        can_manage_users: false,
        can_view_reports: true,
        can_export_data: false,
      });
      setSuccessMessage('Invitation sent successfully');
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to send invitation');
    } finally {
      setSendingInvite(false);
    }
  };

  const handleResendInvite = async (inviteId: string) => {
    if (!currentOrganization) return;

    try {
      await resendInvite(currentOrganization.id, inviteId);
      setSuccessMessage('Invitation resent successfully');
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to resend invitation');
    }
  };

  const handleCancelInvite = async (inviteId: string) => {
    if (!currentOrganization) return;
    if (!window.confirm('Are you sure you want to cancel this invitation?')) return;

    try {
      await cancelInvite(currentOrganization.id, inviteId);
      setSuccessMessage('Invitation cancelled');
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to cancel invitation');
    }
  };

  const handleRemoveMember = async (userId: number) => {
    if (!currentOrganization) return;
    if (!window.confirm('Are you sure you want to remove this member?')) return;

    try {
      await removeMember(currentOrganization.id, userId);
      setSuccessMessage('Member removed successfully');
    } catch (err: any) {
      setSubmitError(err.message || 'Failed to remove member');
    }
  };

  const handleEditMember = (member: OrganizationUser) => {
    setSelectedMember(member);
    setEditMemberDialogOpen(true);
  };

  const handleSaveMember = async (memberId: number, data: Partial<OrganizationUser>) => {
    await updateMember(memberId, data);
    setSuccessMessage('Member updated successfully');
  };

  const getRoleBadgeColor = (role: string): 'primary' | 'secondary' | 'default' | 'success' | 'info' => {
    switch (role) {
      case 'owner': return 'primary';
      case 'admin': return 'secondary';
      case 'manager': return 'success';
      case 'worker': return 'info';
      default: return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
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
          Manage organization details, members, and invitations
        </Typography>
      </Box>

      {(error || submitError) && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setSubmitError(null)}>
          {submitError || error}
        </Alert>
      )}

      <Snackbar
        open={Boolean(successMessage)}
        autoHideDuration={4000}
        onClose={() => setSuccessMessage(null)}
        message={successMessage}
      />

      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            <Tab label="Details" icon={<BusinessIcon />} iconPosition="start" />
            <Tab label="Members" icon={<PeopleIcon />} iconPosition="start" />
            <Tab label="Settings" icon={<SettingsIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        <CardContent>
          {/* Details Tab */}
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

          {/* Members Tab */}
          <TabPanel value={activeTab} index={1}>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">Organization Members</Typography>
              <Button
                variant="contained"
                startIcon={<MailIcon />}
                onClick={() => setInviteDialogOpen(true)}
              >
                Invite Member
              </Button>
            </Box>

            {/* Current Members */}
            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
              Current Members ({members.length})
            </Typography>
            <List sx={{ mb: 4 }}>
              {members.map((member) => (
                <React.Fragment key={member.id}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body1">
                            {member.user.first_name && member.user.last_name
                              ? `${member.user.first_name} ${member.user.last_name}`
                              : member.user.username}
                          </Typography>
                          <Chip
                            label={member.role}
                            size="small"
                            color={getRoleBadgeColor(member.role)}
                            sx={{ textTransform: 'capitalize' }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box sx={{ mt: 0.5 }}>
                          <Typography variant="body2" color="text.secondary">
                            {member.user.email} · Joined {formatDate(member.joined_at)}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5, flexWrap: 'wrap' }}>
                            {member.can_manage_farms && (
                              <Chip label="Farms" size="small" variant="outlined" />
                            )}
                            {member.can_manage_users && (
                              <Chip label="Users" size="small" variant="outlined" />
                            )}
                            {member.can_view_reports && (
                              <Chip label="Reports" size="small" variant="outlined" />
                            )}
                            {member.can_export_data && (
                              <Chip label="Export" size="small" variant="outlined" />
                            )}
                          </Box>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      {member.role !== 'owner' && (isOwner || isAdmin) && (
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="Edit member">
                            <IconButton
                              edge="end"
                              onClick={() => handleEditMember(member)}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Remove member">
                            <IconButton
                              edge="end"
                              onClick={() => handleRemoveMember(member.user.id)}
                              color="error"
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      )}
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider component="li" />
                </React.Fragment>
              ))}
            </List>

            {/* Pending Invites */}
            {pendingInvites.length > 0 && (
              <>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  Pending Invitations ({pendingInvites.length})
                </Typography>
                <List>
                  {pendingInvites.map((invite) => (
                    <React.Fragment key={invite.id}>
                      <ListItem>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body1">{invite.email}</Typography>
                              <Chip
                                label={invite.role}
                                size="small"
                                color={getRoleBadgeColor(invite.role)}
                                sx={{ textTransform: 'capitalize' }}
                              />
                              <Chip
                                label="Pending"
                                size="small"
                                color="warning"
                                icon={<ScheduleIcon />}
                              />
                            </Box>
                          }
                          secondary={
                            <Typography variant="body2" color="text.secondary">
                              Invited {formatDate(invite.created_at)} · 
                              Expires {formatDate(invite.expires_at)}
                            </Typography>
                          }
                        />
                        <ListItemSecondaryAction>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Resend invitation">
                              <IconButton
                                edge="end"
                                onClick={() => handleResendInvite(invite.id)}
                              >
                                <RefreshIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Cancel invitation">
                              <IconButton
                                edge="end"
                                onClick={() => handleCancelInvite(invite.id)}
                                color="error"
                              >
                                <CancelIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </ListItemSecondaryAction>
                      </ListItem>
                      <Divider component="li" />
                    </React.Fragment>
                  ))}
                </List>
              </>
            )}
          </TabPanel>

          {/* Settings Tab */}
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
                      sx={{ mt: 1, textTransform: 'capitalize' }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      Status: <strong>{currentOrganization.subscription_status}</strong>
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
                      Farms: <strong>{currentOrganization.total_farms || 0}</strong> / {currentOrganization.max_farms}
                    </Typography>
                    <Typography variant="body2">
                      Users: <strong>{currentOrganization.total_users || 0}</strong> / {currentOrganization.max_users}
                    </Typography>
                    <Typography variant="body2">
                      Houses per Farm: <strong>{currentOrganization.max_houses_per_farm}</strong>
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>
        </CardContent>
      </Card>

      {/* Invite Member Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Invite Member</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="colleague@example.com"
              sx={{ mb: 3 }}
            />
            
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Role</InputLabel>
              <Select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                label="Role"
              >
                <MenuItem value="viewer">Viewer</MenuItem>
                <MenuItem value="worker">Worker</MenuItem>
                <MenuItem value="manager">Manager</MenuItem>
                <MenuItem value="admin">Administrator</MenuItem>
                {isOwner && <MenuItem value="owner">Owner</MenuItem>}
              </Select>
            </FormControl>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Permissions
            </Typography>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={invitePermissions.can_manage_farms}
                    onChange={(e) => setInvitePermissions({
                      ...invitePermissions,
                      can_manage_farms: e.target.checked,
                    })}
                  />
                }
                label="Can manage farms"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={invitePermissions.can_manage_users}
                    onChange={(e) => setInvitePermissions({
                      ...invitePermissions,
                      can_manage_users: e.target.checked,
                    })}
                  />
                }
                label="Can manage users"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={invitePermissions.can_view_reports}
                    onChange={(e) => setInvitePermissions({
                      ...invitePermissions,
                      can_view_reports: e.target.checked,
                    })}
                  />
                }
                label="Can view reports"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={invitePermissions.can_export_data}
                    onChange={(e) => setInvitePermissions({
                      ...invitePermissions,
                      can_export_data: e.target.checked,
                    })}
                  />
                }
                label="Can export data"
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)} disabled={sendingInvite}>
            Cancel
          </Button>
          <Button
            onClick={handleSendInvite}
            variant="contained"
            disabled={!inviteEmail || sendingInvite}
            startIcon={sendingInvite ? <CircularProgress size={20} /> : <SendIcon />}
          >
            {sendingInvite ? 'Sending...' : 'Send Invitation'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Member Edit Dialog */}
      <MemberEditDialog
        open={editMemberDialogOpen}
        member={selectedMember}
        onClose={() => {
          setEditMemberDialogOpen(false);
          setSelectedMember(null);
        }}
        onSave={handleSaveMember}
        isCurrentUserOwner={isOwner}
      />
    </Box>
  );
};

export default OrganizationSettings;
