import { FileText, X, AlertTriangle, CheckCircle, Download } from 'lucide-react';
import RiskScore from '../shared/RiskScore';
import { generateDocumentReport } from '../../utils/pdfGenerator';

const DocumentViewer = ({ document, onClose }) => {
  const getIssueIcon = (type) => {
    switch (type) {
      case 'critical':
        return <AlertTriangle className="w-4 h-4 text-risk-high" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-risk-medium" />;
      case 'pass':
        return <CheckCircle className="w-4 h-4 text-risk-low" />;
      default:
        return null;
    }
  };

  const getIssueColor = (type) => {
    switch (type) {
      case 'critical':
        return 'bg-risk-high/10 border-risk-high/20';
      case 'warning':
        return 'bg-risk-medium/10 border-risk-medium/20';
      case 'pass':
        return 'bg-risk-low/10 border-risk-low/20';
      default:
        return 'bg-surface-grey border-surface-iron';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
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

        {/* Content */}
        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Document Preview */}
          <div>
            <h3 className="text-lg font-semibold text-primary-navy mb-4">Document Preview</h3>
            <div className="bg-surface-grey rounded-lg p-8 aspect-[3/4] flex items-center justify-center">
              <div className="text-center text-text-secondary">
                <FileText className="w-16 h-16 mx-auto mb-4 opacity-40" />
                <p>PDF Preview</p>
                <p className="text-sm mt-2">{document.fileName}</p>
              </div>
            </div>
          </div>

          {/* Analysis Results */}
          <div className="space-y-6">
            {/* Risk Score */}
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

            {/* Extracted Data */}
            <div>
              <h3 className="text-lg font-semibold text-primary-navy mb-3">Extracted Data</h3>
              <div className="space-y-3 bg-white border border-surface-iron rounded-lg p-4">
                {Object.entries(document.extractedData).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-start">
                    <span className="text-sm text-text-secondary capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}:
                    </span>
                    <span className="text-sm font-medium text-text-primary text-right">
                      {value}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Issues Found */}
            <div>
              <h3 className="text-lg font-semibold text-primary-navy mb-3">
                Issues Found ({document.issues.length})
              </h3>
              <div className="space-y-2">
                {document.issues.map((issue, index) => (
                  <div
                    key={index}
                    className={`flex items-start space-x-3 p-3 border rounded-lg ${getIssueColor(issue.type)}`}
                  >
                    {getIssueIcon(issue.type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-primary">{issue.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
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
