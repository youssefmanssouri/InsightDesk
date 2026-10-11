export interface DateRange {
  start: string | null;
  end: string | null;
}

export interface DatasetMeta {
  filename: string;
  row_count: number;
  column_count: number;
  date_range: DateRange | null;
}

export interface ColumnProfile {
  name: string;
  inferred_type: string;
  null_count: number;
  null_percentage: number;
}

export interface DataQualityReport {
  completeness_score: number;
  duplicate_rows: number;
  columns_profile: ColumnProfile[];
  validation_status: 'valid' | 'warning';
  validation_notes: string[];
}

export interface CoreMetrics {
  total_revenue: number;
  total_orders: number;
  average_order_value: number;
  total_units_sold: number;
  average_discount: number;
}

export interface MonthlyTrend {
  month: string;
  revenue: number;
  order_count: number;
  mom_growth_pct: number | null;
}

export interface TopProduct {
  product_id: string;
  product_name: string;
  category: string;
  revenue: number;
  units_sold: number;
  share_of_total_pct: number;
}

export interface RegionalPerformance {
  region: string;
  revenue: number;
  order_count: number;
  aov: number;
  share_of_total_pct: number;
}

export interface AutomatedInsight {
  id: string;
  category: string;
  title: string;
  description: string;
  metric_reference: string;
}

export type PreviewRow = Record<string, string | number | boolean | null>;

export interface AnalysisResponse {
  dataset_id: string;
  dataset_meta: DatasetMeta;
  data_quality: DataQualityReport;
  metrics: CoreMetrics;
  monthly_trends: MonthlyTrend[];
  top_products: TopProduct[];
  regional_performance: RegionalPerformance[];
  top5_revenue_concentration_pct: number;
  automated_insights: AutomatedInsight[];
  preview_rows: PreviewRow[];
}

export interface AskQuestionRequest {
  question: string;
  dataset_id?: string;
}

export interface AskQuestionResponse {
  answer: string;
  observed_facts: string[];
  recommendations: string[];
  is_grounded: boolean;
  model_used: string | null;
  ai_configured: boolean;
}

export interface AiStatusResponse {
  configured: boolean;
  model: string;
}
