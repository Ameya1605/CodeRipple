

export type RiskTier = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

interface RiskBadgeProps {
  tier: RiskTier;
  className?: string;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ tier, className = '' }) => {
  return (
    <span className={`risk-badge ${tier} ${className}`}>
      {tier}
    </span>
  );
};
