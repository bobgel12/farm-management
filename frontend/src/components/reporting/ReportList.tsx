import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  InputAdornment,
  Menu,
  MenuItem,
  LinearProgress,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  MoreVert as MoreVertIcon,
  Search as SearchIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  GetApp as DownloadIcon,
  Schedule as ScheduleIcon,
  Description as ReportIcon,
} from '@mui/icons-material';
import { useReporting } from '../../contexts/ReportingContext';
import { ReportTemplate, ScheduledReport } from '../../types';
import dayjs from 'dayjs';

const ReportList: React.FC = () => {
  const navigate = useNavigate();
  const {
    templates,
    scheduledReports,
    loading,
    error,
    fetchTemplates,
    fetchScheduledReports,
    deleteTemplate,
    deleteScheduledReport,
  } = useReporting();

  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'templates' | 'scheduled'>('all');
  const [menuAnchor, setMenuAnchor] = useState<{ el: HTMLElement; type: 'template' | 'scheduled'; id: number } | null>(null);

  useEffect(() => {
    fetchTemplates();
    fetchScheduledReports();
  }, [fetchTemplates, fetchScheduledReports]);

  const filteredTemplates = templates.filter((template) =>
    template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    template.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredScheduled = scheduledReports.filter((report) =>
    report.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, type: 'template' | 'scheduled', id: number) => {
    setMenuAnchor({ el: event.currentTarget, type, id });
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
  };

  const handleView = (id: number, type: 'template' | 'scheduled') => {
    handleMenuClose();
    if (type === 'template') {
      navigate(`/reports/templates/${id}`);
    } else {
      navigate(`/reports/scheduled/${id}`);
    }
  };

  const handleEdit = (id: number, type: 'template' | 'scheduled') => {
    handleMenuClose();
    if (type === 'template') {
      navigate(`/reports/templates/${id}/edit`);
    } else {
      navigate(`/reports/scheduled/${id}/edit`);
    }
  };

  const handleDelete = async (id: number, type: 'template' | 'scheduled') => {
    handleMenuClose();
    if (window.confirm(`Are you sure you want to delete this ${type === 'template' ? 'template' : 'scheduled report'}?`)) {
      try {
        if (type === 'template') {
          await deleteTemplate(id);
        } else {
          await deleteScheduledReport(id);
        }
      } catch (err) {
        console.error('Error deleting:', err);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'running':
        return 'info';
      case 'completed':
        return 'default';
      case 'failed':
        return 'error';
      case 'paused':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Reports
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<ScheduleIcon />}
            onClick={() => navigate('/reports/scheduled/new')}
          >
            Schedule Report
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/reports/templates/new')}
          >
            New Template
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search reports..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Chip
                  label="All"
                  onClick={() => setFilterType('all')}
                  color={filterType === 'all' ? 'primary' : 'default'}
                  variant={filterType === 'all' ? 'filled' : 'outlined'}
                />
                <Chip
                  label={`Templates (${templates.length})`}
                  onClick={() => setFilterType('templates')}
                  color={filterType === 'templates' ? 'primary' : 'default'}
                  variant={filterType === 'templates' ? 'filled' : 'outlined'}
                />
                <Chip
                  label={`Scheduled (${scheduledReports.length})`}
                  onClick={() => setFilterType('scheduled')}
                  color={filterType === 'scheduled' ? 'primary' : 'default'}
                  variant={filterType === 'scheduled' ? 'filled' : 'outlined'}
                />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {loading ? (
        <LinearProgress />
      ) : (
        <>
          {/* Templates Table */}
          {(filterType === 'all' || filterType === 'templates') && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ReportIcon />
                  <Typography variant="h6">Report Templates</Typography>
                </Box>
                {filteredTemplates.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="text.secondary" gutterBottom>
                      No report templates found
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<AddIcon />}
                      onClick={() => navigate('/reports/templates/new')}
                      sx={{ mt: 2 }}
                    >
                      Create Template
                    </Button>
                  </Box>
                ) : (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Name</TableCell>
                          <TableCell>Description</TableCell>
                          <TableCell>Type</TableCell>
                          <TableCell>Format</TableCell>
                          <TableCell>Created</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {filteredTemplates.map((template) => (
                          <TableRow key={template.id} hover>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                {template.name}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" color="text.secondary" noWrap sx={{ maxWidth: 300 }}>
                                {template.description || '-'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip label={template.report_type} size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>
                              <Chip label={template.default_format} size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" color="text.secondary">
                                {dayjs(template.created_at).format('MMM DD, YYYY')}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={template.is_active ? 'Active' : 'Inactive'}
                                size="small"
                                color={template.is_active ? 'success' : 'default'}
                              />
                            </TableCell>
                            <TableCell align="right">
                              <IconButton
                                size="small"
                                onClick={(e) => handleMenuOpen(e, 'template', template.id)}
                              >
                                <MoreVertIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          )}

          {/* Scheduled Reports Table */}
          {(filterType === 'all' || filterType === 'scheduled') && (
            <Card>
              <CardContent>
                <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ScheduleIcon />
                  <Typography variant="h6">Scheduled Reports</Typography>
                </Box>
                {filteredScheduled.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography color="text.secondary" gutterBottom>
                      No scheduled reports found
                    </Typography>
                    <Button
                      variant="outlined"
                      startIcon={<ScheduleIcon />}
                      onClick={() => navigate('/reports/scheduled/new')}
                      sx={{ mt: 2 }}
                    >
                      Schedule Report
                    </Button>
                  </Box>
                ) : (
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Name</TableCell>
                          <TableCell>Template</TableCell>
                          <TableCell>Schedule</TableCell>
                          <TableCell>Next Run</TableCell>
                          <TableCell>Last Run</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell align="right">Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {filteredScheduled.map((report) => (
                          <TableRow key={report.id} hover>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                {report.name}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" color="text.secondary">
                                {`Template #${report.template || report.template_id || '-'}`}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip label={report.frequency} size="small" variant="outlined" />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" color="text.secondary">
                                {report.next_run_at
                                  ? dayjs(report.next_run_at).format('MMM DD, YYYY HH:mm')
                                  : '-'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" color="text.secondary">
                                {report.last_run_at
                                  ? dayjs(report.last_run_at).format('MMM DD, YYYY HH:mm')
                                  : '-'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Chip
                                label={report.status}
                                size="small"
                                color={getStatusColor(report.status) as any}
                              />
                            </TableCell>
                            <TableCell align="right">
                              <IconButton
                                size="small"
                                onClick={(e) => handleMenuOpen(e, 'scheduled', report.id)}
                              >
                                <MoreVertIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={menuAnchor?.el}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => menuAnchor && handleView(menuAnchor.id, menuAnchor.type)}>
          <ViewIcon sx={{ mr: 1 }} fontSize="small" />
          View
        </MenuItem>
        <MenuItem onClick={() => menuAnchor && handleEdit(menuAnchor.id, menuAnchor.type)}>
          <EditIcon sx={{ mr: 1 }} fontSize="small" />
          Edit
        </MenuItem>
        <MenuItem
          onClick={() => menuAnchor && handleDelete(menuAnchor.id, menuAnchor.type)}
          sx={{ color: 'error.main' }}
        >
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default ReportList;

