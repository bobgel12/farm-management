import React from 'react';
import {
  Box,
  Select,
  MenuItem,
  FormControl,
  Chip,
  Typography,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import {
  Business as BusinessIcon,
} from '@mui/icons-material';
import { useOrganization } from '../../contexts/OrganizationContext';

const OrganizationSwitcher: React.FC = () => {
  const {
    currentOrganization,
    organizations,
    setCurrentOrganization,
    loading,
  } = useOrganization();

  const handleChange = (event: SelectChangeEvent<string>) => {
    const orgId = event.target.value;
    const org = organizations.find((m) => m.organization.id === orgId);
    if (org) {
      setCurrentOrganization(org.organization);
    }
  };

  if (loading || !organizations.length) {
    return null;
  }

  const currentOrgId = currentOrganization?.id || organizations[0]?.organization.id || '';

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 200 }}>
      <BusinessIcon sx={{ color: 'text.secondary', fontSize: 20 }} />
      <FormControl
        variant="outlined"
        size="small"
        sx={{ minWidth: 180 }}
      >
        <Select
          value={currentOrgId}
          onChange={handleChange}
          displayEmpty
          sx={{
            '& .MuiSelect-select': {
              py: 1,
              fontSize: '0.875rem',
            },
          }}
        >
          {organizations.map((membership) => (
            <MenuItem
              key={membership.organization.id}
              value={membership.organization.id}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                <Typography variant="body2" sx={{ flex: 1 }}>
                  {membership.organization.name}
                </Typography>
                <Chip
                  label={membership.role}
                  size="small"
                  color={
                    membership.role === 'owner'
                      ? 'primary'
                      : membership.role === 'admin'
                      ? 'secondary'
                      : 'default'
                  }
                  sx={{ height: 20, fontSize: '0.7rem' }}
                />
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      {currentOrganization && (
        <Chip
          label={currentOrganization.subscription_tier}
          size="small"
          color={
            currentOrganization.subscription_tier === 'enterprise'
              ? 'primary'
              : currentOrganization.subscription_tier === 'premium'
              ? 'secondary'
              : 'default'
          }
          sx={{ fontSize: '0.7rem', height: 24 }}
        />
      )}
    </Box>
  );
};

export default OrganizationSwitcher;

