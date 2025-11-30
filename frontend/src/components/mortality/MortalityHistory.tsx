import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Chip,
  CircularProgress,
  Alert,
  TablePagination,
  Collapse,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { MortalityRecord } from '../../types';
import { mortalityApi, MortalityFilters } from '../../services/mortalityApi';

interface MortalityHistoryProps {
  flockId?: number;
  houseId?: number;
  farmId?: number;
  showActions?: boolean;
  onEdit?: (record: MortalityRecord) => void;
  onDelete?: (id: number) => void;
  refresh?: number; // Increment to trigger refresh
}

export const MortalityHistory: React.FC<MortalityHistoryProps> = ({
  flockId,
  houseId,
  farmId,
  showActions = true,
  onEdit,
  onDelete,
  refresh = 0,
}) => {
  const [records, setRecords] = useState<MortalityRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadRecords();
  }, [flockId, houseId, farmId, refresh]);

  const loadRecords = async () => {
    setLoading(true);
    setError(null);

    try {
      const filters: MortalityFilters = {};
      if (flockId) filters.flock_id = flockId;
      if (houseId) filters.house_id = houseId;
      if (farmId) filters.farm_id = farmId;

      const data = await mortalityApi.getRecords(filters);
      // Ensure data is an array
      setRecords(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load mortality records');
      setRecords([]); // Set empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this record?')) return;

    try {
      await mortalityApi.deleteRecord(id);
      setRecords(prev => prev.filter(r => r.id !== id));
      onDelete?.(id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete record');
    }
  };

  const toggleRowExpand = (id: number) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

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

  if (records.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography color="text.secondary" align="center">
            No mortality records found
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const paginatedRecords = records.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          📋 Mortality History
        </Typography>

        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width={40}></TableCell>
                <TableCell>Date</TableCell>
                <TableCell align="right">Deaths</TableCell>
                <TableCell>House</TableCell>
                <TableCell>Recorded By</TableCell>
                <TableCell>Notes</TableCell>
                {showActions && <TableCell width={100}>Actions</TableCell>}
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedRecords.map((record) => (
                <React.Fragment key={record.id}>
                  <TableRow hover>
                    <TableCell>
                      {record.has_detailed_breakdown && (
                        <IconButton
                          size="small"
                          onClick={() => toggleRowExpand(record.id)}
                        >
                          {expandedRows.has(record.id) ? (
                            <ExpandLessIcon fontSize="small" />
                          ) : (
                            <ExpandMoreIcon fontSize="small" />
                          )}
                        </IconButton>
                      )}
                    </TableCell>
                    <TableCell>{formatDate(record.record_date)}</TableCell>
                    <TableCell align="right">
                      <Chip
                        label={record.total_deaths}
                        color="error"
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>House {record.house_number}</TableCell>
                    <TableCell>{record.recorded_by_name || 'N/A'}</TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          maxWidth: 200,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {record.notes || '-'}
                      </Typography>
                    </TableCell>
                    {showActions && (
                      <TableCell>
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => onEdit?.(record)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDelete(record.id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    )}
                  </TableRow>

                  {/* Expanded breakdown row */}
                  {record.has_detailed_breakdown && (
                    <TableRow>
                      <TableCell colSpan={showActions ? 7 : 6} sx={{ py: 0 }}>
                        <Collapse in={expandedRows.has(record.id)}>
                          <Box sx={{ py: 2, px: 4, bgcolor: 'grey.50' }}>
                            <Typography variant="subtitle2" gutterBottom>
                              Breakdown by Cause:
                            </Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                              {record.disease_deaths > 0 && (
                                <Chip
                                  label={`Disease: ${record.disease_deaths}`}
                                  size="small"
                                  color="warning"
                                />
                              )}
                              {record.culling_deaths > 0 && (
                                <Chip
                                  label={`Culling: ${record.culling_deaths}`}
                                  size="small"
                                  color="info"
                                />
                              )}
                              {record.accident_deaths > 0 && (
                                <Chip
                                  label={`Accident: ${record.accident_deaths}`}
                                  size="small"
                                  color="secondary"
                                />
                              )}
                              {record.heat_stress_deaths > 0 && (
                                <Chip
                                  label={`Heat Stress: ${record.heat_stress_deaths}`}
                                  size="small"
                                  sx={{ bgcolor: '#ff7043', color: 'white' }}
                                />
                              )}
                              {record.cold_stress_deaths > 0 && (
                                <Chip
                                  label={`Cold Stress: ${record.cold_stress_deaths}`}
                                  size="small"
                                  sx={{ bgcolor: '#42a5f5', color: 'white' }}
                                />
                              )}
                              {record.unknown_deaths > 0 && (
                                <Chip
                                  label={`Unknown: ${record.unknown_deaths}`}
                                  size="small"
                                />
                              )}
                              {record.other_deaths > 0 && (
                                <Chip
                                  label={`Other: ${record.other_deaths}`}
                                  size="small"
                                />
                              )}
                            </Box>
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  )}
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={records.length}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </CardContent>
    </Card>
  );
};

export default MortalityHistory;

