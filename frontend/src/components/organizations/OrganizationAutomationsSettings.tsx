import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Paper,
} from '@mui/material';
import { Add, Delete, Edit, Refresh } from '@mui/icons-material';
import {
  automationsApi,
  AutomationWorkflow,
  AutomationWorkflowInput,
} from '../../services/automationsApi';

interface OrganizationAutomationsSettingsProps {
  organizationId: string;
  isAdmin: boolean;
}

const emptyForm: AutomationWorkflowInput = {
  slug: '',
  name: '',
  description: '',
  webhook_url: '',
  webhook_secret: '',
  organization: '',
  farm: null,
  is_active: true,
};

const OrganizationAutomationsSettings: React.FC<OrganizationAutomationsSettingsProps> = ({
  organizationId,
  isAdmin,
}) => {
  const [workflows, setWorkflows] = useState<AutomationWorkflow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<AutomationWorkflowInput>(emptyForm);
  const [saving, setSaving] = useState(false);

  const fetchWorkflows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await automationsApi.listWorkflows({ organization_id: organizationId });
      setWorkflows(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load workflows';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    fetchWorkflows();
  }, [fetchWorkflows]);

  const openCreateDialog = () => {
    setEditingId(null);
    setForm({ ...emptyForm, organization: organizationId });
    setDialogOpen(true);
  };

  const openEditDialog = (workflow: AutomationWorkflow) => {
    setEditingId(workflow.id);
    setForm({
      slug: workflow.slug,
      name: workflow.name,
      description: workflow.description,
      webhook_url: '',
      webhook_secret: '',
      organization: organizationId,
      farm: workflow.farm_id,
      is_active: workflow.is_active,
    });
    setDialogOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const payload: Partial<AutomationWorkflowInput> = {
        slug: form.slug,
        name: form.name,
        description: form.description,
        organization: organizationId,
        farm: form.farm,
        is_active: form.is_active,
      };
      if (form.webhook_url) {
        payload.webhook_url = form.webhook_url;
      }
      if (form.webhook_secret) {
        payload.webhook_secret = form.webhook_secret;
      }

      if (editingId) {
        await automationsApi.updateWorkflow(editingId, payload);
        setSuccess('Workflow updated');
      } else {
        if (!form.webhook_url) {
          setError('Webhook URL is required');
          setSaving(false);
          return;
        }
        await automationsApi.createWorkflow({
          ...payload,
          webhook_url: form.webhook_url,
        } as AutomationWorkflowInput);
        setSuccess('Workflow created');
      }
      setDialogOpen(false);
      fetchWorkflows();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save workflow';
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this automation workflow?')) return;
    try {
      await automationsApi.deleteWorkflow(id);
      setSuccess('Workflow deleted');
      fetchWorkflows();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to delete workflow';
      setError(message);
    }
  };

  if (!isAdmin) {
    return (
      <Alert severity="info">
        Only organization admins can manage n8n automation workflows.
      </Alert>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">n8n Automations</Typography>
        <Box>
          <IconButton onClick={fetchWorkflows} size="small" aria-label="Refresh workflows">
            <Refresh />
          </IconButton>
          <Button variant="contained" startIcon={<Add />} onClick={openCreateDialog} sx={{ ml: 1 }}>
            Add Workflow
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : (
        <Card variant="outlined">
          <CardContent sx={{ p: 0 }}>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Slug</TableCell>
                    <TableCell>Scope</TableCell>
                    <TableCell>Active</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {workflows.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography color="textSecondary" py={2}>
                          No workflows configured yet.
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ) : (
                    workflows.map((workflow) => (
                      <TableRow key={workflow.id}>
                        <TableCell>{workflow.name}</TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {workflow.slug}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {workflow.farm_name || 'Organization-wide'}
                        </TableCell>
                        <TableCell>{workflow.is_active ? 'Yes' : 'No'}</TableCell>
                        <TableCell align="right">
                          <IconButton size="small" onClick={() => openEditDialog(workflow)}>
                            <Edit />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete(workflow.id)}
                          >
                            <Delete />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingId ? 'Edit Workflow' : 'Add Workflow'}</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField
              label="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Slug"
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
              fullWidth
              required
              helperText="Machine ID used in API calls, e.g. send_report"
            />
            <TextField
              label="Description"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              fullWidth
              multiline
              rows={2}
            />
            <TextField
              label="n8n Webhook URL"
              value={form.webhook_url}
              onChange={(e) => setForm({ ...form, webhook_url: e.target.value })}
              fullWidth
              required={!editingId}
              helperText={
                editingId
                  ? 'Leave blank to keep the existing URL'
                  : 'Production webhook URL from your n8n workflow'
              }
            />
            <TextField
              label="Webhook Secret (optional)"
              value={form.webhook_secret}
              onChange={(e) => setForm({ ...form, webhook_secret: e.target.value })}
              fullWidth
              type="password"
              helperText="Sent as X-Webhook-Secret header to n8n"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={form.is_active ?? true}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OrganizationAutomationsSettings;
