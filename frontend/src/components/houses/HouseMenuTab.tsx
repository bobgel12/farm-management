import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  ExpandMore,
  Settings as ControlIcon,
  ManageAccounts as ManagementIcon,
  History as HistoryIcon,
  Build as SystemIcon,
} from '@mui/icons-material';

interface HouseMenuTabProps {
  houseId: string;
  house: any;
}

const HouseMenuTab: React.FC<HouseMenuTabProps> = ({ houseId, house }) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        House Menu
      </Typography>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <ListItemIcon>
            <ControlIcon />
          </ListItemIcon>
          <Typography variant="h6">Control</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText primary="Temperature Curve" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Min/Max Levels" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Humidity Treatment" />
            </ListItem>
            <ListItem>
              <ListItemText primary="CO2 Treatment" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Natural Ventilation" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Static Pressure" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Cool Pad" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Foggers" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Water & Feed" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Light" />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <ListItemIcon>
            <ManagementIcon />
          </ListItemIcon>
          <Typography variant="h6">Management</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText primary="Bird Inventory" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Feed Inventory" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Growth Day & Flock" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Alarm Settings" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Alarm Reset" />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <ListItemIcon>
            <HistoryIcon />
          </ListItemIcon>
          <Typography variant="h6">History</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText primary="Temperature" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Humidity" />
            </ListItem>
            <ListItem>
              <ListItemText primary="CO2" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Bird Weight" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Feed Conversion" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Water" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Feed" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Mortality" />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <ListItemIcon>
            <SystemIcon />
          </ListItemIcon>
          <Typography variant="h6">System</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <List>
            <ListItem>
              <ListItemText primary="Setup" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Time & Date" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Sensors" />
            </ListItem>
            <ListItem>
              <ListItemText primary="House Dimensions" />
            </ListItem>
            <ListItem>
              <ListItemText primary="Fan Air Capacity" />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default HouseMenuTab;

