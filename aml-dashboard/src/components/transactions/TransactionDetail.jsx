import { X, AlertTriangle, Shield, FileText } from 'lucide-react';
import RiskScore from '../shared/RiskScore';
import RiskBadge from '../shared/RiskBadge';
import { generateTransactionReport } from '../../utils/pdfGenerator';

const TransactionDetail = ({ transaction, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-primary-navy text-white p-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Transaction Details</h2>
            <p className="text-sm text-white/70 mt-1 font-mono">{transaction.id}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Risk Score Section */}
          <div className="flex items-center justify-between p-6 bg-surface-grey rounded-lg">
            <div>
              <h3 className="text-lg font-semibold text-primary-navy mb-2">Risk Assessment</h3>
              <RiskBadge risk={transaction.riskRating} />
              {transaction.flagReason && (
                <div className="mt-3 flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-risk-high mt-0.5" />
                  <p className="text-sm text-text-primary">{transaction.flagReason}</p>
                </div>
              )}
            </div>
            <RiskScore score={transaction.riskScore} size="lg" />
          </div>

          {/* Customer Information */}
          <div>
            <h3 className="text-lg font-semibold text-primary-navy mb-3">Customer Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-text-secondary">Customer Name</label>
                <p className="text-sm font-medium text-text-primary">{transaction.customerName}</p>
              </div>
              <div>
                <label className="text-xs text-text-secondary">Customer ID</label>
                <p className="text-sm font-medium text-text-primary font-mono">{transaction.customerId}</p>
              </div>
              <div>
                <label className="text-xs text-text-secondary">Risk Rating</label>
                <p className="text-sm font-medium text-text-primary">{transaction.riskRating}</p>
              </div>
              <div>
                <label className="text-xs text-text-secondary">PEP Status</label>
                <p className="text-sm font-medium text-text-primary">
                  {transaction.isPep ? '⚠️ Yes' : 'No'}
                </p>
              </div>
            </div>
          </div>

          {/* Transaction Details */}
          <div>
            <h3 className="text-lg font-semibold text-primary-navy mb-3">Transaction Details</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-text-secondary">Amount</label>
                <p className="text-sm font-medium text-text-primary">
                  {transaction.currency} {transaction.amount.toLocaleString()}
                </p>
              </div>
              <div>
                <label className="text-xs text-text-secondary">Date</label>
                <p className="text-sm font-medium text-text-primary">
                  {new Date(transaction.date).toLocaleString()}
                </p>
              </div>
              <div>
                <label className="text-xs text-text-secondary">Jurisdiction</label>
                <p className="text-sm font-medium text-text-primary">{transaction.jurisdiction}</p>
              </div>
              <div>
                <label className="text-xs text-text-secondary">Product Type</label>
                <p className="text-sm font-medium text-text-primary capitalize">
                  {transaction.productType.replace('_', ' ')}
                </p>
              </div>
              <div>
                <label className="text-xs text-text-secondary">Sanctions Screening</label>
                <p className="text-sm font-medium text-text-primary capitalize">
                  {transaction.sanctionsScreening}
                </p>
              </div>
              {transaction.dailyCashTotal && (
                <div>
                  <label className="text-xs text-text-secondary">Daily Cash Total</label>
                  <p className="text-sm font-medium text-text-primary">
                    {transaction.currency} {transaction.dailyCashTotal.toLocaleString()} ({transaction.dailyCashCount} txns)
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Compliance Checks */}
          <div>
            <h3 className="text-lg font-semibold text-primary-navy mb-3">Compliance Checks</h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-surface-grey rounded">
                <span className="text-sm text-text-primary">Enhanced Due Diligence (EDD)</span>
                <span className={`text-sm font-medium ${transaction.eddRequired ? (transaction.eddPerformed ? 'text-risk-low' : 'text-risk-high') : 'text-text-secondary'}`}>
                  {transaction.eddRequired ? (transaction.eddPerformed ? '✓ Complete' : '✗ Required but not performed') : 'Not Required'}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-surface-grey rounded">
                <span className="text-sm text-text-primary">Suspicious Transaction Report (STR)</span>
                <span className={`text-sm font-medium ${transaction.strFiled ? 'text-risk-high' : 'text-text-secondary'}`}>
                  {transaction.strFiled ? `✓ Filed ${transaction.strFiledDate ? `on ${new Date(transaction.strFiledDate).toLocaleDateString()}` : ''}` : 'Not Filed'}
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t">
            <button
              onClick={() => generateTransactionReport(transaction)}
              className="btn-secondary"
            >
              <FileText className="w-4 h-4 inline mr-2" />
              Generate Report
            </button>
            {!transaction.strFiled && transaction.riskScore >= 70 && (
              <button className="bg-risk-high text-white px-6 py-2.5 rounded hover:bg-risk-high/90 transition-colors">
                <Shield className="w-4 h-4 inline mr-2" />
                File STR
              </button>
            )}
            <button onClick={onClose} className="btn-primary">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionDetail;
