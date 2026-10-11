import React from 'react';
import { FileText, Calendar, Layers, ShieldCheck, AlertTriangle } from 'lucide-react';
import type { DatasetMeta, DataQualityReport } from '../types/analytics';

interface ContextRibbonProps {
  meta: DatasetMeta;
  quality: DataQualityReport;
}

export const ContextRibbon: React.FC<ContextRibbonProps> = ({ meta, quality }) => {
  const dateRangeDisplay = meta.date_range?.start && meta.date_range?.end
    ? `${meta.date_range.start} → ${meta.date_range.end}`
    : 'No temporal dates detected';

  return (
    <div className="context-ribbon">
      <div className="context-items">
        <div className="context-item">
          <FileText size={13} style={{ color: 'var(--text-muted)' }} />
          <span className="label">File:</span>
          <span className="value">{meta.filename}</span>
        </div>

        <div className="context-item">
          <Calendar size={13} style={{ color: 'var(--text-muted)' }} />
          <span className="label">Period:</span>
          <span className="value tabular-nums">{dateRangeDisplay}</span>
        </div>

        <div className="context-item">
          <Layers size={13} style={{ color: 'var(--text-muted)' }} />
          <span className="label">Records:</span>
          <span className="value tabular-nums">{meta.row_count.toLocaleString()} rows ({meta.column_count} cols)</span>
        </div>

        <div className="context-item">
          {quality.validation_status === 'valid' ? (
            <ShieldCheck size={13} style={{ color: 'var(--color-success)' }} />
          ) : (
            <AlertTriangle size={13} style={{ color: 'var(--color-warning)' }} />
          )}
          <span className="label">Data Completeness:</span>
          <span className="value tabular-nums">{quality.completeness_score.toFixed(1)}%</span>
        </div>
      </div>

      {quality.duplicate_rows > 0 && (
        <div style={{ fontSize: '0.75rem', color: 'var(--color-warning)' }}>
          {quality.duplicate_rows} duplicate rows detected
        </div>
      )}
    </div>
  );
};
