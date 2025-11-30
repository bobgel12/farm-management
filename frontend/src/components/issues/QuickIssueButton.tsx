import React, { useState } from 'react';
import {
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Zoom,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Report as ReportIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { IssueReportForm } from './IssueReportForm';

interface QuickIssueButtonProps {
  houseId: number;
  houseName?: string;
  onIssueCreated?: () => void;
}

export const QuickIssueButton: React.FC<QuickIssueButtonProps> = ({
  houseId,
  houseName,
  onIssueCreated,
}) => {
  const [dialogOpen, setDialogOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleSuccess = () => {
    setDialogOpen(false);
    onIssueCreated?.();
  };

  return (
    <>
      <Zoom in={true}>
        <Fab
          color="warning"
          aria-label="Report Issue"
          onClick={() => setDialogOpen(true)}
          sx={{
            position: 'fixed',
            bottom: isMobile ? 70 : 24,
            right: 24,
            zIndex: 1000,
          }}
        >
          <ReportIcon />
        </Fab>
      </Zoom>

      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          Report Issue
          <IconButton onClick={() => setDialogOpen(false)}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <IssueReportForm
            houseId={houseId}
            houseName={houseName}
            onSuccess={handleSuccess}
            onCancel={() => setDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </>
  );
};

export default QuickIssueButton;

