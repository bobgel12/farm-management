import React, { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from '@mui/material';
import { useOrganization } from '../../contexts/OrganizationContext';
import { farmsApi, extractApiErrorMessage } from '../../services/farmsApi';

interface MoveFarmToOrganizationDialogProps {
  open: boolean;
  farmId: number;
  farmName: string;
  sourceOrganizationId: string | null | undefined;
  onClose: () => void;
  onSuccess: (targetOrganizationId: string) => void;
}

const MoveFarmToOrganizationDialog: React.FC<MoveFarmToOrganizationDialogProps> = ({
  open,
  farmId,
  farmName,
  sourceOrganizationId,
  onClose,
  onSuccess,
}) => {
  const { organizations } = useOrganization();
  const [targetOrganizationId, setTargetOrganizationId] = useState('');
  const [confirmName, setConfirmName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eligibleTargetOrganizations = useMemo(
    () =>
      organizations
        .filter(
          (membership) =>
            (membership.is_owner || membership.is_admin) &&
            membership.organization.id !== sourceOrganizationId
        )
        .map((membership) => membership.organization),
    [organizations, sourceOrganizationId]
  );

  const canSubmit =
    Boolean(targetOrganizationId) &&
    confirmName.trim() === farmName.trim() &&
    !submitting;

  const handleClose = () => {
    if (submitting) {
      return;
    }
    setTargetOrganizationId('');
    setConfirmName('');
    setError(null);
    onClose();
  };

  const handleTransfer = async () => {
    if (!canSubmit) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      await farmsApi.transferFarm(farmId, targetOrganizationId);
      const transferredTo = targetOrganizationId;
      setTargetOrganizationId('');
      setConfirmName('');
      onSuccess(transferredTo);
      onClose();
    } catch (err) {
      setError(extractApiErrorMessage(err, 'Failed to transfer farm'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Move farm to another organization</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Move <strong>{farmName}</strong> and all of its data to a different organization.
          You must be an administrator of both the current and target organizations.
        </Typography>

        <Alert severity="warning" sx={{ mb: 2 }}>
          <Typography variant="body2" component="div">
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Houses, tasks, and flock data move with the farm.</li>
              <li>Organization-specific n8n workflows may need reconfiguration.</li>
              <li>The farm will disappear from the source organization for other members.</li>
            </ul>
          </Typography>
        </Alert>

        {eligibleTargetOrganizations.length === 0 ? (
          <Alert severity="info">
            No other organizations are available. You need admin access on at least one
            other organization to transfer this farm.
          </Alert>
        ) : (
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="target-org-label">Target organization</InputLabel>
            <Select
              labelId="target-org-label"
              label="Target organization"
              value={targetOrganizationId}
              onChange={(event) => setTargetOrganizationId(event.target.value)}
            >
              {eligibleTargetOrganizations.map((org) => (
                <MenuItem key={org.id} value={org.id}>
                  {org.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}

        <TextField
          fullWidth
          label={`Type "${farmName}" to confirm`}
          value={confirmName}
          onChange={(event) => setConfirmName(event.target.value)}
          disabled={eligibleTargetOrganizations.length === 0}
          autoComplete="off"
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={submitting}>
          Cancel
        </Button>
        <Button
          onClick={handleTransfer}
          variant="contained"
          color="warning"
          disabled={!canSubmit || eligibleTargetOrganizations.length === 0}
          startIcon={submitting ? <CircularProgress size={18} color="inherit" /> : undefined}
        >
          {submitting ? 'Transferring...' : 'Transfer'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MoveFarmToOrganizationDialog;
