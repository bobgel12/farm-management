import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Divider,
  Stack,
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  PhotoCamera as PhotoIcon,
} from '@mui/icons-material';
import { IssueListItem, IssueStatus, IssueCategory, IssuePriority } from '../../types';
import { issuesApi, IssueFilters } from '../../services/issuesApi';

interface IssueListProps {
  houseId?: number;
  farmId?: number;
  onSelectIssue?: (issue: IssueListItem) => void;
  refresh?: number;
}

const PRIORITY_COLORS: Record<IssuePriority, 'success' | 'warning' | 'error' | 'secondary'> = {
  low: 'success',
  medium: 'warning',
  high: 'error',
  critical: 'secondary',
};

const STATUS_COLORS: Record<IssueStatus, 'warning' | 'info' | 'success' | 'default'> = {
  open: 'warning',
  in_progress: 'info',
  resolved: 'success',
  closed: 'default',
};

const CATEGORY_ICONS: Record<IssueCategory, string> = {
  equipment: '🔧',
  health: '🐔',
  environment: '🌡️',
  maintenance: '🔨',
  other: '📝',
};

export const IssueList: React.FC<IssueListProps> = ({
  houseId,
  farmId,
  onSelectIssue,
  refresh = 0,
}) => {
  const [issues, setIssues] = useState<IssueListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<IssueStatus | 'open' | ''>('');
  const [categoryFilter, setCategoryFilter] = useState<IssueCategory | ''>('');

  useEffect(() => {
    loadIssues();
  }, [houseId, farmId, refresh]);

  const loadIssues = async () => {
    setLoading(true);
    setError(null);

    try {
      const filters: IssueFilters = {};
      if (houseId) filters.house_id = houseId;
      if (farmId) filters.farm_id = farmId;

      const data = await issuesApi.getIssues(filters);
      // Ensure data is an array
      setIssues(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load issues');
      setIssues([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const filteredIssues = (Array.isArray(issues) ? issues : []).filter((issue) => {
    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      if (
        !issue.title.toLowerCase().includes(term) &&
        !issue.farm_name.toLowerCase().includes(term)
      ) {
        return false;
      }
    }

    // Status filter
    if (statusFilter) {
      if (statusFilter === 'open') {
        if (issue.status !== 'open' && issue.status !== 'in_progress') {
          return false;
        }
      } else if (issue.status !== statusFilter) {
        return false;
      }
    }

    // Category filter
    if (categoryFilter && issue.category !== categoryFilter) {
      return false;
    }

    return true;
  });

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          🚨 Issues
        </Typography>

        {/* Filters */}
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ mb: 2 }}>
          <TextField
            size="small"
            placeholder="Search issues..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
            sx={{ flexGrow: 1 }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              label="Status"
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="open">Open</MenuItem>
              <MenuItem value="in_progress">In Progress</MenuItem>
              <MenuItem value="resolved">Resolved</MenuItem>
              <MenuItem value="closed">Closed</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value as any)}
              label="Category"
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="equipment">🔧 Equipment</MenuItem>
              <MenuItem value="health">🐔 Health</MenuItem>
              <MenuItem value="environment">🌡️ Environment</MenuItem>
              <MenuItem value="maintenance">🔨 Maintenance</MenuItem>
              <MenuItem value="other">📝 Other</MenuItem>
            </Select>
          </FormControl>
        </Stack>

        <Divider sx={{ mb: 2 }} />

        {filteredIssues.length === 0 ? (
          <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
            No issues found
          </Typography>
        ) : (
          <List>
            {filteredIssues.map((issue, index) => (
              <React.Fragment key={issue.id}>
                {index > 0 && <Divider />}
                <ListItem
                  sx={{
                    cursor: onSelectIssue ? 'pointer' : 'default',
                    '&:hover': onSelectIssue
                      ? { bgcolor: 'action.hover' }
                      : undefined,
                  }}
                  onClick={() => onSelectIssue?.(issue)}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <span>{CATEGORY_ICONS[issue.category]}</span>
                        <Typography variant="subtitle2">{issue.title}</Typography>
                        {issue.photo_count > 0 && (
                          <Chip
                            icon={<PhotoIcon fontSize="small" />}
                            label={issue.photo_count}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                          House {issue.house_number} • {issue.farm_name} •{' '}
                          {issue.age_display}
                        </Typography>
                        <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5 }}>
                          <Chip
                            label={issue.priority}
                            size="small"
                            color={PRIORITY_COLORS[issue.priority]}
                          />
                          <Chip
                            label={issue.status.replace('_', ' ')}
                            size="small"
                            color={STATUS_COLORS[issue.status]}
                            variant="outlined"
                          />
                        </Box>
                      </Box>
                    }
                  />
                  {onSelectIssue && (
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectIssue(issue);
                        }}
                      >
                        <ViewIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  )}
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        )}

        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Showing {filteredIssues.length} of {issues.length} issues
        </Typography>
      </CardContent>
    </Card>
  );
};

export default IssueList;

