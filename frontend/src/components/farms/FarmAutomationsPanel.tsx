import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
  Typography,
} from '@mui/material';
import { PlayArrow, Science, Refresh } from '@mui/icons-material';
import {
  automationsApi,
  AutomationWorkflow,
  AutomationTriggerResult,
} from '../../services/automationsApi';

interface FarmAutomationsPanelProps {
  organizationId: string;
  farmId?: number;
  showTestButton?: boolean;
  compact?: boolean;
}

const FarmAutomationsPanel: React.FC<FarmAutomationsPanelProps> = ({
  organizationId,
  farmId,
  showTestButton = false,
  compact = false,
}) => {
  const [workflows, setWorkflows] = useState<AutomationWorkflow[]>([]);
  const [loading, setLoading] = useState(false);
  const [triggeringSlug, setTriggeringSlug] = useState<string | null>(null);
  const [testingSlug, setTestingSlug] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AutomationTriggerResult | null>(null);

  const fetchWorkflows = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await automationsApi.listWorkflows({
        organization_id: organizationId,
        farm_id: farmId,
      });
      setWorkflows(data.filter((w) => w.is_active));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load automations';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [organizationId, farmId]);

  useEffect(() => {
    if (organizationId) {
      fetchWorkflows();
    }
  }, [organizationId, farmId, fetchWorkflows]);

  const handleTrigger = async (slug: string) => {
    setTriggeringSlug(slug);
    setError(null);
    setResult(null);
    try {
      const response = await automationsApi.triggerWorkflow(slug, {
        organizationId,
        farmId,
      });
      setResult(response);
      if (response.status !== 'success') {
        setError(response.message);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to trigger workflow';
      setError(message);
    } finally {
      setTriggeringSlug(null);
    }
  };

  const handleTest = async (slug: string) => {
    setTestingSlug(slug);
    setError(null);
    setResult(null);
    try {
      const response = await automationsApi.testWorkflow(slug, {
        organizationId,
        farmId,
      });
      setResult(response);
      if (response.status !== 'success') {
        setError(response.message);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to test workflow';
      setError(message);
    } finally {
      setTestingSlug(null);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" py={2}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (workflows.length === 0) {
    return (
      <Typography variant="body2" color="textSecondary">
        No automation workflows configured for this {farmId ? 'farm' : 'organization'}.
      </Typography>
    );
  }

  if (compact) {
    return (
      <Box display="flex" flexWrap="wrap" gap={1} alignItems="center">
        {workflows.map((workflow) => (
          <Button
            key={workflow.id}
            variant="outlined"
            size="small"
            startIcon={
              triggeringSlug === workflow.slug ? (
                <CircularProgress size={14} />
              ) : (
                <PlayArrow />
              )
            }
            onClick={() => handleTrigger(workflow.slug)}
            disabled={triggeringSlug !== null}
          >
            {triggeringSlug === workflow.slug ? 'Running...' : workflow.name}
          </Button>
        ))}
        {error && (
          <Typography variant="caption" color="error">
            {error}
          </Typography>
        )}
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="subtitle1" fontWeight={600}>
          n8n Automations
        </Typography>
        <IconButton onClick={fetchWorkflows} size="small" aria-label="Refresh automations">
          <Refresh />
        </IconButton>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {result?.status === 'success' && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {result.message} ({result.execution_time?.toFixed(2)}s)
        </Alert>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Scope</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {workflows.map((workflow) => (
              <TableRow key={workflow.id}>
                <TableCell>{workflow.name}</TableCell>
                <TableCell>{workflow.description || '—'}</TableCell>
                <TableCell>
                  {workflow.farm_name ? workflow.farm_name : 'Organization-wide'}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Run workflow">
                    <span>
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => handleTrigger(workflow.slug)}
                        disabled={triggeringSlug !== null}
                      >
                        {triggeringSlug === workflow.slug ? (
                          <CircularProgress size={18} />
                        ) : (
                          <PlayArrow />
                        )}
                      </IconButton>
                    </span>
                  </Tooltip>
                  {showTestButton && (
                    <Tooltip title="Test webhook connection">
                      <span>
                        <IconButton
                          size="small"
                          onClick={() => handleTest(workflow.slug)}
                          disabled={testingSlug !== null}
                        >
                          {testingSlug === workflow.slug ? (
                            <CircularProgress size={18} />
                          ) : (
                            <Science />
                          )}
                        </IconButton>
                      </span>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default FarmAutomationsPanel;
