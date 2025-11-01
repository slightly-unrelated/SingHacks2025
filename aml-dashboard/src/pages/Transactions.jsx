import { useState } from 'react';
import { Upload, AlertCircle, CheckCircle } from 'lucide-react';
import TransactionTable from '../components/transactions/TransactionTable';
import { uploadTransactionCSV, transformAPIResponse } from '../services/api';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileUpload = async (file) => {
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return;
    }

    setIsLoading(true);
    setError(null);
    setUploadStatus(null);

    try {
      const response = await uploadTransactionCSV(file);

      if (response.status === 'success') {
        if (response.alerts_found === 0) {
          setTransactions([]);
          setUploadStatus({
            type: 'success',
            message: 'Analysis complete! No high-risk accounts detected (all accounts below 85% risk threshold).'
          });
        } else {
          const transformedData = transformAPIResponse(response);
          setTransactions(transformedData);
          setUploadStatus({
            type: 'success',
            message: `Analysis complete! ${response.alerts_found} high-risk account(s) detected above 85% risk threshold.`
          });
        }
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to analyze transactions. Please try again.');
      setUploadStatus({
        type: 'error',
        message: 'Analysis failed. Please check your file and try again.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
    e.target.value = '';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

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

      {/* File Upload Section */}
      <div className="bg-white rounded-lg shadow-subtle p-6">
        <h2 className="text-xl font-semibold text-primary-navy mb-4">Upload Transaction CSV</h2>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging
              ? 'border-primary-light bg-primary-light/5'
              : 'border-surface-iron bg-surface-grey/30'
          }`}
        >
          <Upload className="w-12 h-12 mx-auto text-primary-navy/40 mb-4" />
          <p className="text-text-primary font-medium mb-2">
            {isLoading ? 'Analyzing transactions...' : 'Drop your CSV file here, or click to browse'}
          </p>
          <p className="text-sm text-text-secondary mb-4">
            Supports CSV format with transaction data (Risk threshold: 85%)
          </p>
          <input
            type="file"
            onChange={handleFileSelect}
            accept=".csv"
            className="hidden"
            id="csv-upload"
            disabled={isLoading}
          />
          <label
            htmlFor="csv-upload"
            className={`inline-block px-6 py-2 bg-primary-navy text-white rounded-md font-medium transition-colors ${
              isLoading ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer hover:bg-primary-navy/90'
            }`}
          >
            {isLoading ? 'Analyzing...' : 'Select CSV File'}
          </label>
        </div>

        {/* Status Messages */}
        {uploadStatus && (
          <div className={`mt-4 p-4 rounded-lg flex items-start gap-3 ${
            uploadStatus.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {uploadStatus.type === 'success' ? (
              <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            )}
            <p className="font-medium">{uploadStatus.message}</p>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 rounded-lg bg-red-50 text-red-800 border border-red-200 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Results Section */}
      {transactions.length > 0 ? (
        <TransactionTable transactions={transactions} />
      ) : !isLoading && (
        <div className="bg-white rounded-lg shadow-subtle p-12 text-center">
          <p className="text-text-secondary text-lg">
            Upload a CSV file to analyze transaction risk profiles
          </p>
          <p className="text-text-secondary text-sm mt-2">
            The GNN model will identify accounts with risk scores ≥ 85%
          </p>
        </div>
      )}
    </div>
  );
};

export default Transactions;
