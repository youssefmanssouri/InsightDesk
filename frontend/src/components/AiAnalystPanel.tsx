import React, { useState, useEffect } from 'react';
import { Send, Loader2, CheckCircle2, AlertCircle, HelpCircle, ArrowRight, Lightbulb } from 'lucide-react';
import { askAnalyticalQuestion, ApiError } from '../services/api';
import type { AskQuestionResponse } from '../types/analytics';

interface AiAnalystPanelProps {
  datasetId?: string;
  isAiConfigured?: boolean;
}

const SUGGESTED_QUESTIONS = [
  'Which region generates the most revenue?',
  'What happened to revenue over the last few months?',
  'Which products contribute the most revenue?',
  'What should I investigate next?',
];

export const AiAnalystPanel: React.FC<AiAnalystPanelProps> = ({ datasetId }) => {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<AskQuestionResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Clean state reset whenever active dataset changes
  useEffect(() => {
    setResponse(null);
    setQuestion('');
    setErrorMessage(null);
  }, [datasetId]);

  const handleSubmit = async (qToAsk?: string) => {
    const activeQuestion = (qToAsk || question).trim();
    if (!activeQuestion || isLoading) return;

    if (qToAsk) {
      setQuestion(qToAsk);
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await askAnalyticalQuestion(activeQuestion, datasetId);
      setResponse(res);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to obtain analytical answer from AI backend.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="surface-panel" style={{ marginBottom: 20 }}>
      <div className="panel-header">
        <div>
          <h2 className="panel-title">Ask Your Data</h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>
            Natural language questions explained using verified Pandas metrics (Python calculates; AI explains)
          </p>
        </div>
        {response?.model_used && (
          <span className="dataset-badge" style={{ fontSize: '0.7rem' }}>
            Model: {response.model_used}
          </span>
        )}
      </div>

      <div className="panel-body">
        {/* Suggested Question Chips */}
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 6, fontWeight: 500 }}>
            Suggested analytical queries:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {SUGGESTED_QUESTIONS.map((sq) => (
              <button
                key={sq}
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => handleSubmit(sq)}
                disabled={isLoading}
                style={{ fontSize: '0.75rem', padding: '4px 8px' }}
              >
                <span>{sq}</span>
                <ArrowRight size={11} style={{ opacity: 0.7 }} />
              </button>
            ))}
          </div>
        </div>

        {/* Input and Submit Row */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about sales revenue, trends, top products, or regional performance..."
              maxLength={500}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '8px 12px',
                fontSize: '0.825rem',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'var(--bg-surface)',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
            />
            {question.length > 350 && (
              <span
                style={{
                  position: 'absolute',
                  right: 8,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  fontSize: '0.7rem',
                  color: 'var(--text-muted)',
                }}
              >
                {question.length}/500
              </span>
            )}
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => handleSubmit()}
            disabled={isLoading || !question.trim()}
          >
            {isLoading ? (
              <>
                <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Send size={13} />
                <span>Ask Analyst</span>
              </>
            )}
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="alert-banner error" role="alert" style={{ marginBottom: 12 }}>
            <AlertCircle size={15} style={{ flexShrink: 0, marginTop: 1 }} />
            <div>
              <strong>Error:</strong> {errorMessage}
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div
            style={{
              padding: '16px',
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: '0.8rem',
              color: 'var(--text-secondary)',
            }}
          >
            <Loader2 size={15} style={{ animation: 'spin 1s linear infinite', color: '#2563eb' }} />
            <span>Consulting verified Pandas calculations and synthesizing analysis...</span>
          </div>
        )}

        {/* Answer Output */}
        {response && !isLoading && (
          <div
            style={{
              backgroundColor: response.ai_configured ? 'var(--bg-surface)' : 'var(--color-warning-bg)',
              border: `1px solid ${response.ai_configured ? 'var(--border-subtle)' : 'var(--color-warning-border)'}`,
              borderRadius: 'var(--radius-sm)',
              padding: '14px 16px',
            }}
          >
            {/* Grounding Status Header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: 8,
                marginBottom: 10,
                borderBottom: '1px solid var(--border-subtle)',
                fontSize: '0.75rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {response.is_grounded ? (
                  <CheckCircle2 size={13} style={{ color: 'var(--color-success)' }} />
                ) : (
                  <HelpCircle size={13} style={{ color: 'var(--text-muted)' }} />
                )}
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {response.ai_configured ? 'Verified Analysis' : 'AI Unconfigured Notice'}
                </span>
                <span style={{ color: 'var(--text-muted)' }}>
                  {response.is_grounded ? '• Grounded strictly in computed metrics' : ''}
                </span>
              </div>
            </div>

            {/* Answer Text */}
            <div
              style={{
                fontSize: '0.85rem',
                lineHeight: 1.5,
                color: 'var(--text-primary)',
                marginBottom: response.observed_facts.length > 0 || response.recommendations.length > 0 ? 12 : 0,
              }}
            >
              {response.answer}
            </div>

            {/* Observed Facts */}
            {response.observed_facts.length > 0 && (
              <div
                style={{
                  marginTop: 10,
                  padding: '8px 12px',
                  backgroundColor: 'var(--bg-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    fontSize: '0.725rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    color: 'var(--text-muted)',
                    marginBottom: 4,
                  }}
                >
                  Observed Facts (From Computed Data):
                </div>
                <ul style={{ paddingLeft: 16, fontSize: '0.785rem', color: 'var(--text-secondary)' }}>
                  {response.observed_facts.map((fact, idx) => (
                    <li key={idx} style={{ marginBottom: 2 }}>
                      {fact}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommended Next Steps */}
            {response.recommendations.length > 0 && (
              <div
                style={{
                  marginTop: 8,
                  padding: '8px 12px',
                  backgroundColor: '#f8fafc',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px dashed var(--border-subtle)',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    fontSize: '0.725rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    color: '#2563eb',
                    marginBottom: 4,
                  }}
                >
                  <Lightbulb size={12} />
                  <span>Analytical Follow-ups & Next Steps:</span>
                </div>
                <ul style={{ paddingLeft: 16, fontSize: '0.785rem', color: 'var(--text-secondary)' }}>
                  {response.recommendations.map((rec, idx) => (
                    <li key={idx} style={{ marginBottom: 2 }}>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
