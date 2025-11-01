const RiskScore = ({ score, size = 'md' }) => {
  const getColor = () => {
    if (score >= 70) return 'text-risk-high';
    if (score >= 40) return 'text-risk-medium';
    return 'text-risk-low';
  };

  const getBgColor = () => {
    if (score >= 70) return 'bg-risk-high/10';
    if (score >= 40) return 'bg-risk-medium/10';
    return 'bg-risk-low/10';
  };

  const sizeClasses = {
    sm: 'w-16 h-16 text-lg',
    md: 'w-24 h-24 text-2xl',
    lg: 'w-32 h-32 text-3xl',
  };

  return (
    <div className="flex flex-col items-center">
      <div
        className={`${sizeClasses[size]} ${getBgColor()} ${getColor()} rounded-full flex items-center justify-center font-bold border-4 border-current/20`}
      >
        {score}
      </div>
      <div className="text-xs text-text-secondary mt-2">Risk Score</div>
    </div>
  );
};

export default RiskScore;
