import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Save as SaveIcon,
  Report as ReportIcon,
} from '@mui/icons-material';
import { IssueCreate, IssueCategory, IssuePriority } from '../../types';
import { issuesApi } from '../../services/issuesApi';
import { PhotoCapture } from './PhotoCapture';

interface IssueReportFormProps {
  houseId: number;
  houseName?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const CATEGORIES: { value: IssueCategory; label: string; icon: string }[] = [
  { value: 'equipment', label: 'Equipment', icon: '🔧' },
  { value: 'health', label: 'Bird Health', icon: '🐔' },
  { value: 'environment', label: 'Environmental', icon: '🌡️' },
  { value: 'maintenance', label: 'Maintenance', icon: '🔨' },
  { value: 'other', label: 'Other', icon: '📝' },
];

const PRIORITIES: { value: IssuePriority; label: string; color: string }[] = [
  { value: 'low', label: 'Low', color: '#4caf50' },
  { value: 'medium', label: 'Medium', color: '#ff9800' },
  { value: 'high', label: 'High', color: '#f44336' },
  { value: 'critical', label: 'Critical', color: '#9c27b0' },
];

interface PhotoData {
  id: string;
  preview: string;
  base64: string;
  caption: string;
}

export const IssueReportForm: React.FC<IssueReportFormProps> = ({
  houseId,
  houseName,
  onSuccess,
  onCancel,
}) => {
  const [formData, setFormData] = useState<Omit<IssueCreate, 'house'>>({
    title: '',
    description: '',
    category: 'equipment',
    priority: 'medium',
    location_in_house: '',
  });

  const [photos, setPhotos] = useState<PhotoData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (field: keyof typeof formData) => (
    e: React.ChangeEvent<HTMLInputElement | { value: unknown }> | any
  ) => {
    setFormData(prev => ({
      ...prev,
      [field]: e.target.value,
    }));
    setError(null);
    setSuccess(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim()) {
      setError('Please enter a title for the issue');
      return;
    }

    if (!formData.description.trim()) {
      setError('Please describe the issue');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const issueData: IssueCreate = {
        house: houseId,
        ...formData,
        photos: photos.map(p => ({
          image: p.base64,
          caption: p.caption,
        })),
      };

      await issuesApi.createIssue(issueData);
      setSuccess(true);

      // Reset form
      setFormData({
        title: '',
        description: '',
        category: 'equipment',
        priority: 'medium',
        location_in_house: '',
      });
      setPhotos([]);

      onSuccess?.();
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Failed to submit issue report'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card elevation={2}>
      <CardContent>
        <Typography
          variant="h6"
          gutterBottom
          sx={{ display: 'flex', alignItems: 'center', gap: 1 }}
        >
          <ReportIcon color="warning" />
          Report Issue
          {houseName && (
            <Typography variant="body2" color="text.secondary">
              - {houseName}
            </Typography>
          )}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(false)}>
            Issue reported successfully!
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Issue Title"
                value={formData.title}
                onChange={handleChange('title')}
                required
                placeholder="Brief description of the issue..."
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  onChange={handleChange('category')}
                  label="Category"
                >
                  {CATEGORIES.map((cat) => (
                    <MenuItem key={cat.value} value={cat.value}>
                      {cat.icon} {cat.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={formData.priority}
                  onChange={handleChange('priority')}
                  label="Priority"
                >
                  {PRIORITIES.map((pri) => (
                    <MenuItem key={pri.value} value={pri.value}>
                      <Box
                        component="span"
                        sx={{
                          display: 'inline-block',
                          width: 12,
                          height: 12,
                          borderRadius: '50%',
                          bgcolor: pri.color,
                          mr: 1,
                        }}
                      />
                      {pri.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Location in House"
                value={formData.location_in_house}
                onChange={handleChange('location_in_house')}
                placeholder="e.g., Near feeder line 3, South wall..."
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Description"
                value={formData.description}
                onChange={handleChange('description')}
                required
                placeholder="Describe the issue in detail..."
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          <Typography variant="subtitle2" gutterBottom>
            📷 Photos (optional)
          </Typography>
          <PhotoCapture photos={photos} onChange={setPhotos} maxPhotos={5} />

          <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            {onCancel && (
              <Button onClick={onCancel} disabled={loading}>
                Cancel
              </Button>
            )}
            <Button
              type="submit"
              variant="contained"
              color="warning"
              startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
              disabled={loading}
            >
              Submit Report
            </Button>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default IssueReportForm;

