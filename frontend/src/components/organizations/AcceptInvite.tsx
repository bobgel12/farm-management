import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Divider,
  Chip,
} from '@mui/material';
import {
  Business as BusinessIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { organizationsApi } from '../../services/organizationsApi';
import { useAuth } from '../../contexts/AuthContext';
import { InviteInfo } from '../../types';

const AcceptInvite: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();

  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [acceptedOrg, setAcceptedOrg] = useState<{ id: string; name: string } | null>(null);

  // Registration form state (for new users)
  const [showRegistration, setShowRegistration] = useState(false);
  const [registrationData, setRegistrationData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
  });
  const [registrationErrors, setRegistrationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (token) {
      loadInviteInfo();
    }
  }, [token]);

  const loadInviteInfo = async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const info = await organizationsApi.getInviteInfo(token);
      setInviteInfo(info);
      
      // If invite is not valid, show appropriate error
      if (!info.is_valid) {
        if (info.is_expired) {
          setError('This invitation has expired. Please request a new invitation.');
        } else {
          setError('This invitation is no longer valid.');
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Invalid or expired invitation link.');
    } finally {
      setLoading(false);
    }
  };

  const validateRegistration = (): boolean => {
    const errors: Record<string, string> = {};

    if (!registrationData.username.trim()) {
      errors.username = 'Username is required';
    } else if (registrationData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    }

    if (!registrationData.password) {
      errors.password = 'Password is required';
    } else if (registrationData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }

    if (registrationData.password !== registrationData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setRegistrationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAcceptInvite = async () => {
    if (!token || !inviteInfo) return;

    // If user is not logged in and doesn't have an existing account
    if (!user && !inviteInfo.has_existing_user && !showRegistration) {
      setShowRegistration(true);
      return;
    }

    // If showing registration, validate the form
    if (showRegistration && !validateRegistration()) {
      return;
    }

    setAccepting(true);
    setError(null);

    try {
      const result = await organizationsApi.acceptInvite(
        token,
        showRegistration ? {
          username: registrationData.username,
          password: registrationData.password,
          first_name: registrationData.first_name,
          last_name: registrationData.last_name,
        } : undefined
      );

      setAccepted(true);
      setAcceptedOrg(result.organization);
    } catch (err: any) {
      if (err.response?.data?.requires_registration) {
        setShowRegistration(true);
      } else {
        setError(err.response?.data?.error || 'Failed to accept invitation. Please try again.');
      }
    } finally {
      setAccepting(false);
    }
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

  if (loading || authLoading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          backgroundColor: 'grey.100',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        backgroundColor: 'grey.100',
        p: 2,
      }}
    >
      <Card sx={{ maxWidth: 480, width: '100%' }}>
        <CardContent sx={{ p: 4 }}>
          {/* Success State */}
          {accepted && acceptedOrg && (
            <Box sx={{ textAlign: 'center' }}>
              <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Welcome to {acceptedOrg.name}!
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                You have successfully joined the organization.
              </Typography>
              <Button
                variant="contained"
                size="large"
                onClick={() => navigate('/')}
                fullWidth
              >
                Go to Dashboard
              </Button>
              {!user && (
                <Button
                  variant="text"
                  onClick={() => navigate('/login')}
                  sx={{ mt: 2 }}
                  fullWidth
                >
                  Sign in to your account
                </Button>
              )}
            </Box>
          )}

          {/* Error State */}
          {error && !inviteInfo && (
            <Box sx={{ textAlign: 'center' }}>
              <ErrorIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Invalid Invitation
              </Typography>
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
              <Button
                variant="contained"
                component={RouterLink}
                to="/login"
                fullWidth
              >
                Go to Login
              </Button>
            </Box>
          )}

          {/* Invite Info State */}
          {inviteInfo && !accepted && (
            <>
              <Box sx={{ textAlign: 'center', mb: 3 }}>
                <BusinessIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" gutterBottom>
                  You're Invited!
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  {inviteInfo.invited_by} has invited you to join
                </Typography>
                <Typography variant="h6" sx={{ mt: 1 }}>
                  {inviteInfo.organization_name}
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
                <Chip
                  label={inviteInfo.role}
                  color={getRoleBadgeColor(inviteInfo.role)}
                  sx={{ textTransform: 'capitalize' }}
                />
              </Box>

              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}

              {!inviteInfo.is_valid ? (
                <Box sx={{ textAlign: 'center' }}>
                  <Alert severity="warning" sx={{ mb: 3 }}>
                    {inviteInfo.is_expired 
                      ? 'This invitation has expired. Please request a new invitation.' 
                      : 'This invitation is no longer valid.'}
                  </Alert>
                  <Button
                    variant="contained"
                    component={RouterLink}
                    to="/login"
                    fullWidth
                  >
                    Go to Login
                  </Button>
                </Box>
              ) : (
                <>
                  {/* User is logged in */}
                  {user && (
                    <Box sx={{ mb: 3 }}>
                      <Alert severity="info" icon={<PersonIcon />}>
                        Signed in as <strong>{user.username}</strong>
                      </Alert>
                    </Box>
                  )}

                  {/* User needs to log in or register */}
                  {!user && inviteInfo.has_existing_user && (
                    <Box sx={{ mb: 3 }}>
                      <Alert severity="info">
                        An account with email <strong>{inviteInfo.email}</strong> already exists.
                        Please sign in to accept this invitation.
                      </Alert>
                      <Button
                        variant="outlined"
                        component={RouterLink}
                        to="/login"
                        fullWidth
                        sx={{ mt: 2 }}
                      >
                        Sign In
                      </Button>
                      <Divider sx={{ my: 2 }}>or</Divider>
                    </Box>
                  )}

                  {/* Registration Form */}
                  {showRegistration && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" gutterBottom>
                        Create your account
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Your email: {inviteInfo.email}
                      </Typography>
                      <TextField
                        fullWidth
                        label="Username"
                        value={registrationData.username}
                        onChange={(e) => setRegistrationData({ 
                          ...registrationData, 
                          username: e.target.value 
                        })}
                        error={Boolean(registrationErrors.username)}
                        helperText={registrationErrors.username}
                        sx={{ mb: 2 }}
                      />
                      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                        <TextField
                          fullWidth
                          label="First Name"
                          value={registrationData.first_name}
                          onChange={(e) => setRegistrationData({ 
                            ...registrationData, 
                            first_name: e.target.value 
                          })}
                        />
                        <TextField
                          fullWidth
                          label="Last Name"
                          value={registrationData.last_name}
                          onChange={(e) => setRegistrationData({ 
                            ...registrationData, 
                            last_name: e.target.value 
                          })}
                        />
                      </Box>
                      <TextField
                        fullWidth
                        label="Password"
                        type="password"
                        value={registrationData.password}
                        onChange={(e) => setRegistrationData({ 
                          ...registrationData, 
                          password: e.target.value 
                        })}
                        error={Boolean(registrationErrors.password)}
                        helperText={registrationErrors.password}
                        sx={{ mb: 2 }}
                      />
                      <TextField
                        fullWidth
                        label="Confirm Password"
                        type="password"
                        value={registrationData.confirmPassword}
                        onChange={(e) => setRegistrationData({ 
                          ...registrationData, 
                          confirmPassword: e.target.value 
                        })}
                        error={Boolean(registrationErrors.confirmPassword)}
                        helperText={registrationErrors.confirmPassword}
                        sx={{ mb: 2 }}
                      />
                    </Box>
                  )}

                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleAcceptInvite}
                    disabled={accepting}
                    fullWidth
                    startIcon={accepting ? <CircularProgress size={20} /> : null}
                  >
                    {accepting 
                      ? 'Accepting...' 
                      : showRegistration 
                        ? 'Create Account & Join' 
                        : 'Accept Invitation'}
                  </Button>

                  {!user && !inviteInfo.has_existing_user && !showRegistration && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                      You'll be asked to create an account
                    </Typography>
                  )}
                </>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default AcceptInvite;

