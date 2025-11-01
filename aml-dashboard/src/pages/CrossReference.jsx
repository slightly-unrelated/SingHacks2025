import { useState } from 'react';
import { Search, AlertTriangle, Link2 } from 'lucide-react';
import { mockTransactions, mockDocuments } from '../data/mockData';
import RiskBadge from '../components/shared/RiskBadge';
import Card from '../components/shared/Card';

const CrossReference = () => {
  const [customerId, setCustomerId] = useState('');
  const [results, setResults] = useState(null);

  const handleSearch = () => {
    const customerTransactions = mockTransactions.filter(
      (t) => t.customerId === customerId
    );
    const customerDocuments = mockDocuments.filter(
      (d) => d.customerId === customerId
    );

    const mismatches = [];

    // Check for mismatches between transactions and documents
    if (customerTransactions.length > 0 && customerDocuments.length > 0) {
      const transaction = customerTransactions[0];
      const document = customerDocuments[0];

      // Example mismatch detection
      if (document.extractedData.amount && !document.extractedData.amount.includes(transaction.amount.toString())) {
        mismatches.push({
          type: 'amount',
          message: `Amount mismatch: Transaction shows ${transaction.currency} ${transaction.amount.toLocaleString()}, but document shows ${document.extractedData.amount}`,
          severity: 'high',
        });
      }
    }

    // Check for missing documentation
    const highRiskTxns = customerTransactions.filter(t => t.riskScore >= 70);
    if (highRiskTxns.length > 0 && customerDocuments.length === 0) {
      mismatches.push({
        type: 'missing_docs',
        message: `${highRiskTxns.length} high-risk transaction(s) found with no supporting documentation`,
        severity: 'critical',
      });
    }

    setResults({
      transactions: customerTransactions,
      documents: customerDocuments,
      mismatches,
    });
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-risk-high/10 text-risk-high border-risk-high/30';
      case 'high':
        return 'bg-risk-high/10 text-risk-high border-risk-high/30';
      case 'medium':
        return 'bg-risk-medium/10 text-risk-medium border-risk-medium/30';
      default:
        return 'bg-surface-grey text-text-secondary border-surface-iron';
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-subtle p-8">
        <h1 className="text-4xl font-bold text-primary-navy mb-2">
          Cross-Reference Analysis
        </h1>
        <p className="text-text-secondary">
          Link and verify transactions against supporting documentation
        </p>
      </div>

      {/* Search */}
      <Card title="Customer Lookup">
        <div className="flex items-end space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-text-primary mb-2">
              Customer ID
            </label>
            <input
              type="text"
              value={customerId}
              onChange={(e) => setCustomerId(e.target.value)}
              placeholder="e.g., CUST-956783"
              className="w-full px-4 py-3 border border-surface-iron rounded focus:outline-none focus:ring-2 focus:ring-primary-light"
            />
            <p className="text-xs text-text-secondary mt-2">
              Try: CUST-956783, CUST-489206, CUST-786015
            </p>
          </div>
          <button
            onClick={handleSearch}
            className="btn-primary flex items-center"
            disabled={!customerId}
          >
            <Search className="w-4 h-4 mr-2" />
            Search
          </button>
        </div>
      </Card>

      {/* Results */}
      {results && (
        <>
          {/* Mismatches/Alerts */}
          {results.mismatches.length > 0 && (
            <Card title="🚨 Cross-Reference Alerts">
              <div className="space-y-3">
                {results.mismatches.map((mismatch, index) => (
                  <div
                    key={index}
                    className={`flex items-start space-x-3 p-4 border-2 rounded-lg ${getSeverityColor(mismatch.severity)}`}
                  >
                    <AlertTriangle className="w-5 h-5 mt-0.5" />
                    <div className="flex-1">
                      <p className="font-medium capitalize">{mismatch.type.replace('_', ' ')}</p>
                      <p className="text-sm mt-1">{mismatch.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Transactions */}
          <Card title={`Transactions (${results.transactions.length})`}>
            {results.transactions.length > 0 ? (
              <div className="space-y-2">
                {results.transactions.map((txn) => (
                  <div
                    key={txn.id}
                    className="flex items-center justify-between p-4 bg-surface-grey rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-text-primary">
                        {txn.currency} {txn.amount.toLocaleString()}
                      </p>
                      <p className="text-sm text-text-secondary">
                        {new Date(txn.date).toLocaleDateString()} • {txn.productType.replace('_', ' ')}
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <p className="text-xs text-text-secondary">Risk Score</p>
                        <p className="text-lg font-bold text-primary-navy">{txn.riskScore}</p>
                      </div>
                      <RiskBadge risk={txn.riskRating} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-text-secondary py-8">
                No transactions found for this customer
              </p>
            )}
          </Card>

          {/* Documents */}
          <Card title={`Documents (${results.documents.length})`}>
            {results.documents.length > 0 ? (
              <div className="space-y-2">
                {results.documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-4 bg-surface-grey rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-text-primary">{doc.fileName}</p>
                      <p className="text-sm text-text-secondary">
                        Uploaded: {doc.uploadDate} • {doc.issues.length} issues found
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <p className="text-xs text-text-secondary">Risk Score</p>
                        <p className="text-lg font-bold text-primary-navy">{doc.riskScore}</p>
                      </div>
                      <RiskBadge
                        risk={doc.status === 'approved' ? 'Low' : doc.riskScore >= 70 ? 'High' : 'Medium'}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-text-secondary py-8">
                No documents found for this customer
              </p>
            )}
          </Card>

          {/* Combined Risk Assessment */}
          {(results.transactions.length > 0 || results.documents.length > 0) && (
            <Card title="Combined Risk Assessment">
              <div className="grid grid-cols-3 gap-6 text-center">
                <div>
                  <p className="text-sm text-text-secondary mb-2">Transaction Risk</p>
                  <p className="text-4xl font-bold text-primary-navy">
                    {results.transactions.length > 0
                      ? Math.max(...results.transactions.map((t) => t.riskScore))
                      : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary mb-2">Document Risk</p>
                  <p className="text-4xl font-bold text-primary-navy">
                    {results.documents.length > 0
                      ? Math.max(...results.documents.map((d) => d.riskScore))
                      : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-text-secondary mb-2">Combined Risk</p>
                  <p className="text-4xl font-bold text-risk-high">
                    {results.transactions.length > 0 && results.documents.length > 0
                      ? Math.round(
                          (Math.max(...results.transactions.map((t) => t.riskScore)) +
                            Math.max(...results.documents.map((d) => d.riskScore))) /
                            2
                        )
                      : results.transactions.length > 0
                      ? Math.max(...results.transactions.map((t) => t.riskScore))
                      : results.documents.length > 0
                      ? Math.max(...results.documents.map((d) => d.riskScore))
                      : '—'}
                  </p>
                </div>
              </div>
              {results.mismatches.length > 0 && (
                <div className="mt-6 p-4 bg-risk-high/10 border border-risk-high/30 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Link2 className="w-5 h-5 text-risk-high" />
                    <p className="font-medium text-risk-high">
                      {results.mismatches.length} cross-reference issue(s) detected
                    </p>
                  </div>
                  <p className="text-sm text-text-primary mt-2">
                    Immediate review required by compliance team
                  </p>
                </div>
              )}
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default CrossReference;
