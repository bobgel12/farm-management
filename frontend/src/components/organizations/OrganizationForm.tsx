import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
  Divider,
  InputAdornment,
} from '@mui/material';
import {
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
  Business as BusinessIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Language as WebsiteIcon,
  LocationOn as LocationIcon,
} from '@mui/icons-material';
import { useOrganization } from '../../contexts/OrganizationContext';
import { Organization } from '../../types';

interface FormData {
  name: string;
  slug: string;
  description: string;
  contact_email: string;
  contact_phone: string;
  website: string;
  address: string;
}

const initialFormData: FormData = {
  name: '',
  slug: '',
  description: '',
  contact_email: '',
  contact_phone: '',
  website: '',
  address: '',
};

const OrganizationForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditing = Boolean(id);

  const {
    currentOrganization,
    createOrganization,
    updateOrganization,
    fetchOrganization,
    loading,
  } = useOrganization();

  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  useEffect(() => {
    if (isEditing && id) {
      fetchOrganization(id);
    }
  }, [id, isEditing, fetchOrganization]);

  useEffect(() => {
    if (isEditing && currentOrganization && currentOrganization.id === id) {
      setFormData({
        name: currentOrganization.name || '',
        slug: currentOrganization.slug || '',
        description: currentOrganization.description || '',
        contact_email: currentOrganization.contact_email || '',
        contact_phone: currentOrganization.contact_phone || '',
        website: currentOrganization.website || '',
        address: currentOrganization.address || '',
      });
    }
  }, [currentOrganization, id, isEditing]);

  // Auto-generate slug from name
  const generateSlug = (name: string): string => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  };

  const handleChange = (field: keyof FormData) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const value = e.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Auto-generate slug when name changes (only for new organizations)
    if (field === 'name' && !isEditing) {
      setFormData(prev => ({ ...prev, slug: generateSlug(value) }));
    }
    
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  const validate = (): boolean => {
    const errors: Partial<Record<keyof FormData, string>> = {};

    if (!formData.name.trim()) {
      errors.name = 'Organization name is required';
    }

    if (!formData.slug.trim()) {
      errors.slug = 'Slug is required';
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      errors.slug = 'Slug can only contain lowercase letters, numbers, and hyphens';
    }

    if (!formData.contact_email.trim()) {
      errors.contact_email = 'Contact email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      errors.contact_email = 'Please enter a valid email address';
    }

    if (formData.website && !/^https?:\/\/.+/.test(formData.website)) {
      errors.website = 'Please enter a valid URL (starting with http:// or https://)';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) {
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      if (isEditing && id) {
        await updateOrganization(id, formData);
        navigate('/organization/settings');
      } else {
        await createOrganization(formData);
        navigate('/organizations');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to save organization');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && isEditing) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(-1)}
          sx={{ mb: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 0.5 }}>
          {isEditing ? 'Edit Organization' : 'Create Organization'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {isEditing 
            ? 'Update your organization details' 
            : 'Set up a new organization to manage your farms'}
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              {/* Basic Information */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="primary" />
                  <Typography variant="h6">Basic Information</Typography>
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Organization Name"
                  value={formData.name}
                  onChange={handleChange('name')}
                  error={Boolean(validationErrors.name)}
                  helperText={validationErrors.name}
                  placeholder="My Farm Organization"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Slug"
                  value={formData.slug}
                  onChange={handleChange('slug')}
                  error={Boolean(validationErrors.slug)}
                  helperText={validationErrors.slug || 'URL-friendly identifier (lowercase, no spaces)'}
                  placeholder="my-farm-org"
                  disabled={isEditing}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">/</InputAdornment>
                    ),
                  }}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Description"
                  value={formData.description}
                  onChange={handleChange('description')}
                  placeholder="Describe your organization..."
                />
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 1 }} />
              </Grid>

              {/* Contact Information */}
              <Grid item xs={12}>
                <Typography variant="h6" sx={{ mb: 1 }}>Contact Information</Typography>
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  required
                  label="Contact Email"
                  type="email"
                  value={formData.contact_email}
                  onChange={handleChange('contact_email')}
                  error={Boolean(validationErrors.contact_email)}
                  helperText={validationErrors.contact_email}
                  placeholder="contact@example.com"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <EmailIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Contact Phone"
                  value={formData.contact_phone}
                  onChange={handleChange('contact_phone')}
                  placeholder="+1 (555) 123-4567"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <PhoneIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Website"
                  value={formData.website}
                  onChange={handleChange('website')}
                  error={Boolean(validationErrors.website)}
                  helperText={validationErrors.website}
                  placeholder="https://www.example.com"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <WebsiteIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Address"
                  value={formData.address}
                  onChange={handleChange('address')}
                  placeholder="123 Farm Road, City, Country"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <LocationIcon color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>

              {/* Actions */}
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }} />
              </Grid>

              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                  <Button
                    variant="outlined"
                    onClick={() => navigate(-1)}
                    disabled={submitting}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={submitting ? <CircularProgress size={20} /> : <SaveIcon />}
                    disabled={submitting}
                  >
                    {submitting 
                      ? 'Saving...' 
                      : isEditing 
                        ? 'Update Organization' 
                        : 'Create Organization'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default OrganizationForm;

