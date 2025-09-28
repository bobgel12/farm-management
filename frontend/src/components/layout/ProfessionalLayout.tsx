import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Box,
  Divider,
  useTheme,
  useMediaQuery,
  SwipeableDrawer,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Agriculture as FarmIcon,
  Schedule as ProgramIcon,
  People as WorkerIcon,
  Logout as LogoutIcon,
  Close as CloseIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Agriculture as AgricultureIcon,
  AccountCircle as AccountIcon,
  Security as SecurityIcon,
  Sensors as SensorsIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import EmailStatus from '../EmailStatus';

interface ProfessionalLayoutProps {
  children: React.ReactNode;
}

const ProfessionalLayout: React.FC<ProfessionalLayoutProps> = ({ children }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleLogout = async () => {
    await logout();
    navigate('/login');
    setAnchorEl(null);
  };

  const menuItems = [
    { 
      text: 'Dashboard', 
      icon: <DashboardIcon />, 
      path: '/',
      description: 'Overview and analytics'
    },
    { 
      text: 'Farms', 
      icon: <FarmIcon />, 
      path: '/farms',
      description: 'Manage farms and houses'
    },
    { 
      text: 'Rotem Integration', 
      icon: <SensorsIcon />, 
      path: '/rotem',
      description: 'Sensor data and monitoring'
    },
    { 
      text: 'Programs', 
      icon: <ProgramIcon />, 
      path: '/programs',
      description: 'Task programs and schedules'
    },
    { 
      text: 'Workers', 
      icon: <WorkerIcon />, 
      path: '/farms/1/workers',
      description: 'Manage farm workers'
    },
    { 
      text: 'Security', 
      icon: <SecurityIcon />, 
      path: '/security',
      description: 'Password and security settings'
    },
  ];

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const drawerContent = (
    <Box sx={{ width: 280, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Logo/Brand */}
      <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box display="flex" alignItems="center" gap={2}>
          <Avatar sx={{ bgcolor: 'primary.main', width: 40, height: 40 }}>
            <AgricultureIcon />
          </Avatar>
          <Box>
            <Typography variant="h6" fontWeight={700} color="primary">
              FarmFlow
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Management System
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Navigation */}
      <Box sx={{ flex: 1, py: 2 }}>
        <List>
          {menuItems.map((item) => (
            <Tooltip key={item.text} title={item.description} placement="right">
              <ListItem
                button
                onClick={() => {
                  navigate(item.path);
                  if (isMobile) setDrawerOpen(false);
                }}
                selected={isActive(item.path)}
                sx={{
                  mx: 1,
                  borderRadius: 2,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.50',
                    '&:hover': {
                      backgroundColor: 'primary.100',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: isActive(item.path) ? 'primary.main' : 'text.secondary' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.text}
                  primaryTypographyProps={{
                    fontWeight: isActive(item.path) ? 600 : 400,
                    color: isActive(item.path) ? 'primary.main' : 'text.primary',
                  }}
                />
              </ListItem>
            </Tooltip>
          ))}
        </List>
      </Box>

      {/* User Section */}
      <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
            <AccountIcon />
          </Avatar>
          <Box flex={1}>
            <Typography variant="body2" fontWeight={500}>
              {user?.username || 'Admin'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Administrator
            </Typography>
          </Box>
        </Box>
        <EmailStatus />
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setDrawerOpen(!drawerOpen)}
            sx={{ mr: 2 }}
          >
            {drawerOpen ? <CloseIcon /> : <MenuIcon />}
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            {menuItems.find(item => isActive(item.path))?.text || 'Dashboard'}
          </Typography>

          <Box display="flex" alignItems="center" gap={1}>
            <Tooltip title="Notifications">
              <IconButton color="inherit">
                <Badge badgeContent={0} color="error">
                  <NotificationsIcon />
                </Badge>
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Settings">
              <IconButton color="inherit">
                <SettingsIcon />
              </IconButton>
            </Tooltip>

            <Button
              color="inherit"
              onClick={(e) => setAnchorEl(e.currentTarget)}
              startIcon={<AccountIcon />}
              sx={{ textTransform: 'none' }}
            >
              {user?.username || 'Admin'}
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* User Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <MenuItem onClick={() => setAnchorEl(null)}>
          <ListItemIcon>
            <AccountIcon />
          </ListItemIcon>
          <ListItemText>Profile</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => setAnchorEl(null)}>
          <ListItemIcon>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon />
          </ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>

      {/* Drawer */}
      {isMobile ? (
        <SwipeableDrawer
          anchor="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          onOpen={() => setDrawerOpen(true)}
          sx={{
            '& .MuiDrawer-paper': {
              width: 280,
            },
          }}
        >
          {drawerContent}
        </SwipeableDrawer>
      ) : (
        <Drawer
          variant="persistent"
          anchor="left"
          open={drawerOpen}
          sx={{
            width: 280,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: 280,
              boxSizing: 'border-box',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${drawerOpen ? 280 : 0}px)` },
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          ml: { md: drawerOpen ? 0 : 0 },
        }}
      >
        <Toolbar />
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default ProfessionalLayout;
