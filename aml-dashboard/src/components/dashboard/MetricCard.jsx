import Card from '../shared/Card';

const MetricCard = ({ title, value, subtitle, icon: Icon, trend }) => {
  return (
    <Card className="flex items-start justify-between">
      <div>
        <p className="text-sm text-text-secondary mb-1">{title}</p>
        <p className="text-3xl font-bold text-primary-navy">{value}</p>
        {subtitle && (
          <p className="text-xs text-text-secondary mt-1">{subtitle}</p>
        )}
      </div>
      {Icon && (
        <div className="p-3 bg-primary-navy/5 rounded-lg">
          <Icon className="w-6 h-6 text-primary-navy" />
        </div>
      )}
    </Card>
  );
};

export default MetricCard;
