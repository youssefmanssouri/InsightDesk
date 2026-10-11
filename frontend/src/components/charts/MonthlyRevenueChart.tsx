import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import type { MonthlyTrend } from '../../types/analytics';

interface MonthlyRevenueChartProps {
  data: MonthlyTrend[];
}

export const MonthlyRevenueChart: React.FC<MonthlyRevenueChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="surface-panel">
        <div className="panel-header">
          <span className="panel-title">Monthly Revenue Trend</span>
        </div>
        <div className="panel-body" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          No monthly date-stamped records found in this dataset.
        </div>
      </div>
    );
  }

  const formatCurrencyAxis = (val: number) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
    return `$${val}`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;
    const item: MonthlyTrend = payload[0].payload;

    return (
      <div
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '8px 12px',
          boxShadow: 'var(--shadow-dropdown)',
          fontSize: '0.8rem',
        }}
      >
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
          {label}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span style={{ color: 'var(--text-muted)' }}>Revenue:</span>
          <span style={{ fontWeight: 600, color: '#2563eb' }} className="tabular-nums">
            ${item.revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span style={{ color: 'var(--text-muted)' }}>Orders:</span>
          <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }} className="tabular-nums">
            {item.order_count.toLocaleString()}
          </span>
        </div>
        {item.mom_growth_pct !== null && (
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginTop: 4, paddingTop: 4, borderTop: '1px dashed var(--border-subtle)' }}>
            <span style={{ color: 'var(--text-muted)' }}>MoM Growth:</span>
            <span
              style={{
                fontWeight: 600,
                color: item.mom_growth_pct >= 0 ? 'var(--color-success)' : 'var(--color-error)',
              }}
              className="tabular-nums"
            >
              {item.mom_growth_pct >= 0 ? `+${item.mom_growth_pct.toFixed(1)}%` : `${item.mom_growth_pct.toFixed(1)}%`}
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="surface-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Monthly Revenue & Order Volume</h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Aggregated gross revenue (bars) and sequential order counts (line)
          </p>
        </div>
      </div>
      <div className="panel-body" style={{ height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="month"
              tickLine={false}
              axisLine={{ stroke: '#cbd5e1' }}
              tick={{ fontSize: 11, fill: '#64748b' }}
            />
            {/* Primary Y Axis: Revenue */}
            <YAxis
              yAxisId="left"
              tickLine={false}
              axisLine={false}
              tickFormatter={formatCurrencyAxis}
              tick={{ fontSize: 11, fill: '#64748b' }}
              width={65}
            />
            {/* Secondary Y Axis: Orders */}
            <YAxis
              yAxisId="right"
              orientation="right"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              width={40}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              yAxisId="left"
              dataKey="revenue"
              fill="#2563eb"
              radius={[3, 3, 0, 0]}
              maxBarSize={48}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="order_count"
              stroke="#64748b"
              strokeWidth={1.5}
              dot={{ r: 2.5, fill: '#64748b' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
