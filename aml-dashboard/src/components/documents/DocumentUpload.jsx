import { Upload } from 'lucide-react';
import { useState } from 'react';

const DocumentUpload = ({ onUpload, isProcessing = false, error }) => {
  const [isDragging, setIsDragging] = useState(false);

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
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0 && onUpload && !isProcessing) {
      onUpload(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0 && onUpload && !isProcessing) {
      onUpload(files[0]);
    }
    e.target.value = '';
  };

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-primary-navy mb-4">Upload Document</h2>
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragging
            ? 'border-primary-light bg-primary-light/5'
            : 'border-surface-iron bg-surface-grey/30'
        }`}
      >
        <Upload className="w-12 h-12 mx-auto text-primary-navy/40 mb-4" />
        <p className="text-text-primary font-medium mb-2">
          {isProcessing ? 'Processing document…' : 'Drop your document here, or click to browse'}
        </p>
        <p className="text-sm text-text-secondary mb-4">
          Supports PDF, PNG, JPG (Max 10MB)
        </p>
        <input
          type="file"
          onChange={handleFileSelect}
          accept=".pdf,.png,.jpg,.jpeg"
          className="hidden"
          id="file-upload"
          disabled={isProcessing}
        />
        <label
          htmlFor="file-upload"
          className={`btn-primary inline-block ${isProcessing ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          {isProcessing ? 'Analyzing…' : 'Select File'}
        </label>
        {error && (
          <p className="text-sm text-risk-high mt-4">
            {error}
          </p>
        )}
      </div>
    </div>
  );
};

export default DocumentUpload;
