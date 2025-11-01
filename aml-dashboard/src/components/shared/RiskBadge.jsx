const RiskBadge = ({ risk }) => {
  const riskLevel = risk.toLowerCase();

  const badgeClasses = {
    low: 'risk-badge-low',
    medium: 'risk-badge-medium',
    high: 'risk-badge-high',
  };

  return (
    <span className={badgeClasses[riskLevel] || 'risk-badge-low'}>
      {risk}
    </span>
  );
};

export default RiskBadge;
