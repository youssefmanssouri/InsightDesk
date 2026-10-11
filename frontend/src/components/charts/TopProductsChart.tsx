import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import type { TopProduct } from '../../types/analytics';

interface TopProductsChartProps {
  products: TopProduct[];
}

export const TopProductsChart: React.FC<TopProductsChartProps> = ({ products }) => {
  if (!products || products.length === 0) {
    return (
      <div className="surface-panel">
        <div className="panel-header">
          <span className="panel-title">Top Products</span>
        </div>
        <div className="panel-body" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          No product identifiers present in the uploaded dataset.
        </div>
      </div>
    );
  }

  // Slice top 8 products for clean vertical layout
  const chartData = [...products].slice(0, 8).map(p => ({
    name: p.product_name,
    shortName: p.product_name.length > 24 ? `${p.product_name.slice(0, 22)}...` : p.product_name,
    revenue: p.revenue,
    units: p.units_sold,
    share: p.share_of_total_pct,
    category: p.category,
  })).reverse(); // Reverse for top items to display at top of horizontal chart

  const formatCurrencyAxis = (val: number) => {
    if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
    if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
    return `$${val}`;
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;
    const item = payload[0].payload;

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
        <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
          {item.name}
        </div>
        <div style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginBottom: 6 }}>
          Category: {item.category}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span style={{ color: 'var(--text-muted)' }}>Revenue:</span>
          <span style={{ fontWeight: 600, color: '#0f172a' }} className="tabular-nums">
            ${item.revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span style={{ color: 'var(--text-muted)' }}>Revenue Share:</span>
          <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }} className="tabular-nums">
            {item.share.toFixed(1)}% of total
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
          <span style={{ color: 'var(--text-muted)' }}>Units Sold:</span>
          <span style={{ fontWeight: 500, color: 'var(--text-secondary)' }} className="tabular-nums">
            {item.units.toLocaleString()}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="surface-panel">
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Top Products by Revenue</h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Highest grossing catalog items ranked by cumulative sales
          </p>
        </div>
      </div>
      <div className="panel-body" style={{ height: 320 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={chartData}
            margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis
              type="number"
              tickLine={false}
              axisLine={{ stroke: '#cbd5e1' }}
              tickFormatter={formatCurrencyAxis}
              tick={{ fontSize: 11, fill: '#64748b' }}
            />
            <YAxis
              type="category"
              dataKey="shortName"
              tickLine={false}
              axisLine={false}
              width={140}
              tick={{ fontSize: 11, fill: '#334155' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              dataKey="revenue"
              fill="#1e293b"
              radius={[0, 3, 3, 0]}
              maxBarSize={20}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
