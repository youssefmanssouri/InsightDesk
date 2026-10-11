import React from 'react';
import type { CoreMetrics } from '../types/analytics';

interface KpiGridProps {
  metrics: CoreMetrics;
}

export const KpiGrid: React.FC<KpiGridProps> = ({ metrics }) => {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: val >= 1000000 ? 2 : 2,
    }).format(val);
  };

  const formatNumber = (val: number) => {
    return new Intl.NumberFormat('en-US').format(val);
  };

  const formatPercent = (val: number) => {
    return `${(val * 100).toFixed(1)}%`;
  };

  return (
    <div className="kpi-grid">
      <div className="kpi-card">
        <div className="kpi-title">Total Revenue</div>
        <div className="kpi-value tabular-nums">{formatCurrency(metrics.total_revenue)}</div>
        <div className="kpi-subtext">Net computed sales</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-title">Orders</div>
        <div className="kpi-value tabular-nums">{formatNumber(metrics.total_orders)}</div>
        <div className="kpi-subtext">Unique transactions</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-title">Average Order Value</div>
        <div className="kpi-value tabular-nums">{formatCurrency(metrics.average_order_value)}</div>
        <div className="kpi-subtext">Revenue per order</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-title">Units Sold</div>
        <div className="kpi-value tabular-nums">{formatNumber(metrics.total_units_sold)}</div>
        <div className="kpi-subtext">Total unit volume</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-title">Average Discount</div>
        <div className="kpi-value tabular-nums">{formatPercent(metrics.average_discount)}</div>
        <div className="kpi-subtext">Mean transaction markdown</div>
      </div>
    </div>
  );
};
