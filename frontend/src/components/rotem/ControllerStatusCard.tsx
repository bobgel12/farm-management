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
  Alert,
} from '@mui/material';
import {
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { RotemController } from '../../types/rotem';

interface ControllerStatusCardProps {
  controllers: RotemController[];
}

const ControllerStatusCard: React.FC<ControllerStatusCardProps> = ({ controllers }) => {
  const connectedControllers = controllers.filter(c => c.is_connected).length;
  const totalControllers = controllers.length;

  const getStatusIcon = (isConnected: boolean) => {
    return isConnected ? (
      <CheckCircle color="success" />
    ) : (
      <Error color="error" />
    );
  };

  const getStatusColor = (isConnected: boolean) => {
    return isConnected ? 'success' : 'error';
  };

  const getLastSeenText = (lastSeen: string | null) => {
    if (!lastSeen) return 'Never';
    
    const date = new Date(lastSeen);
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

  const getConnectionHealth = () => {
    if (totalControllers === 0) return { status: 'warning' as const, text: 'No Controllers' };
    const ratio = connectedControllers / totalControllers;
    if (ratio === 1) return { status: 'success' as const, text: 'All Connected' };
    if (ratio > 0.5) return { status: 'warning' as const, text: 'Partially Connected' };
    return { status: 'error' as const, text: 'Mostly Disconnected' };
  };

  const connectionHealth = getConnectionHealth();

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Controller Status
          </Typography>
          <Chip
            label={`${connectedControllers}/${totalControllers} Connected`}
            color={connectionHealth.status as any}
            size="small"
          />
        </Box>
        <Divider sx={{ mb: 2 }} />

        {totalControllers === 0 ? (
          <Alert severity="info">
            No controllers configured for this farm.
          </Alert>
        ) : (
          <>
            <Alert 
              severity={connectionHealth.status as any}
              sx={{ mb: 2 }}
            >
              {connectionHealth.text}
            </Alert>

            <List dense>
              {controllers.map((controller) => (
                <ListItem key={controller.id} sx={{ px: 0 }}>
                  <ListItemIcon sx={{ minWidth: 32 }}>
                    {getStatusIcon(controller.is_connected)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {controller.controller_name}
                        </Typography>
                        <Chip
                          label={controller.controller_type}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="caption" color="textSecondary">
                          ID: {controller.controller_id}
                        </Typography>
                        <br />
                        <Typography variant="caption" color="textSecondary">
                          Last seen: {getLastSeenText(controller.last_seen)}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default ControllerStatusCard;
