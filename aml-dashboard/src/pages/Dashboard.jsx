import { AlertTriangle, FileText, TrendingUp, Shield } from 'lucide-react';
import MetricCard from '../components/dashboard/MetricCard';
import ActivityFeed from '../components/dashboard/ActivityFeed';
import { mockMetrics, mockActivity } from '../data/mockData';

const Dashboard = () => {
  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="bg-white rounded-lg shadow-subtle p-8">
        <h1 className="text-4xl font-bold text-primary-navy mb-2">
          AML Monitoring Dashboard
        </h1>
        <p className="text-text-secondary">
          Real-time anti-money laundering surveillance and compliance monitoring
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="High Risk Alerts"
          value={mockMetrics.highRiskAlerts}
          subtitle="Requiring immediate review"
          icon={AlertTriangle}
        />
        <MetricCard
          title="Documents Analyzed"
          value={mockMetrics.documentsAnalyzed}
          subtitle="This month"
          icon={FileText}
        />
        <MetricCard
          title="STRs Filed"
          value={mockMetrics.strsFiled}
          subtitle="Suspicious transactions reported"
          icon={Shield}
        />
        <MetricCard
          title="Compliance Rate"
          value={`${mockMetrics.complianceRate}%`}
          subtitle="Overall system health"
          icon={TrendingUp}
        />
      </div>

      {/* Activity Feed and Quick Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ActivityFeed activities={mockActivity} />
        </div>
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">Pending Review</h3>
            <div className="text-center">
              <div className="text-5xl font-bold text-risk-medium mb-2">
                {mockMetrics.pendingReview}
              </div>
              <p className="text-sm text-text-secondary">
                Items awaiting compliance approval
              </p>
              <button className="btn-primary mt-4 w-full">
                Review Now
              </button>
            </div>
          </div>
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Transaction Monitor</span>
                <span className="text-risk-low text-sm font-medium">● Active</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Document Analyzer</span>
                <span className="text-risk-low text-sm font-medium">● Active</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Rules Engine</span>
                <span className="text-risk-low text-sm font-medium">● Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
