import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Alert,
  AlertTitle,
  Button,
  CircularProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  Warning,
  Error,
  Refresh,
  Science,
  Assessment,
  Lightbulb,
  BugReport
} from '@mui/icons-material';
import { rotemApi } from '../../services/rotemApi';
import { MLPrediction, MLSummary, AnomalyData, FailureData, OptimizationData, PerformanceData } from '../../types/rotem';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ml-tabpanel-${index}`}
      aria-labelledby={`ml-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const MLDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [mlSummary, setMLSummary] = useState<MLSummary | null>(null);
  const [anomalies, setAnomalies] = useState<MLPrediction[]>([]);
  const [failures, setFailures] = useState<MLPrediction[]>([]);
  const [optimizations, setOptimizations] = useState<MLPrediction[]>([]);
  const [performance, setPerformance] = useState<MLPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadMLData = async () => {
    try {
      setLoading(true);
      const [summary, anomaliesData, failuresData, optimizationsData, performanceData] = await Promise.all([
        rotemApi.getMLSummary(),
        rotemApi.getAnomalies(),
        rotemApi.getFailures(),
        rotemApi.getOptimizations(),
        rotemApi.getPerformance()
      ]);

      setMLSummary(summary);
      setAnomalies(anomaliesData);
      setFailures(failuresData);
      setOptimizations(optimizationsData);
      setPerformance(performanceData);
    } catch (error) {
      // Error loading ML data
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadMLData();
    setRefreshing(false);
  };

  const runMLAnalysis = async () => {
    try {
      setRefreshing(true);
      await rotemApi.runMLAnalysis();
      // Wait a bit for analysis to complete, then refresh
      setTimeout(() => {
        loadMLData();
      }, 5000);
    } catch (error) {
      // Error running ML analysis
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadMLData();
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'primary';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          ML Insights Dashboard
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={refreshing}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Science />}
            onClick={runMLAnalysis}
            disabled={refreshing}
          >
            Run Analysis
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      {mlSummary && (
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <BugReport color="error" sx={{ mr: 1 }} />
                  <Typography variant="h6">Anomalies</Typography>
                </Box>
                <Typography variant="h4" color="error">
                  {mlSummary.last_24h.anomalies}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 24 hours
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <Error color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">Failures</Typography>
                </Box>
                <Typography variant="h4" color="warning.main">
                  {mlSummary.last_7d.failures}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 7 days
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <Lightbulb color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Optimizations</Typography>
                </Box>
                <Typography variant="h4" color="info.main">
                  {mlSummary.last_24h.optimizations}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 24 hours
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <Assessment color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Performance</Typography>
                </Box>
                <Typography variant="h4" color="success.main">
                  {mlSummary.last_24h.performance}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 24 hours
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="Anomalies" icon={<BugReport />} iconPosition="start" />
            <Tab label="Failures" icon={<Error />} iconPosition="start" />
            <Tab label="Optimizations" icon={<Lightbulb />} iconPosition="start" />
            <Tab label="Performance" icon={<Assessment />} iconPosition="start" />
          </Tabs>
        </Box>

        {/* Anomalies Tab */}
        <TabPanel value={activeTab} index={0}>
          <Typography variant="h6" gutterBottom>
            Anomaly Detection ({anomalies.length} detected)
          </Typography>
          {anomalies.length === 0 ? (
            <Alert severity="success">
              <AlertTitle>No Anomalies Detected</AlertTitle>
              All sensor readings are within normal ranges.
            </Alert>
          ) : (
            <List>
              {anomalies.map((anomaly, index) => {
                const data = anomaly.prediction_data as AnomalyData;
                return (
                  <React.Fragment key={anomaly.id}>
                    <ListItem>
                      <ListItemIcon>
                        <Warning color={getSeverityColor(data.severity)} />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle1">
                              {data.data_type} - {data.value} {data.unit}
                            </Typography>
                            <Chip
                              label={data.severity.toUpperCase()}
                              color={getSeverityColor(data.severity)}
                              size="small"
                            />
                            <Chip
                              label={`${((anomaly.confidence_score || 0) * 100).toFixed(1)}%`}
                              color={getConfidenceColor(anomaly.confidence_score || 0)}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Controller: {anomaly.controller_name} | Farm: {anomaly.farm_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Detected: {formatTimestamp(anomaly.predicted_at)}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Anomaly Score: {(data.anomaly_score || 0).toFixed(3)}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < anomalies.length - 1 && <Divider />}
                  </React.Fragment>
                );
              })}
            </List>
          )}
        </TabPanel>

        {/* Failures Tab */}
        <TabPanel value={activeTab} index={1}>
          <Typography variant="h6" gutterBottom>
            Equipment Failure Predictions ({failures.length} predicted)
          </Typography>
          {failures.length === 0 ? (
            <Alert severity="success">
              <AlertTitle>No Failure Predictions</AlertTitle>
              All equipment is operating normally.
            </Alert>
          ) : (
            <List>
              {failures.map((failure, index) => {
                const data = failure.prediction_data as FailureData;
                return (
                  <React.Fragment key={failure.id}>
                    <ListItem>
                      <ListItemIcon>
                        <Error color="error" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle1">
                              Failure Risk: {((data.failure_probability || 0) * 100).toFixed(1)}%
                            </Typography>
                            <Chip
                              label={`${((failure.confidence_score || 0) * 100).toFixed(1)}%`}
                              color={getConfidenceColor(failure.confidence_score || 0)}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Controller: {failure.controller_name} | Farm: {failure.farm_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Predicted: {formatTimestamp(failure.predicted_at)}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Expected Failure: {formatTimestamp(data.predicted_failure_time)}
                            </Typography>
                            <Box mt={1}>
                              <Typography variant="body2" fontWeight="bold">
                                Recommended Actions:
                              </Typography>
                              {data.recommended_actions.map((action, idx) => (
                                <Typography key={idx} variant="body2" color="text.secondary">
                                  • {action}
                                </Typography>
                              ))}
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < failures.length - 1 && <Divider />}
                  </React.Fragment>
                );
              })}
            </List>
          )}
        </TabPanel>

        {/* Optimizations Tab */}
        <TabPanel value={activeTab} index={2}>
          <Typography variant="h6" gutterBottom>
            Environmental Optimizations ({optimizations.length} suggestions)
          </Typography>
          {optimizations.length === 0 ? (
            <Alert severity="info">
              <AlertTitle>No Optimization Suggestions</AlertTitle>
              Current environmental conditions are optimal.
            </Alert>
          ) : (
            <List>
              {optimizations.map((optimization, index) => {
                const data = optimization.prediction_data as OptimizationData;
                return (
                  <React.Fragment key={optimization.id}>
                    <ListItem>
                      <ListItemIcon>
                        <Lightbulb color={data.priority === 'high' ? 'warning' : 'info'} />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle1">
                              {data.type.charAt(0).toUpperCase() + data.type.slice(1)} Optimization
                            </Typography>
                            <Chip
                              label={data.priority.toUpperCase()}
                              color={data.priority === 'high' ? 'error' : data.priority === 'medium' ? 'warning' : 'info'}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Current: {(data.current || 0).toFixed(1)} | Optimal: {(data.optimal_range?.[0] || 0)}-{(data.optimal_range?.[1] || 0)}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Suggested: {formatTimestamp(optimization.predicted_at)}
                            </Typography>
                            <Typography variant="body2" fontWeight="bold" sx={{ mt: 1 }}>
                              Action: {data.action}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < optimizations.length - 1 && <Divider />}
                  </React.Fragment>
                );
              })}
            </List>
          )}
        </TabPanel>

        {/* Performance Tab */}
        <TabPanel value={activeTab} index={3}>
          <Typography variant="h6" gutterBottom>
            System Performance Analysis
          </Typography>
          {performance.length === 0 ? (
            <Alert severity="info">
              <AlertTitle>No Performance Data</AlertTitle>
              Performance analysis is not available yet.
            </Alert>
          ) : (
            <List>
              {performance.map((perf, index) => {
                const data = perf.prediction_data as PerformanceData;
                return (
                  <React.Fragment key={perf.id}>
                    <ListItem>
                      <ListItemIcon>
                        <Assessment color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle1">
                              System Efficiency: {((data.efficiency_score || 0) * 100).toFixed(1)}%
                            </Typography>
                            <Chip
                              label={`${((perf.confidence_score || 0) * 100).toFixed(1)}%`}
                              color={getConfidenceColor(perf.confidence_score || 0)}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              Controller: {perf.controller_name} | Farm: {perf.farm_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Analyzed: {formatTimestamp(perf.predicted_at)}
                            </Typography>
                            <Box mt={1}>
                              <Typography variant="body2" fontWeight="bold">
                                Performance Metrics:
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                • Data Completeness: {((data.data_completeness || 0) * 100).toFixed(1)}%
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                • Good Quality Points: {data.good_quality_points || 0}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                • Warning Points: {data.warning_quality_points || 0}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                • Error Points: {data.error_quality_points || 0}
                              </Typography>
                            </Box>
                            {data.recommendations && data.recommendations.length > 0 && (
                              <Box mt={1}>
                                <Typography variant="body2" fontWeight="bold">
                                  Recommendations:
                                </Typography>
                                {data.recommendations.map((rec, idx) => (
                                  <Typography key={idx} variant="body2" color="text.secondary">
                                    • {rec}
                                  </Typography>
                                ))}
                              </Box>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < performance.length - 1 && <Divider />}
                  </React.Fragment>
                );
              })}
            </List>
          )}
        </TabPanel>
      </Card>
    </Box>
  );
};

export default MLDashboard;
