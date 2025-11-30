import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  IconButton,
  CircularProgress,
  Alert,
  Divider,
  Grid,
  ImageList,
  ImageListItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  CheckCircle as ResolveIcon,
  Refresh as ReopenIcon,
  Assignment as TaskIcon,
  Send as SendIcon,
  Close as CloseIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { Issue, IssueComment, IssuePriority, IssueStatus } from '../../types';
import { issuesApi } from '../../services/issuesApi';

interface IssueDetailProps {
  issueId: number;
  onBack?: () => void;
  onTaskCreated?: (taskId: number) => void;
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

const CATEGORY_ICONS: Record<string, string> = {
  equipment: '🔧',
  health: '🐔',
  environment: '🌡️',
  maintenance: '🔨',
  other: '📝',
};

export const IssueDetail: React.FC<IssueDetailProps> = ({
  issueId,
  onBack,
  onTaskCreated,
}) => {
  const [issue, setIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null);

  // Dialogs
  const [resolveDialogOpen, setResolveDialogOpen] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [createTaskDialogOpen, setCreateTaskDialogOpen] = useState(false);

  // Comment
  const [newComment, setNewComment] = useState('');
  const [submittingComment, setSubmittingComment] = useState(false);

  useEffect(() => {
    loadIssue();
  }, [issueId]);

  const loadIssue = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await issuesApi.getIssue(issueId);
      setIssue(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load issue');
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!issue) return;

    try {
      const updated = await issuesApi.resolveIssue(issue.id, resolutionNotes);
      setIssue(updated);
      setResolveDialogOpen(false);
      setResolutionNotes('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resolve issue');
    }
  };

