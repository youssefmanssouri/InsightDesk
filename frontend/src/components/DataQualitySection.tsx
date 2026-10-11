import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2, AlertTriangle, Table } from 'lucide-react';
import type { DataQualityReport, PreviewRow } from '../types/analytics';

interface DataQualitySectionProps {
  quality: DataQualityReport;
  previewRows: PreviewRow[];
}

export const DataQualitySection: React.FC<DataQualitySectionProps> = ({ quality, previewRows }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'schema' | 'preview'>('schema');
  const [page, setPage] = useState(0);
  const pageSize = 10;

  const totalPages = Math.ceil(previewRows.length / pageSize);
  const displayedRows = previewRows.slice(page * pageSize, (page + 1) * pageSize);
  const columnHeaders = previewRows.length > 0 ? Object.keys(previewRows[0]) : [];

  return (
    <div className="surface-panel" style={{ marginBottom: 40 }}>
      <button
        type="button"
        className="panel-header"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          background: 'none',
          border: 'none',
          borderBottom: isOpen ? '1px solid var(--border-subtle)' : 'none',
          cursor: 'pointer',
          textAlign: 'left',
          padding: '12px 16px',
        }}
        aria-expanded={isOpen}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          <div>
            <h2 className="panel-title" style={{ display: 'inline' }}>
              Data Quality & Dataset Inspector
            </h2>
            <span style={{ fontSize: '0.775rem', color: 'var(--text-muted)', marginLeft: 8 }}>
              ({quality.completeness_score.toFixed(1)}% complete, {quality.columns_profile.length} columns)
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {quality.validation_status === 'valid' ? (
            <span className="dataset-badge" style={{ color: 'var(--color-success)', borderColor: 'var(--color-success-border)' }}>
              <CheckCircle2 size={12} />
              Healthy Schema
            </span>
          ) : (
            <span className="dataset-badge" style={{ color: 'var(--color-warning)', borderColor: 'var(--color-warning-border)' }}>
              <AlertTriangle size={12} />
              Warnings
            </span>
          )}
        </div>
      </button>

      {isOpen && (
        <div className="panel-body">
          {/* Health Summary Strip */}
          <div className="quality-summary-strip">
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Completeness:</span>{' '}
              <strong className="tabular-nums">{quality.completeness_score.toFixed(2)}%</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Duplicate Rows:</span>{' '}
              <strong className="tabular-nums">{quality.duplicate_rows}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Columns Profiled:</span>{' '}
              <strong className="tabular-nums">{quality.columns_profile.length}</strong>
            </div>
          </div>

          {quality.validation_notes.length > 0 && (
            <div className="alert-banner warning" style={{ marginBottom: 14 }}>
              <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                {quality.validation_notes.map((note, idx) => (
                  <div key={idx}>{note}</div>
                ))}
              </div>
            </div>
          )}

          {/* Sub-tabs: Column Schema vs Raw Preview */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button
              type="button"
              className={`btn btn-sm ${activeTab === 'schema' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('schema')}
            >
              Column Schema ({quality.columns_profile.length})
            </button>
            <button
              type="button"
              className={`btn btn-sm ${activeTab === 'preview' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setActiveTab('preview')}
            >
              <Table size={12} />
              Raw Preview (First 50 Rows)
            </button>
          </div>

          {activeTab === 'schema' ? (
            <div className="data-table-wrapper">
              <table className="clean-table">
                <thead>
                  <tr>
                    <th>Column Name</th>
                    <th>Inferred Type</th>
                    <th className="numeric">Missing Count</th>
                    <th className="numeric">Missing %</th>
                  </tr>
                </thead>
                <tbody>
                  {quality.columns_profile.map((col) => (
                    <tr key={col.name}>
                      <td className="mono" style={{ fontWeight: 500 }}>{col.name}</td>
                      <td>
                        <span className="dataset-badge" style={{ fontSize: '0.7rem' }}>
                          {col.inferred_type}
                        </span>
                      </td>
                      <td className="numeric tabular-nums">{col.null_count.toLocaleString()}</td>
                      <td className="numeric tabular-nums">
                        {col.null_percentage > 0 ? (
                          <span style={{ color: 'var(--color-warning)' }}>
                            {col.null_percentage.toFixed(1)}%
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>0.0%</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div>
              <div className="data-table-wrapper" style={{ maxHeight: 320 }}>
                <table className="clean-table">
                  <thead>
                    <tr>
                      {columnHeaders.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {displayedRows.map((row, rowIdx) => (
                      <tr key={rowIdx}>
                        {columnHeaders.map((col) => (
                          <td key={col} className="tabular-nums" style={{ fontSize: '0.75rem' }}>
                            {row[col] !== null && row[col] !== undefined ? String(row[col]) : '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {totalPages > 1 && (
                <div className="table-pagination">
                  <span>
                    Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, previewRows.length)} of {previewRows.length} sample rows
                  </span>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setPage((p) => Math.max(0, p - 1))}
                      disabled={page === 0}
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                      disabled={page >= totalPages - 1}
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
