import TransactionTable from '../components/transactions/TransactionTable';
import { mockTransactions } from '../data/mockData';

const Transactions = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-subtle p-8">
        <h1 className="text-4xl font-bold text-primary-navy mb-2">
          Transaction Monitoring
        </h1>
        <p className="text-text-secondary">
          Real-time AML transaction surveillance and risk assessment
        </p>
      </div>

      <TransactionTable transactions={mockTransactions} />
    </div>
  );
};

export default Transactions;
