import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle } from 'lucide-react';
import TransactionTable from '../components/transactions/TransactionTable';
import { uploadTransactionCSV, transformAPIResponse } from '../services/api';
import { getLocalJSON, setLocalJSON } from '../utils/storage';
import { getCookieJSON, deleteCookie } from '../utils/cookies';

const Transactions = () => {
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  // Drag-and-drop removed in favor of a single action button

  const STORAGE_KEY = 'aml_tx_analysis';
  const COOKIE_NAME = 'aml_tx_analysis'; // legacy key for migration

  // Load last analysis from localStorage on mount (with one-time cookie migration)
  useEffect(() => {
    const saved = getLocalJSON(STORAGE_KEY);
    if (saved && typeof saved === 'object') {
      if (Array.isArray(saved.transactions)) setTransactions(saved.transactions);
      if (saved.uploadStatus) setUploadStatus(saved.uploadStatus);
      return;
    }

    // Legacy cookie migration, if present
    const legacy = getCookieJSON(COOKIE_NAME);
    if (legacy && typeof legacy === 'object') {
      if (Array.isArray(legacy.transactions)) setTransactions(legacy.transactions);
      if (legacy.uploadStatus) setUploadStatus(legacy.uploadStatus);
      try {
        setLocalJSON(STORAGE_KEY, legacy);
        deleteCookie(COOKIE_NAME);
      } catch {
        // ignore
      }
    }
  }, []);

  const saveToStorage = (payload) => {
    const tx = Array.isArray(payload.transactions) ? payload.transactions : [];
    setLocalJSON(STORAGE_KEY, {
      uploadStatus: payload.uploadStatus || null,
      transactions: tx,
      totalTransactions: tx.length,
      savedAt: new Date().toISOString(),
      version: 2
    });
  };

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
          saveToStorage({
            uploadStatus: {
              type: 'success',
              message: 'Analysis complete! No high-risk accounts detected (all accounts below 85% risk threshold).'
            },
            transactions: []
          });
        } else {
          const transformedData = transformAPIResponse(response);
          setTransactions(transformedData);
          setUploadStatus({
            type: 'success',
            message: `Analysis complete! ${response.alerts_found} high-risk account(s) detected above 85% risk threshold.`
          });
          saveToStorage({
            uploadStatus: {
              type: 'success',
              message: `Analysis complete! ${response.alerts_found} high-risk account(s) detected above 85% risk threshold.`
            },
            transactions: transformedData
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
      saveToStorage({
        uploadStatus: {
          type: 'error',
          message: 'Analysis failed. Please check your file and try again.'
        },
        transactions: []
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

  const openFileDialog = () => {
    if (isLoading) return;
    const input = document.getElementById('csv-upload');
    if (input) input.click();
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-subtle p-6 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-primary-navy mb-2">
            Transaction Monitoring
          </h1>
          <p className="text-text-secondary">
            Real-time AML transaction surveillance and risk assessment
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="file"
            onChange={handleFileSelect}
            accept=".csv"
            className="hidden"
            id="csv-upload"
            disabled={isLoading}
          />
          <button
            type="button"
            onClick={openFileDialog}
            disabled={isLoading}
            className={`px-6 py-2 bg-primary-navy text-white rounded-md font-medium transition-colors ${
              isLoading ? 'opacity-60 cursor-not-allowed' : 'hover:bg-primary-navy/90'
            }`}
          >
            {isLoading ? 'Analyzing…' : 'Update Data'}
          </button>
        </div>
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
