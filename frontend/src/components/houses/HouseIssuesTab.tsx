import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Close as CloseIcon,
  ArrowBack as BackIcon,
} from '@mui/icons-material';
import { IssueList, IssueDetail, IssueReportForm } from '../issues';
import { IssueListItem } from '../../types';

interface HouseIssuesTabProps {
  houseId: number;
  house: any;
}

const HouseIssuesTab: React.FC<HouseIssuesTabProps> = ({ houseId, house }) => {
  const [showReportForm, setShowReportForm] = useState(false);
  const [selectedIssueId, setSelectedIssueId] = useState<number | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleIssueSelect = (issue: IssueListItem) => {
    setSelectedIssueId(issue.id);
  };

  const handleReportSuccess = () => {
    setShowReportForm(false);
    setRefreshKey(prev => prev + 1);
  };

  const handleBack = () => {
    setSelectedIssueId(null);
    setRefreshKey(prev => prev + 1);
  };

  // Show issue detail if one is selected
  if (selectedIssueId) {
    return (
      <IssueDetail
        issueId={selectedIssueId}
        onBack={handleBack}
      />
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h6">Issue Tracking</Typography>
          <Typography variant="body2" color="text.secondary">
            Report and manage issues for House {house.house_number}
          </Typography>
        </Box>
        
        <Button
          variant="contained"
          color="warning"
          startIcon={<AddIcon />}
          onClick={() => setShowReportForm(true)}
        >
          Report Issue
        </Button>
      </Box>

      {/* Issue List */}
      <IssueList
        houseId={houseId}
        onSelectIssue={handleIssueSelect}
        refresh={refreshKey}
      />

      {/* Report Form Dialog */}
      <Dialog
        open={showReportForm}
        onClose={() => setShowReportForm(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Report New Issue
          <IconButton onClick={() => setShowReportForm(false)}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <IssueReportForm
            houseId={houseId}
            houseName={`House ${house.house_number}`}
            onSuccess={handleReportSuccess}
            onCancel={() => setShowReportForm(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default HouseIssuesTab;

