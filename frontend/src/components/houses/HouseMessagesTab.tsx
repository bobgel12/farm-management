import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
} from '@mui/material';

interface HouseMessagesTabProps {
  houseId: string;
  house: any;
}

const HouseMessagesTab: React.FC<HouseMessagesTabProps> = ({ houseId, house }) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Messages
      </Typography>
      <Card>
        <CardContent>
          <Typography variant="body1" color="text.secondary" align="center">
            Message system will be implemented in a future phase.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default HouseMessagesTab;

