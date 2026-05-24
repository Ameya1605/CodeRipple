import React from 'react';
import ReactMarkdown from 'react-markdown';
import { RiskBadge } from './RiskBadge';
import type { RiskTier } from './RiskBadge';
import { Terminal, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';

interface TestGap {
  chunk_id: string;
  suggestion: string;
}

interface AnalysisPanelProps {
  status: string;
  streamedText: string;
  finalRiskTier?: RiskTier;
  testGaps?: TestGap[];
  requestId?: string;
  symbolId?: string;
}

export const AnalysisPanel = ({ status, streamedText, finalRiskTier, testGaps, requestId, symbolId }: AnalysisPanelProps) => {
  const isLoading = status !== 'Complete' && status !== 'Ready' && status !== 'DISCONNECTED';
  const [feedbackStatus, setFeedbackStatus] = React.useState<'idle' | 'submitted'>('idle');

  const submitFeedback = async (isCorrect: boolean) => {
    if (!requestId || !symbolId) return;

    try {
      await fetch(`${import.meta.env.VITE_API_URL}/api/v1/feedback/analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request_id: requestId,
          symbol_id: symbolId,
          is_correct: isCorrect,
          comments: isCorrect ? 'Confirmed by user' : 'Flagged as false positive'
        })
      });
      setFeedbackStatus('submitted');
    } catch (err) {
      console.error('Failed to submit feedback', err);
    }
  };

  return (
    <div className="glass-panel section-card" style={{ minHeight: 420 }}>
      <div className="section-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ padding: 10, borderRadius: 12, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <Terminal size={18} color="var(--accent-primary)" />
          </div>
          <div>
            <h3 className="section-title" style={{ margin: 0, fontSize: 18 }}>Analysis Reasoning</h3>
            <p className="section-subtitle" style={{ margin: 0 }}>Review AI-guided reasoning for the selected symbol.</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div className="status-chip">
            {isLoading ? (
              <Loader2 size={14} className="animate-spin" color="var(--accent-primary)" />
            ) : (
              <CheckCircle2 size={14} color="var(--tier-low)" />
            )}
            {status}
          </div>
          {finalRiskTier && <RiskBadge tier={finalRiskTier} />}
        </div>
      </div>

      <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: 18, padding: 22, border: '1px solid rgba(255,255,255,0.08)', minHeight: 240, marginBottom: 26 }}>
        <div className="markdown-body" style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.8 }}>
          <ReactMarkdown>{streamedText}</ReactMarkdown>
        </div>
      </div>

      {status === 'Complete' && feedbackStatus === 'idle' && (
        <div style={{ display: 'grid', gap: 14, padding: 20, background: 'rgba(255,255,255,0.03)', borderRadius: 18, border: '1px solid rgba(255,255,255,0.08)', marginBottom: 24 }}>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Is this analysis accurate?</span>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button
              onClick={() => submitFeedback(true)}
              className="btn-secondary"
              style={{ background: 'rgba(34, 197, 94, 0.12)', color: 'var(--tier-low)', borderColor: 'rgba(34, 197, 94, 0.2)' }}
            >
              <CheckCircle2 size={14} /> Yes, Correct
            </button>
            <button
              onClick={() => submitFeedback(false)}
              className="btn-secondary"
              style={{ background: 'rgba(239, 68, 68, 0.12)', color: 'var(--tier-critical)', borderColor: 'rgba(239, 68, 68, 0.2)' }}
            >
              <AlertTriangle size={14} /> False Positive
            </button>
          </div>
        </div>
      )}

      {feedbackStatus === 'submitted' && (
        <div style={{ padding: '16px 20px', background: 'rgba(34, 197, 94, 0.12)', borderRadius: 18, border: '1px solid rgba(82, 196, 26, 0.18)', marginBottom: 24, display: 'flex', alignItems: 'center', gap: 10, color: 'var(--tier-low)' }}>
          <CheckCircle2 size={16} /> Thank you for your feedback! The system has been updated.
        </div>
      )}

      {testGaps && testGaps.length > 0 && (
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <AlertTriangle size={18} color="var(--tier-high)" />
            <h4 style={{ margin: 0, fontSize: 15, color: 'var(--tier-high)', fontWeight: 600 }}>Recommended Test Coverage</h4>
          </div>
          <div style={{ display: 'grid', gap: 12 }}>
            {testGaps.map((gap, i) => (
              <div key={i} style={{ padding: 16, borderRadius: 16, background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', fontSize: 13, lineHeight: 1.7 }}>
                <div style={{ marginBottom: 8 }}>
                  <code style={{ color: 'var(--accent-primary)', background: 'rgba(56, 189, 248, 0.12)', padding: '4px 8px', borderRadius: 8, fontSize: 12, fontWeight: 700 }}>
                    {gap.chunk_id}
                  </code>
                </div>
                <div style={{ color: 'var(--text-secondary)' }}>{gap.suggestion}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
