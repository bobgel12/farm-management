import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import { OrganizationUser } from '../../types';

interface MemberEditDialogProps {
  open: boolean;
  member: OrganizationUser | null;
  onClose: () => void;
  onSave: (memberId: number, data: Partial<OrganizationUser>) => Promise<void>;
  isCurrentUserOwner: boolean;
}

const MemberEditDialog: React.FC<MemberEditDialogProps> = ({
  open,
  member,
  onClose,
  onSave,
  isCurrentUserOwner,
}) => {
  const [role, setRole] = useState<string>('worker');
  const [canManageFarms, setCanManageFarms] = useState(false);
  const [canManageUsers, setCanManageUsers] = useState(false);
  const [canViewReports, setCanViewReports] = useState(true);
  const [canExportData, setCanExportData] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (member) {
      setRole(member.role);
      setCanManageFarms(member.can_manage_farms);
      setCanManageUsers(member.can_manage_users);
      setCanViewReports(member.can_view_reports);
      setCanExportData(member.can_export_data);
    }
  }, [member]);

  const handleSave = async () => {
    if (!member) return;

    setSaving(true);
    setError(null);

    try {
      await onSave(member.id, {
        role: role as any,
        can_manage_farms: canManageFarms,
        can_manage_users: canManageUsers,
        can_view_reports: canViewReports,
        can_export_data: canExportData,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to update member');
    } finally {
      setSaving(false);
    }
  };

  const isOwner = member?.role === 'owner';

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Edit Member</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {member && (
          <Box sx={{ pt: 1 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Member
            </Typography>
            <Typography variant="body1" sx={{ mb: 3 }}>
              {member.user.first_name && member.user.last_name
                ? `${member.user.first_name} ${member.user.last_name}`
                : member.user.username}
              {' '}({member.user.email})
            </Typography>

            {isOwner ? (
              <Alert severity="info" sx={{ mb: 2 }}>
                Owner role cannot be changed. Transfer ownership to change this member's role.
              </Alert>
            ) : (
              <>
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>Role</InputLabel>
                  <Select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    label="Role"
                  >
                    <MenuItem value="admin">Administrator</MenuItem>
                    <MenuItem value="manager">Manager</MenuItem>
                    <MenuItem value="worker">Worker</MenuItem>
                    <MenuItem value="viewer">Viewer</MenuItem>
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
                        checked={canManageFarms}
                        onChange={(e) => setCanManageFarms(e.target.checked)}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">Manage Farms</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Can create, edit, and delete farms
                        </Typography>
                      </Box>
                    }
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={canManageUsers}
                        onChange={(e) => setCanManageUsers(e.target.checked)}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">Manage Users</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Can invite, edit, and remove organization members
                        </Typography>
                      </Box>
                    }
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={canViewReports}
                        onChange={(e) => setCanViewReports(e.target.checked)}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">View Reports</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Can access reports and analytics
                        </Typography>
                      </Box>
                    }
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={canExportData}
                        onChange={(e) => setCanExportData(e.target.checked)}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">Export Data</Typography>
                        <Typography variant="caption" color="text.secondary">
                          Can export data to CSV, Excel, etc.
                        </Typography>
                      </Box>
                    }
                  />
                </Box>
              </>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        {!isOwner && (
          <Button
            onClick={handleSave}
            variant="contained"
            disabled={saving}
            startIcon={saving ? <CircularProgress size={20} /> : null}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default MemberEditDialog;

