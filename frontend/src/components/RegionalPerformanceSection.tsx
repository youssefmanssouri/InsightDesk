import React from 'react';
import type { RegionalPerformance } from '../types/analytics';

interface RegionalPerformanceSectionProps {
  data: RegionalPerformance[];
}

export const RegionalPerformanceSection: React.FC<RegionalPerformanceSectionProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="surface-panel">
        <div className="panel-header">
          <span className="panel-title">Regional Performance</span>
        </div>
        <div className="panel-body" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          No regional breakdown attributes available.
        </div>
      </div>
    );
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 2,
    }).format(val);
  };

  return (
    <div className="surface-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Regional Performance Breakdown</h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Territory contribution, order volume, and geographic AOV
          </p>
        </div>
      </div>

      <div className="data-table-wrapper">
        <table className="clean-table">
          <thead>
            <tr>
              <th>Region</th>
              <th className="numeric">Revenue</th>
              <th className="numeric">Orders</th>
              <th className="numeric">AOV</th>
              <th className="numeric">Share</th>
              <th style={{ width: '120px' }}>Contribution</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.region}>
                <td style={{ fontWeight: 500 }}>{row.region}</td>
                <td className="numeric tabular-nums" style={{ fontWeight: 600 }}>
                  {formatCurrency(row.revenue)}
                </td>
                <td className="numeric tabular-nums">{row.order_count.toLocaleString()}</td>
                <td className="numeric tabular-nums">{formatCurrency(row.aov)}</td>
                <td className="numeric tabular-nums">{row.share_of_total_pct.toFixed(1)}%</td>
                <td>
                  <div
                    style={{
                      height: '6px',
                      backgroundColor: 'var(--bg-muted)',
                      borderRadius: '2px',
                      overflow: 'hidden',
                      width: '100%',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${Math.min(100, Math.max(0, row.share_of_total_pct))}%`,
                        backgroundColor: '#2563eb',
                        borderRadius: '2px',
                      }}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
