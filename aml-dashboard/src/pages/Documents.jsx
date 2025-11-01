import { useState } from 'react';
import { FileText, Eye } from 'lucide-react';
import DocumentUpload from '../components/documents/DocumentUpload';
import DocumentViewer from '../components/documents/DocumentViewer';
import RiskBadge from '../components/shared/RiskBadge';
import { mockDocuments } from '../data/mockData';

const Documents = () => {
  const [documents, setDocuments] = useState(mockDocuments);
  const [selectedDocument, setSelectedDocument] = useState(null);

  const handleUpload = (file) => {
    alert(`File uploaded: ${file.name}\n\nIn production, this would:\n1. Upload to server\n2. Run OCR extraction\n3. Perform image forensics\n4. Generate risk score\n5. Display results`);
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

      <DocumentUpload onUpload={handleUpload} />

      {/* Documents List */}
      <div className="card">
        <h2 className="text-xl font-semibold text-primary-navy mb-4">Analyzed Documents</h2>
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
                    Customer: {doc.customerId} • Uploaded: {doc.uploadDate}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm text-text-secondary">Risk Score</p>
                  <p className="text-2xl font-bold text-primary-navy">{doc.riskScore}</p>
                </div>
                <RiskBadge
                  risk={doc.status === 'approved' ? 'Low' : doc.riskScore >= 70 ? 'High' : 'Medium'}
                />
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
