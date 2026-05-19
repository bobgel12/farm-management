import React, { useEffect, useState } from 'react';
import { Chip, Tooltip, CircularProgress } from '@mui/material';
import api from '../../services/api';
import { FlockRiskScore } from '../../types/monitoring';

interface Props {
  flockId: number;
  size?: 'small' | 'medium';
}

const FlockRiskBadge: React.FC<Props> = ({ flockId, size = 'small' }) => {
  const [scores, setScores] = useState<FlockRiskScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await api.get(`/flocks/${flockId}/risk_scores/`);
        if (!cancelled) setScores(response.data ?? []);
      } catch {
        if (!cancelled) setScores([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [flockId]);

  if (loading) return <CircularProgress size={16} />;
  const mortality = scores.find((s) => s.risk_type === 'mortality_3d');
  if (!mortality) return null;

  const pct = Math.round(mortality.score * 100);
  const color = pct >= 70 ? 'error' : pct >= 40 ? 'warning' : 'success';

  return (
    <Tooltip title={`3-day mortality risk model ${mortality.model_version} (confidence ${(mortality.confidence * 100).toFixed(0)}%)`}>
      <Chip label={`Mortality risk ${pct}%`} color={color} size={size} variant="outlined" />
    </Tooltip>
  );
};

export default FlockRiskBadge;
