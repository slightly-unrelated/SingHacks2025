import { FileText, X, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import RiskScore from '../shared/RiskScore';

const severityStyles = {
  critical: {
    container: 'bg-risk-high/10 border-risk-high/20',
    icon: <AlertTriangle className="w-4 h-4 text-risk-high" />,
  },
  warning: {
    container: 'bg-risk-medium/10 border-risk-medium/20',
    icon: <AlertTriangle className="w-4 h-4 text-risk-medium" />,
  },
  info: {
    container: 'bg-risk-low/10 border-risk-low/20',
    icon: <Info className="w-4 h-4 text-risk-low" />,
  },
  pass: {
    container: 'bg-risk-low/10 border-risk-low/20',
    icon: <CheckCircle className="w-4 h-4 text-risk-low" />,
  },
};

const issueTypeMap = {
  'double-spacing': {
    severity: 'info',
    formatter: (issue) => `Additional spacing detected around line ${issue.line + 1}.`,
  },
  'irregular-font': {
    severity: 'warning',
    formatter: (issue) =>
      `Font size variation detected on line ${issue.line + 1} (coefficient of variation ${issue.cv}).`,
  },
  'indent-inconsistent': {
    severity: 'info',
    formatter: (issue) =>
      `Indentation at line ${issue.line + 1} differs from dominant offset (${issue.left}px vs ${issue.dominant}px).`,
  },
  spelling: {
    severity: 'warning',
    formatter: (issue) =>
      `Low OCR confidence (${Math.round(issue.conf || 0)}%) for phrase "${issue.at?.text ?? 'unknown'}".`,
  },
  'missing-section': {
    severity: 'critical',
    formatter: (issue) => `Required section header "${issue.header}" not detected.`,
  },
  'incorrect-header': {
    severity: 'warning',
    formatter: (issue) =>
      `Header "${issue.got}" may be incorrect. Expected something similar to "${issue.want}".`,
  },
  'structure-order': {
    severity: 'critical',
    formatter: (issue) => {
      if (Array.isArray(issue.detail) && issue.detail.length > 0) {
        return issue.detail
          .map(
            (entry) =>
              `Section "${entry.a}" appears after "${entry.b}" (${(entry.posA ?? 0) + 1} vs ${(entry.posB ?? 0) + 1}).`
          )
          .join(' ');
      }
      return 'Document sections appear out of the expected order.';
    },
  },
};

const expandIssues = (issues) => {
  if (!Array.isArray(issues)) return [];
  return issues.flatMap((issue) => {
    const config = issueTypeMap[issue.type];
    if (!config) {
      return {
        severity: 'info',
        message: issue.type ? `Reported issue: ${issue.type}` : 'Unspecified document issue.',
      };
    }

    const message = config.formatter(issue);
    if (!message) {
      return [];
    }

    if (Array.isArray(message)) {
      return message
        .filter(Boolean)
        .map((entry) => ({ severity: config.severity, message: entry }));
    }

    return { severity: config.severity, message };
  });
};

const formatPercent = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '—';
  }
  const percent = Number(value) <= 1 ? Number(value) * 100 : Number(value);
  return `${Math.round(percent)}%`;
};

const metricItems = (summary) => {
  if (!summary) return [];
  return [
    { label: 'Lines Detected', value: summary.lines ?? '—' },
    { label: 'Tokens Extracted', value: summary.tokens ?? '—' },
    { label: 'Template Match', value: formatPercent(summary.template_match) },
    { label: 'Completeness', value: formatPercent(summary.completeness) },
    { label: 'Order Score', value: formatPercent(summary.order_score) },
  ];
};

const factorLabel = (key) => {
  switch (key) {
    case 'double':
      return 'Spacing Alerts';
    case 'fonts':
      return 'Font Variance';
    case 'indent':
      return 'Indentation Alerts';
    case 'spelling':
      return 'Low Confidence Tokens';
    case 'missing':
      return 'Missing Sections';
    case 'order':
      return 'Order Issues';
    case 'template':
      return 'Template Match Dampener';
    case 'completeness':
      return 'Completeness Dampener';
    default:
      return key;
  }
};

const formatFactorValue = (value) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return value;
  }
  if (value > 1 || value < 0) {
    return Number.isInteger(value) ? value : value.toFixed(2);
  }
  return `${Math.round(value * 100)}%`;
};

