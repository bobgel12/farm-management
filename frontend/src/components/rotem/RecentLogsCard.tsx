import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Schedule,
  Warning,
  AccessTime,
} from '@mui/icons-material';
import { RotemScrapeLog } from '../../types/rotem';

interface RecentLogsCardProps {
  logs: RotemScrapeLog[];
}

const RecentLogsCard: React.FC<RecentLogsCardProps> = ({ logs }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle color="success" />;
      case 'failed':
        return <Error color="error" />;
      case 'running':
        return <Schedule color="info" />;
      case 'partial':
        return <Warning color="warning" />;
      default:
        return <Warning color="action" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'info';
      case 'partial':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const formatDuration = (startedAt: string, completedAt: string | null) => {
    if (!completedAt) return 'Running...';
    
    const start = new Date(startedAt);
    const end = new Date(completedAt);
    const diffMs = end.getTime() - start.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    
    if (diffSecs < 60) return `${diffSecs}s`;
    const diffMins = Math.floor(diffSecs / 60);
    return `${diffMins}m ${diffSecs % 60}s`;
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Recent Scraping Logs
        </Typography>
        <Divider sx={{ mb: 2 }} />

        {logs.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="body2" color="textSecondary">
              No scraping logs available
            </Typography>
          </Box>
        ) : (
          <List dense>
            {logs.slice(0, 5).map((log) => (
              <ListItem key={log.id} sx={{ px: 0 }}>
                <ListItemIcon sx={{ minWidth: 32 }}>
                  {getStatusIcon(log.status)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        Scrape {log.scrape_id.substring(0, 8)}...
                      </Typography>
                      <Chip
                        label={log.status}
                        size="small"
                        color={getStatusColor(log.status)}
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <AccessTime fontSize="small" color="action" />
                        <Typography variant="caption" color="textSecondary">
                          {formatTimestamp(log.started_at)}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          • {formatDuration(log.started_at, log.completed_at)}
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="textSecondary">
                        {log.data_points_collected} data points collected
                      </Typography>
                      {log.error_message && (
                        <Tooltip title={log.error_message} arrow>
                          <Typography
                            variant="caption"
                            color="error"
                            sx={{
                              display: 'block',
                              mt: 0.5,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              maxWidth: '200px',
                            }}
                          >
                            Error: {log.error_message}
                          </Typography>
                        </Tooltip>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}

        {logs.length > 5 && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="textSecondary">
              Showing 5 of {logs.length} logs
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default RecentLogsCard;
