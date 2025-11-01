import { AlertTriangle, FileText, CheckCircle, Shield } from 'lucide-react';
import Card from '../shared/Card';

const ActivityFeed = ({ activities }) => {
  const getIcon = (type) => {
    switch (type) {
      case 'transaction':
        return AlertTriangle;
      case 'document':
        return FileText;
      case 'str':
        return Shield;
      default:
        return CheckCircle;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high':
        return 'text-risk-high bg-risk-high/10';
      case 'medium':
        return 'text-risk-medium bg-risk-medium/10';
      case 'low':
        return 'text-risk-low bg-risk-low/10';
      default:
        return 'text-text-secondary bg-surface-grey';
    }
  };

  return (
    <Card title="Recent Activity">
      <div className="space-y-3">
        {activities.map((activity) => {
          const Icon = getIcon(activity.type);
          return (
            <div
              key={activity.id}
              className="flex items-start space-x-3 p-3 rounded-lg hover:bg-surface-grey transition-colors"
            >
              <div className={`p-2 rounded-full ${getSeverityColor(activity.severity)}`}>
                <Icon className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-text-primary">{activity.message}</p>
                <p className="text-xs text-text-secondary mt-1">
                  {activity.timestamp}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};

export default ActivityFeed;
