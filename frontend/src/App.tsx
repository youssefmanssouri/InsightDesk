import React, { useState } from 'react';
import { Header } from './components/Header';
import { EmptyState } from './components/EmptyState';
import { ContextRibbon } from './components/ContextRibbon';
import { KpiGrid } from './components/KpiGrid';
import { MonthlyRevenueChart } from './components/charts/MonthlyRevenueChart';
import { TopProductsChart } from './components/charts/TopProductsChart';
import { RegionalPerformanceSection } from './components/RegionalPerformanceSection';
import { AutomatedFindings } from './components/AutomatedFindings';
import { AiAnalystPanel } from './components/AiAnalystPanel';
import { DataQualitySection } from './components/DataQualitySection';
import { loadSampleDataset, uploadDatasetCsv, ApiError } from './services/api';
import type { AnalysisResponse } from './types/analytics';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [data, setData] = useState<AnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleLoadSample = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const response = await loadSampleDataset();
      setData(response);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to load sample dataset. Check server connection.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadFile = async (file: File) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const response = await uploadDatasetCsv(file);
      setData(response);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to upload and analyze dataset.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangeDataset = () => {
    setData(null);
    setErrorMessage(null);
  };

  return (
    <>
      <Header
        meta={data ? data.dataset_meta : null}
        onChangeDataset={handleChangeDataset}
        isLoading={isLoading}
      />

      <main className="app-container">
        {errorMessage && data && (
          <div className="alert-banner error" role="alert">
            <AlertCircle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
            <div>
              <strong>Error:</strong> {errorMessage}
            </div>
          </div>
        )}

        {!data ? (
          <EmptyState
            onLoadSample={handleLoadSample}
            onUploadFile={handleUploadFile}
            isLoading={isLoading}
            errorMessage={errorMessage}
            onClearError={() => setErrorMessage(null)}
          />
        ) : (
          <div>
            {/* 1. Dataset Context */}
            <ContextRibbon meta={data.dataset_meta} quality={data.data_quality} />

            {/* 2. KPI Section */}
            <KpiGrid metrics={data.metrics} />

            {/* 3. Main Trend Analysis (Monthly Revenue & Orders) */}
            <div className="dashboard-grid">
              <MonthlyRevenueChart data={data.monthly_trends} />
            </div>

            {/* 4. Product Performance & 5. Regional Performance */}
            <div className="grid-two-columns">
              <TopProductsChart products={data.top_products} />
              <RegionalPerformanceSection data={data.regional_performance} />
            </div>

            {/* 6. Automated Findings (Deterministic Rule-Based Insights) */}
            <AutomatedFindings insights={data.automated_insights} />

            {/* 7. Grounded AI Analyst Panel */}
            <AiAnalystPanel datasetId={data.dataset_id} />

            {/* 8. Data Quality & Raw Preview */}
            <DataQualitySection
              quality={data.data_quality}
              previewRows={data.preview_rows}
            />
          </div>
        )}
      </main>
    </>
  );
};

export default App;
