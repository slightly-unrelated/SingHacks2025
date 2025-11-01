import { useState } from 'react';
import { Eye } from 'lucide-react';
import RiskBadge from '../shared/RiskBadge';
import TransactionDetail from './TransactionDetail';

const TransactionTable = ({ transactions }) => {
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [filterRisk, setFilterRisk] = useState('all');

  const filteredTransactions = transactions.filter((t) => {
    if (filterRisk === 'all') return true;
    return t.riskRating.toLowerCase() === filterRisk;
  });

  const sortedTransactions = [...filteredTransactions].sort((a, b) => b.riskScore - a.riskScore);

  return (
    <>
      <div className="card">
        {/* Filters */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-semibold text-primary-navy">Transactions</h2>
            <p className="text-sm text-text-secondary mt-1">
              {sortedTransactions.length} transactions (sorted by risk score)
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
                <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                  Transaction ID
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                  Customer
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                  Amount
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                  Date
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                  Risk Score
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                  Risk Level
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-text-primary">
                  Status
                </th>
                <th className="text-right py-3 px-4 text-sm font-semibold text-text-primary">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedTransactions.map((transaction) => (
                <tr
                  key={transaction.id}
                  className="border-b border-surface-grey hover:bg-surface-grey/50 transition-colors"
                >
                  <td className="py-3 px-4 text-sm text-text-secondary font-mono">
                    {transaction.id.substring(0, 8)}...
                  </td>
                  <td className="py-3 px-4">
                    <div>
                      <div className="text-sm font-medium text-text-primary">
                        {transaction.customerName}
                      </div>
                      <div className="text-xs text-text-secondary">
                        {transaction.customerId}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-sm font-medium text-text-primary">
                    {transaction.currency} {transaction.amount.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-sm text-text-secondary">
                    {new Date(transaction.date).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center">
                      <div className="text-2xl font-bold text-primary-navy mr-2">
                        {transaction.riskScore}
                      </div>
                      <div className="text-xs text-text-secondary">/100</div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <RiskBadge risk={transaction.riskRating} />
                  </td>
                  <td className="py-3 px-4">
                    {transaction.strFiled ? (
                      <span className="text-xs font-medium text-risk-high">STR Filed</span>
                    ) : transaction.isPep ? (
                      <span className="text-xs font-medium text-risk-medium">PEP</span>
                    ) : (
                      <span className="text-xs text-text-secondary">Normal</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => setSelectedTransaction(transaction)}
                      className="inline-flex items-center space-x-1 text-primary-light hover:text-primary-navy transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                      <span className="text-sm">View</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transaction Detail Modal */}
      {selectedTransaction && (
        <TransactionDetail
          transaction={selectedTransaction}
          onClose={() => setSelectedTransaction(null)}
        />
      )}
    </>
  );
};

export default TransactionTable;
