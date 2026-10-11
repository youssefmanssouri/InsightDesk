import React from 'react';
import { Database, RefreshCw } from 'lucide-react';
import type { DatasetMeta } from '../types/analytics';

interface HeaderProps {
  meta: DatasetMeta | null;
  onChangeDataset: () => void;
  isLoading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ meta, onChangeDataset, isLoading }) => {
  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="header-brand">
          <span className="brand-title">InsightDesk</span>
          <span className="brand-subtitle">Sales Analytics</span>
        </div>

        {meta && (
          <div className="header-meta">
            <div className="dataset-badge" title={`Columns: ${meta.column_count}`}>
              <Database size={13} className="badge-icon" />
              <span>{meta.filename}</span>
              <span className="tabular-nums mono" style={{ color: 'var(--text-muted)' }}>
                ({meta.row_count.toLocaleString()} rows)
              </span>
            </div>

            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={onChangeDataset}
              disabled={isLoading}
              title="Upload another dataset or reload sample"
            >
              <RefreshCw size={12} />
              <span>Change dataset</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