const DocumentViewer = ({ document, onClose }) => {
  const report = document.report || {};
  const summaryMetrics = metricItems(report.summary);
  const riskFactors = Object.entries(report?.risk?.factors || {});
  const issueList = expandIssues(report.issues);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-primary-navy text-white p-6 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <FileText className="w-6 h-6" />
            <div>
              <h2 className="text-2xl font-bold">Document Analysis</h2>
              <p className="text-sm text-white/70 mt-1">{document.fileName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-6">
            <div className="bg-surface-grey rounded-lg p-6">
              <h3 className="text-lg font-semibold text-primary-navy mb-4">Document Details</h3>
              <div className="space-y-3 text-sm text-text-secondary">
                <div className="flex justify-between">
                  <span>Uploaded</span>
                  <span className="text-text-primary">{new Date(document.uploadedAt).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Type</span>
                  <span className="text-text-primary">{document.type.toUpperCase()}</span>
                </div>
                {document.pages !== null && (
                  <div className="flex justify-between">
                    <span>Pages Processed</span>
                    <span className="text-text-primary">{document.pages}</span>
                  </div>
                )}
              </div>
            </div>

            {summaryMetrics.length > 0 && (
              <div className="bg-white border border-surface-iron rounded-lg p-6">
                <h3 className="text-lg font-semibold text-primary-navy mb-4">Extraction Metrics</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  {summaryMetrics.map((metric) => (
                    <div key={metric.label} className="bg-surface-grey rounded-lg p-4">
                      <p className="text-text-secondary">{metric.label}</p>
                      <p className="text-lg font-semibold text-primary-navy">{metric.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {riskFactors.length > 0 && (
              <div className="bg-white border border-surface-iron rounded-lg p-6">
                <h3 className="text-lg font-semibold text-primary-navy mb-4">Risk Factors</h3>
                <div className="space-y-2 text-sm">
                  {riskFactors.map(([key, value]) => (
                    <div key={key} className="flex justify-between bg-surface-grey rounded p-3">
                      <span className="text-text-secondary">{factorLabel(key)}</span>
                      <span className="text-text-primary font-medium">
                        {typeof value === 'number'
                          ? formatFactorValue(value)
                          : value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="bg-surface-grey rounded-lg p-6 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-primary-navy mb-2">Risk Assessment</h3>
                <p className="text-sm text-text-secondary">
                  Status: <span className={`font-medium ${document.status === 'approved' ? 'text-risk-low' : 'text-risk-high'}`}>
                    {document.status === 'approved' ? 'Approved' : 'Flagged'}
                  </span>
                </p>
              </div>
              <RiskScore score={document.riskScore} />
            </div>

            <div>
              <h3 className="text-lg font-semibold text-primary-navy mb-3">
                Issues Detected ({issueList.length})
              </h3>
              {issueList.length === 0 ? (
                <div className="bg-surface-grey rounded-lg p-4 text-sm text-text-secondary">
                  No issues detected by automated checks.
                </div>
              ) : (
                <div className="space-y-2">
                  {issueList.map((issue, index) => {
                    const style = severityStyles[issue.severity] || severityStyles.info;
                    return (
                      <div
                        key={`${issue.message}-${index}`}
                        className={`flex items-start space-x-3 p-3 border rounded-lg ${style.container}`}
                      >
                        {style.icon}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-text-primary">{issue.message}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {Array.isArray(report.audit) && report.audit.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold text-primary-navy mb-3">Processing Audit</h3>
                <div className="bg-white border border-surface-iron rounded-lg p-4 text-sm text-text-secondary space-y-2">
                  {report.audit.map((entry) => (
                    <div key={entry}>{entry}</div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center justify-end space-x-3 pt-4">
              {document.status === 'flagged' ? (
                <>
                  <button className="bg-risk-high text-white px-6 py-2.5 rounded hover:bg-risk-high/90 transition-colors">
                    Reject Document
                  </button>
                  <button className="btn-secondary">
                    Request More Info
                  </button>
                </>
              ) : (
                <button className="bg-risk-low text-white px-6 py-2.5 rounded hover:bg-risk-low/90 transition-colors">
                  Approved
                </button>
              )}
              <button onClick={onClose} className="btn-primary">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentViewer;
