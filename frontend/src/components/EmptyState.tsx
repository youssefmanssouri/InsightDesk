import React, { useState, useRef } from 'react';
import { Upload, FileSpreadsheet, AlertCircle, Loader2 } from 'lucide-react';

interface EmptyStateProps {
  onLoadSample: () => void;
  onUploadFile: (file: File) => void;
  isLoading: boolean;
  errorMessage: string | null;
  onClearError: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  onLoadSample,
  onUploadFile,
  isLoading,
  errorMessage,
  onClearError,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      onClearError();
      onUploadFile(file);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      onClearError();
      onUploadFile(file);
    }
  };

  return (
    <div className="empty-state-wrapper">
      {errorMessage && (
        <div className="alert-banner error" role="alert">
          <AlertCircle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
          <div>
            <strong>Validation Error:</strong> {errorMessage}
          </div>
        </div>
      )}

      <div className="empty-state-card">
        <div className="empty-header">
          <div className="app-label">InsightDesk • Sales Analytics</div>
          <h1>Analyze a sales dataset</h1>
          <p>
            Upload your sales transaction CSV or initialize with the bundled benchmark dataset to generate deterministic revenue metrics, product rankings, and analytical findings.
          </p>
        </div>

        {/* Drag and Drop Zone */}
        <div
          className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isLoading && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              fileInputRef.current?.click();
            }
          }}
          aria-label="Upload CSV File"
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".csv"
            style={{ display: 'none' }}
            disabled={isLoading}
          />
          {isLoading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
              <Loader2 size={24} className="badge-icon" style={{ animation: 'spin 1s linear infinite' }} />
              <span className="dropzone-label">Computing deterministic analytics...</span>
              <span className="dropzone-subtext">Executing Pandas profiling on backend</span>
            </div>
          ) : (
            <>
              <Upload size={22} className="dropzone-icon" />
              <div className="dropzone-label">Drop CSV file here, or click to browse</div>
              <div className="dropzone-subtext">Supports standard UTF-8 CSV datasets up to 25 MB</div>
            </>
          )}
        </div>

        <div className="empty-actions-divider">or</div>

        {/* Sample Data Loader */}
        <div className="sample-loader-box">
          <div className="sample-loader-info">
            <h4>Load benchmark sales dataset</h4>
            <p>1,500 B2B sales records spanning all 12 months with multi-region transactions</p>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={onLoadSample}
            disabled={isLoading}
          >
            <FileSpreadsheet size={14} />
            <span>Load sample data</span>
          </button>
        </div>

        {/* Requirements Footer */}
        <div className="schema-requirements-note">
          <strong>CSV Requirements:</strong> Must contain numerical sales data. Expected columns include{' '}
          <span className="mono">revenue</span> (or both <span className="mono">quantity</span> and{' '}
          <span className="mono">unit_price</span>). Standard attributes such as <span className="mono">order_id</span>,{' '}
          <span className="mono">order_date</span>, <span className="mono">product_name</span>, and{' '}
          <span className="mono">region</span> enable complete dimensional reporting.
        </div>
      </div>
    </div>
  );
};
