import { useEffect, useState } from 'react';
import { FileText, Eye } from 'lucide-react';
import DocumentUpload from '../components/documents/DocumentUpload';
import DocumentViewer from '../components/documents/DocumentViewer';
import RiskBadge from '../components/shared/RiskBadge';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:4000';
const STORAGE_KEY = 'analyzedDocuments';

const loadStoredDocuments = () => {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (err) {
    console.warn('Unable to load stored documents', err);
    return [];
  }
};

const getDocumentType = (file) => {
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (ext === 'pdf' || file.type === 'application/pdf') {
    return { type: 'pdf', endpoint: '/process/pdf' };
  }
  if (['png', 'jpg', 'jpeg'].includes(ext) || file.type.startsWith('image/')) {
    return { type: 'image', endpoint: '/process/image' };
  }
  throw new Error('Unsupported file type. Please upload a PDF or image file.');
};

const getRiskLevel = (score) => {
  if (score >= 70) return 'High';
  if (score >= 40) return 'Medium';
  return 'Low';
};

const normalizeDocument = (file, payload, type) => {
  const uploadedAt = new Date().toISOString();
  const report = payload?.report || {};
  const riskScore = Math.round(report?.risk?.score ?? 0);
  const riskLevel = getRiskLevel(riskScore);

  return {
    id: payload?.id || uploadedAt,
    fileName: file.name,
    uploadedAt,
    riskScore,
    riskLevel,
    status: riskScore >= 60 ? 'flagged' : 'approved',
    type,
    pages: payload?.pages ?? null,
    report,
    artifacts: payload?.artifacts ?? {},
  };
};

const parseErrorMessage = (raw, status) => {
  if (!raw) {
    return `Failed to process document (status ${status}).`;
  }
  if (typeof raw === 'string') {
    return raw;
  }
  if (raw.detail) {
    return Array.isArray(raw.detail) ? raw.detail[0]?.msg || String(raw.detail[0]) : raw.detail;
  }
  if (raw.message) {
    return raw.message;
  }
  return `Failed to process document (status ${status}).`;
};

const Documents = () => {
  const [documents, setDocuments] = useState(() => loadStoredDocuments());
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(documents));
    } catch (err) {
      console.warn('Unable to persist analyzed documents', err);
    }
  }, [documents]);

  const handleUpload = async (file) => {
    setError('');

    try {
      const { type, endpoint } = getDocumentType(file);
      setIsProcessing(true);

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      const text = await response.text();
      let parsed = null;
      if (text) {
        try {
          parsed = JSON.parse(text);
        } catch {
          if (response.ok) {
            throw new Error('Unexpected response format from document analysis service.');
          }
        }
      }

      if (!response.ok) {
        throw new Error(parseErrorMessage(parsed ?? text, response.status));
      }

      if (!parsed || typeof parsed !== 'object') {
        throw new Error('Received empty response from document analysis service.');
      }

      const normalized = normalizeDocument(file, parsed, type);
      setDocuments((prev) => [normalized, ...prev]);
      setSelectedDocument(normalized);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Document processing failed.';
      setError(message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-subtle p-8">
        <h1 className="text-4xl font-bold text-primary-navy mb-2">
          Document Analysis
        </h1>
        <p className="text-text-secondary">
          Automated document verification and fraud detection
        </p>
      </div>

      <DocumentUpload onUpload={handleUpload} isProcessing={isProcessing} error={error} />

      {/* Documents List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-primary-navy mb-4">Analyzed Documents</h2>
        {documents.length === 0 ? (
          <div className="p-6 bg-surface-grey rounded-lg text-text-secondary text-sm">
            Upload a document to view automated analysis results.
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-4 bg-surface-grey hover:bg-surface-iron/30 rounded-lg transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className="p-3 bg-primary-navy/5 rounded-lg">
                    <FileText className="w-6 h-6 text-primary-navy" />
                  </div>
                  <div>
                    <p className="font-medium text-text-primary">{doc.fileName}</p>
                    <p className="text-sm text-text-secondary">
                      {[
                        `Uploaded: ${new Date(doc.uploadedAt).toLocaleString()}`,
                        doc.pages !== null && doc.pages !== undefined ? `Pages: ${doc.pages}` : null,
                        `Type: ${doc.type.toUpperCase()}`,
                      ]
                        .filter(Boolean)
                        .join(' • ')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <p className="text-sm text-text-secondary">Risk Score</p>
                    <p className="text-2xl font-bold text-primary-navy">{doc.riskScore}</p>
                  </div>
                  <RiskBadge risk={doc.riskLevel} />
                  <button
                    onClick={() => setSelectedDocument(doc)}
                    className="btn-secondary"
                  >
                    <Eye className="w-4 h-4 inline mr-2" />
                    View Analysis
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Document Viewer Modal */}
      {selectedDocument && (
        <DocumentViewer
          document={selectedDocument}
          onClose={() => setSelectedDocument(null)}
        />
      )}
    </div>
  );
};

export default Documents;
