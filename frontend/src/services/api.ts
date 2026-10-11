import type { AnalysisResponse, AskQuestionResponse, AiStatusResponse } from '../types/analytics';

const API_BASE_URL = '';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function checkBackendHealth(): Promise<{ status: string; has_active_dataset: boolean; ai_configured: boolean; ai_model: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) {
      throw new ApiError(`Backend health check failed (${res.status})`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Cannot connect to InsightDesk backend server. Ensure the backend is running on port 8000.');
  }
}

export async function checkAiStatus(): Promise<AiStatusResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/ai/status`);
    if (!res.ok) {
      throw new ApiError(`Failed to fetch AI configuration (${res.status})`, res.status);
    }
    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    return { configured: false, model: 'unknown' };
  }
}

export async function loadSampleDataset(): Promise<AnalysisResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/sample`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      const message = errBody.detail || `Server error (${res.status})`;
      throw new ApiError(message, res.status);
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Failed to communicate with backend server. Check that the API server is reachable.');
  }
}

export async function uploadDatasetCsv(file: File): Promise<AnalysisResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
      },
      body: formData,
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      const message = errBody.detail || `Upload failed with status code ${res.status}`;
      throw new ApiError(message, res.status);
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Failed to upload file to backend. Check network connection or file format.');
  }
}

export async function askAnalyticalQuestion(
  question: string,
  datasetId?: string
): Promise<AskQuestionResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        question: question.trim(),
        dataset_id: datasetId,
      }),
    });

    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      const message = errBody.detail || `Query failed with status code ${res.status}`;
      throw new ApiError(message, res.status);
    }

    return await res.json();
  } catch (err: unknown) {
    if (err instanceof ApiError) throw err;
    throw new ApiError('Failed to query AI Analyst. Check server connection or API key.');
  }
}
