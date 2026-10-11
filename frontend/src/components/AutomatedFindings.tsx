import React from 'react';
import { Info, TrendingUp, Compass, Award, BarChart3 } from 'lucide-react';
import type { AutomatedInsight } from '../types/analytics';

interface AutomatedFindingsProps {
  insights: AutomatedInsight[];
}

export const AutomatedFindings: React.FC<AutomatedFindingsProps> = ({ insights }) => {
  if (!insights || insights.length === 0) {
    return null;
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'growth':
        return <TrendingUp size={13} style={{ color: 'var(--color-success)' }} />;
      case 'performance':
        return <Award size={13} style={{ color: '#2563eb' }} />;
      case 'concentration':
        return <BarChart3 size={13} style={{ color: '#64748b' }} />;
      case 'outlier':
        return <Compass size={13} style={{ color: '#d97706' }} />;
      default:
        return <Info size={13} style={{ color: 'var(--text-muted)' }} />;
    }
  };

  return (
    <div className="surface-panel" style={{ marginBottom: 20 }}>
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Automated Findings</h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Programmatic business observations derived deterministically from dataset aggregations
          </p>
        </div>
      </div>

      <div className="panel-body">
        <div className="findings-container">
          {insights.map((item) => (
            <div key={item.id} className="finding-row">
              <div className="finding-badge">
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  {getCategoryIcon(item.category)}
                  {item.category}
                </span>
              </div>
              <div className="finding-content">
                <h4>{item.title}</h4>
                <p>{item.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
