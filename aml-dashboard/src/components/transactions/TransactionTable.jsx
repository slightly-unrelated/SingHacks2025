import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import RiskBadge from '../shared/RiskBadge';

const TransactionTable = ({ transactions }) => {
  const [expandedRow, setExpandedRow] = useState(null);
  const [filterRisk, setFilterRisk] = useState('all');

  const filteredTransactions = transactions.filter((t) => {
    if (filterRisk === 'all') return true;
    return t.riskRating.toLowerCase() === filterRisk;
  });

  const sortedTransactions = [...filteredTransactions].sort((a, b) => b.riskScore - a.riskScore);

  const toggleExpand = (id) => {
    setExpandedRow(expandedRow === id ? null : id);
  };

  return (
    <div className="card">
      {/* Filters */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-primary-navy">High-Risk Account Analysis</h2>
          <p className="text-sm text-text-secondary mt-1">
            {sortedTransactions.length} account(s) flagged (sorted by risk score)
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <label className="text-sm text-text-secondary">Filter by risk:</label>
          <select
            value={filterRisk}
            onChange={(e) => setFilterRisk(e.target.value)}
            className="px-4 py-2 border border-surface-iron rounded focus:outline-none focus:ring-2 focus:ring-primary-light"
          >
            <option value="all">All Levels</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-surface-iron">
              <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary w-12"></th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                Account ID
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                Risk Score
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                Risk Level
              </th>
              <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">
                Total Sent
              </th>
              <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">
                Total Received
              </th>
              <th className="text-center py-3 px-4 text-sm font-semibold text-text-primary">
                Transactions
              </th>
              <th className="text-center py-3 px-4 text-sm font-semibold text-text-primary">
                Risk Indicators
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedTransactions.map((account) => (
              <>
                <tr
                  key={account.id}
                  className="border-b border-surface-grey hover:bg-surface-grey/50 transition-colors cursor-pointer"
                  onClick={() => toggleExpand(account.id)}
                >
                  <td className="py-3 px-4">
                    {expandedRow === account.id ? (
                      <ChevronUp className="w-4 h-4 text-text-secondary" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-text-secondary" />
                    )}
                  </td>
                  <td className="py-3 px-4 text-sm font-mono text-text-primary font-medium">
                    {account.accountId}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center">
                      <div className="text-2xl font-bold text-primary-navy mr-2">
                        {account.riskScore}
                      </div>
                      <div className="text-xs text-text-secondary">/100</div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <RiskBadge risk={account.riskRating} />
                  </td>
                  <td className="py-3 px-4 text-right text-sm font-medium text-text-primary">
                    ${parseFloat(account.totalSent).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right text-sm font-medium text-text-primary">
                    ${parseFloat(account.totalReceived).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="text-sm text-text-primary">
                      <span className="font-medium">{account.numSentTx}</span> sent /{' '}
                      <span className="font-medium">{account.numReceivedTx}</span> received
                    </div>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="flex items-center justify-center space-x-2">
                      {account.crossBorderSent + account.crossBorderReceived > 0 && (
                        <span className="text-xs px-2 py-1 bg-risk-medium/10 text-risk-medium rounded">
                          Cross-border
                        </span>
                      )}
                      {account.nightTxSent + account.nightTxReceived > 0 && (
                        <span className="text-xs px-2 py-1 bg-risk-medium/10 text-risk-medium rounded">
                          Night Tx
                        </span>
                      )}
                      {account.smallTxSent + account.smallTxReceived > 5 && (
                        <span className="text-xs px-2 py-1 bg-risk-medium/10 text-risk-medium rounded">
                          Structuring
                        </span>
                      )}
                    </div>
                  </td>
                </tr>

                {/* Expanded Details Row */}
                {expandedRow === account.id && (
                  <tr className="bg-surface-grey/30">
                    <td colSpan="8" className="py-4 px-4">
                      <div className="grid grid-cols-3 gap-4">
                        {/* Transaction Statistics */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                          <h4 className="text-sm font-semibold text-primary-navy mb-3">
                            Transaction Statistics
                          </h4>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Average Sent:</span>
                              <span className="font-medium text-text-primary">
                                ${parseFloat(account.avgSent).toLocaleString()}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Average Received:</span>
                              <span className="font-medium text-text-primary">
                                ${parseFloat(account.avgReceived).toLocaleString()}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Tx Frequency/Day:</span>
                              <span className="font-medium text-text-primary">
                                {account.txFrequencyPerDay}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Account Age:</span>
                              <span className="font-medium text-text-primary">
                                {account.accountAgeDays} days
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Risk Patterns */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                          <h4 className="text-sm font-semibold text-primary-navy mb-3">
                            Risk Patterns
                          </h4>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Cross-border (Sent):</span>
                              <span className="font-medium text-text-primary">
                                {account.crossBorderSent}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Cross-border (Received):</span>
                              <span className="font-medium text-text-primary">
                                {account.crossBorderReceived}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Night Transactions (Sent):</span>
                              <span className="font-medium text-text-primary">
                                {account.nightTxSent}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Night Transactions (Rcv):</span>
                              <span className="font-medium text-text-primary">
                                {account.nightTxReceived}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Structuring Indicators */}
                        <div className="bg-white rounded-lg p-4 shadow-sm">
                          <h4 className="text-sm font-semibold text-primary-navy mb-3">
                            Structuring Indicators
                          </h4>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Small Tx (Sent):</span>
                              <span className="font-medium text-text-primary">
                                {account.smallTxSent}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Small Tx (Received):</span>
                              <span className="font-medium text-text-primary">
                                {account.smallTxReceived}
                              </span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-text-secondary">Total Small Tx:</span>
                              <span className={`font-medium ${
                                account.smallTxSent + account.smallTxReceived > 5
                                  ? 'text-risk-high'
                                  : 'text-text-primary'
                              }`}>
                                {account.smallTxSent + account.smallTxReceived}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TransactionTable;