  const handleReopen = async () => {
    if (!issue) return;

    try {
      const updated = await issuesApi.reopenIssue(issue.id);
      setIssue(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reopen issue');
    }
  };

  const handleCreateTask = async () => {
    if (!issue) return;

    try {
      const result = await issuesApi.createTask(issue.id, {});
      setCreateTaskDialogOpen(false);
      onTaskCreated?.(result.task_id);
      loadIssue(); // Refresh to get updated task reference
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create task');
    }
  };

  const handleAddComment = async () => {
    if (!issue || !newComment.trim()) return;

    setSubmittingComment(true);
    try {
      await issuesApi.addComment(issue.id, newComment);
      setNewComment('');
      loadIssue(); // Refresh to get new comment
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add comment');
    } finally {
      setSubmittingComment(false);
    }
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

  if (!issue) {
    return (
      <Alert severity="info">Issue not found</Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 2 }}>
        {onBack && (
          <IconButton onClick={onBack}>
            <BackIcon />
          </IconButton>
        )}
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {CATEGORY_ICONS[issue.category]} {issue.title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            House {issue.house_number} • {issue.farm_name} • {issue.age_display}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            label={issue.priority}
            color={PRIORITY_COLORS[issue.priority]}
          />
          <Chip
            label={issue.status.replace('_', ' ')}
            color={STATUS_COLORS[issue.status]}
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Actions */}
      <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
        {issue.is_open && (
          <Button
            variant="contained"
            color="success"
            startIcon={<ResolveIcon />}
            onClick={() => setResolveDialogOpen(true)}
          >
            Resolve
          </Button>
        )}
        {(issue.status === 'resolved' || issue.status === 'closed') && (
          <Button
            variant="outlined"
            startIcon={<ReopenIcon />}
            onClick={handleReopen}
          >
            Reopen
          </Button>
        )}
        {!issue.created_task && issue.is_open && (
          <Button
            variant="outlined"
            startIcon={<TaskIcon />}
            onClick={() => setCreateTaskDialogOpen(true)}
          >
            Create Task
          </Button>
        )}
        {issue.created_task && (
          <Chip
            icon={<TaskIcon />}
            label={`Task #${issue.created_task}`}
            color="info"
            variant="outlined"
          />
        )}
      </Box>

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Description</Typography>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {issue.description}
              </Typography>

              {issue.location_in_house && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Location
                  </Typography>
                  <Typography>{issue.location_in_house}</Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Photos */}
          {issue.photos.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📷 Photos ({issue.photos.length})
                </Typography>
                <ImageList cols={3} rowHeight={150}>
                  {issue.photos.map((photo) => (
                    <ImageListItem
                      key={photo.id}
                      sx={{ cursor: 'pointer' }}
                      onClick={() => setSelectedPhoto(photo.cloudinary_url)}
                    >
                      <img
                        src={photo.cloudinary_url}
                        alt={photo.caption || 'Issue photo'}
                        loading="lazy"
                        style={{ objectFit: 'cover', height: '150px' }}
                      />
                    </ImageListItem>
                  ))}
                </ImageList>
              </CardContent>
            </Card>
          )}

          {/* Comments */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💬 Comments ({issue.comments.length})
              </Typography>

              {issue.comments.length > 0 && (
                <List>
                  {issue.comments.map((comment) => (
                    <ListItem key={comment.id} alignItems="flex-start">
                      <ListItemAvatar>
                        <Avatar>
                          <PersonIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={comment.user?.full_name || comment.user?.username || 'Unknown'}
                        secondary={
                          <>
                            <Typography
                              component="span"
                              variant="body2"
                              sx={{ display: 'block', mt: 0.5 }}
                            >
                              {comment.content}
                            </Typography>
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              {new Date(comment.created_at).toLocaleString()}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}

              <Divider sx={{ my: 2 }} />

              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Add a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleAddComment();
                    }
                  }}
                />
                <IconButton
                  color="primary"
                  onClick={handleAddComment}
                  disabled={submittingComment || !newComment.trim()}
                >
                  {submittingComment ? <CircularProgress size={24} /> : <SendIcon />}
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Details</Typography>

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Reported By
                </Typography>
                <Typography>
                  {issue.reported_by?.full_name || issue.reported_by?.username || 'Unknown'}
                </Typography>
              </Box>

              {issue.assigned_to && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Assigned To
                  </Typography>
                  <Typography>
                    {issue.assigned_to.full_name || issue.assigned_to.username}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Created
                </Typography>
                <Typography>
                  {new Date(issue.created_at).toLocaleString()}
                </Typography>
              </Box>

              {issue.resolved_at && (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Resolved
                    </Typography>
                    <Typography>
                      {new Date(issue.resolved_at).toLocaleString()}
                    </Typography>
                  </Box>

                  {issue.resolved_by && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Resolved By
                      </Typography>
                      <Typography>
                        {issue.resolved_by.full_name || issue.resolved_by.username}
                      </Typography>
                    </Box>
                  )}

                  {issue.resolution_notes && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Resolution Notes
                      </Typography>
                      <Typography sx={{ whiteSpace: 'pre-wrap' }}>
                        {issue.resolution_notes}
                      </Typography>
                    </Box>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Photo Preview Dialog */}
      <Dialog
        open={!!selectedPhoto}
        onClose={() => setSelectedPhoto(null)}
        maxWidth="lg"
      >
        <DialogContent sx={{ p: 0, position: 'relative' }}>
          <IconButton
            onClick={() => setSelectedPhoto(null)}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              bgcolor: 'rgba(0,0,0,0.5)',
              color: 'white',
            }}
          >
            <CloseIcon />
          </IconButton>
          {selectedPhoto && (
            <img
              src={selectedPhoto}
              alt="Issue photo"
              style={{ maxWidth: '100%', display: 'block' }}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Resolve Dialog */}
      <Dialog
        open={resolveDialogOpen}
        onClose={() => setResolveDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Resolve Issue</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Resolution Notes (optional)"
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
            placeholder="Describe how the issue was resolved..."
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResolveDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="success"
            onClick={handleResolve}
          >
            Mark as Resolved
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Task Dialog */}
      <Dialog
        open={createTaskDialogOpen}
        onClose={() => setCreateTaskDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create Task from Issue</DialogTitle>
        <DialogContent>
          <Typography>
            Create a task to address this issue? The task will be linked to this issue.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateTaskDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateTask}
            startIcon={<TaskIcon />}
          >
            Create Task
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default IssueDetail;

