import { useState, useEffect } from 'react';
import { useAnalysis } from '../hooks/useAnalysis';
import { CallGraphViewer } from '../components/CallGraphViewer';
import { AnalysisPanel } from '../components/AnalysisPanel';
import { ImpactMetrics } from '../components/ImpactMetrics';
import { RepoIndexer } from '../components/RepoIndexer';
import { SearchInput } from '../components/Input/SearchInput';
import type { RiskTier } from '../components/RiskBadge';
import { Shield, Zap, Info, Database, Activity, Server, Box, Sparkles } from 'lucide-react';
import { useNotification } from '../hooks/useNotification';
import LoadingSpinner from '../components/Loading/LoadingSpinner';
import { SkeletonCard } from '../components/Loading/Skeleton';

export const Dashboard = () => {
  const [query, setQuery] = useState('calculate_impact');
  const [repoId, setRepoId] = useState('core-api');
  const { state, triggerAnalysis } = useAnalysis();
  const notify = useNotification();
  const [systemHealth, setSystemHealth] = useState<any>(null);

  const suggestions = ['calculate_impact', 'resolve_dependency', 'refresh_pipeline', 'validate_schema', 'load_config'];

  useEffect(() => {
    fetch('/api/v1/health/codebase')
      .then(res => res.json())
      .then(data => setSystemHealth(data))
      .catch(err => console.error('Failed to fetch health:', err));
  }, []);

  const handleAnalyze = async () => {
    notify.info('Analysis started', 3000);
    await triggerAnalysis({
      chunk: {
        chunk_id: 'mock1',
        repo_id: repoId,
        file_path: 'utils.py',
        symbol_type: 'func',
        symbol_name: query || 'mock',
        qualified_name: query || 'mock',
        start_line: 1,
        end_line: 10,
        signature: 'def mock()',
        content: 'pass',
        language: 'python'
      },
      change_summary: 'Modified logic'
    });

    if (state.status === 'running' || state.status === 'queued') {
      notify.info('Analysis queued', 2500);
    } else if (state.status === 'complete') {
      notify.success('Analysis complete', 3000);
    }
  };

  const finalRiskTier = state.validation?.risk_tier as RiskTier | undefined;
  const testGaps = state.validation?.test_gap_suggestions || [];
  const panelStatus = state.status === 'running' ? state.currentStep : (state.status === 'complete' ? 'Complete' : state.status);
  const streamedText = state.streamedText;
  const hasRealGraph = state.graphData?.nodes?.length && state.graphData.nodes.length > 0;
  const displayNodes = hasRealGraph ? state.graphData!.nodes : [];
  const displayEdges = hasRealGraph ? state.graphData!.edges : [];
  const hasRealMetrics = state.result != null;
  const nodeCount = hasRealGraph ? displayNodes.length : 0;
  const edgeCount = hasRealGraph ? displayEdges.length : 0;

  let chartData: any[] = [];
  let riskDist: any[] = [];

  if (hasRealMetrics && state.result?.metrics) {
    // populate real metrics when available
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="brand">
          <div className="brand-row">
            <div className="brand-badge">
              <Shield size={24} color="#fff" />
            </div>
            <div>
              <h1>Sentinel AI</h1>
              <p>Real-time dependency impact and risk analysis for modern engineering teams.</p>
            </div>
          </div>
        </div>

        <div className="hero-card">
          <div className="section-header">
            <div>
              <h2 className="hero-title">Launch smarter impact scans</h2>
              <p className="hero-subtitle">Use adaptive repository indexing and symbol-level analysis to identify high-risk dependency changes before they reach production.</p>
            </div>
            <span className="feature-pill">
              <Sparkles size={16} /> Laptop-optimized layout
            </span>
          </div>

          <div className="hero-stats">
            <div className="hero-stat">
              <strong>{repoId}</strong>
              <span>Repository in focus</span>
            </div>
            <div className="hero-stat">
              <strong>{query}</strong>
              <span>Current analysis target</span>
            </div>
            <div className="hero-stat">
              <strong>{state.status?.toUpperCase() || 'IDLE'}</strong>
              <span>Pipeline state</span>
            </div>
            <div className="hero-stat">
              <strong>{nodeCount} / {edgeCount}</strong>
              <span>Graph nodes / edges</span>
            </div>
          </div>
        </div>
      </header>

      <div className="control-panel">
        <div className="section-header">
          <div>
            <h3 className="section-title">Analyze faster</h3>
            <p className="section-subtitle">Type a symbol and repo ID, then trigger a targeted impact scan.</p>
          </div>
          <span className="status-chip">Live preview</span>
        </div>

        <div className="control-grid">
          <div>
            <label className="input-label">Repository ID</label>
            <input
              type="text"
              value={repoId}
              onChange={e => setRepoId(e.target.value)}
              placeholder="core-api"
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">Symbol or function</label>
            <SearchInput
              value={query}
              onChange={setQuery}
              placeholder="Search symbol..."
              suggestions={suggestions}
              className="input-field"
            />
          </div>

          <button
            className="btn-primary"
            onClick={handleAnalyze}
            disabled={state.status === 'queued' || state.status === 'running'}
          >
            {state.status === 'running' ? (
              <>
                <LoadingSpinner size={16} inline />
                <span>Analyzing... {state.progress ?? 0}%</span>
              </>
            ) : (
              <>
                <Zap size={16} /> Analyze impact
              </>
            )}
          </button>
        </div>
      </div>

      <RepoIndexer onSuccess={(id) => setRepoId(id)} />

      <section className="dashboard-grid">
        <div className="dashboard-main">
          <section className="section-card">
            <div className="section-header">
              <div>
                <h2 className="section-title">Call Graph Blast Radius</h2>
                <p className="section-subtitle">Interactive dependency graph showing affected code across the repository.</p>
              </div>
              {hasRealGraph && <span className="status-chip">Interactive</span>}
            </div>

            {hasRealGraph ? (
              <CallGraphViewer nodes={displayNodes as any} edges={displayEdges} />
            ) : (
              <div className="glass-panel" style={{ minHeight: 420, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 18 }}>
                <Sparkles size={48} color="var(--text-tertiary)" />
                <p style={{ color: 'var(--text-secondary)', maxWidth: 420, textAlign: 'center' }}>Run an analysis to populate the blast radius graph and inspect how changes affect code dependencies.</p>
                <SkeletonCard />
              </div>
            )}
          </section>

          <section className="section-card">
            <div className="section-header">
              <div>
                <h2 className="section-title">Impact Analysis Results</h2>
                <p className="section-subtitle">AI-driven risk summaries, tests gaps, and source recommendations.</p>
              </div>
              <Info size={20} color="var(--text-secondary)" />
            </div>

            <AnalysisPanel
              status={panelStatus}
              streamedText={streamedText || 'Initiate analysis to see real-time AI reasoning...'}
              finalRiskTier={finalRiskTier}
              testGaps={testGaps}
              requestId={state.requestId || undefined}
              symbolId={query || 'mock'}
            />

            {state.status === 'error' && (
              <div className="panel-card" style={{ marginTop: 20, background: 'var(--tier-high-bg)', color: 'var(--tier-high)', border: '1px solid var(--tier-high-border)' }}>
                <strong>Error:</strong> {state.error}
              </div>
            )}
          </section>
        </div>

        <aside className="dashboard-side">
          <section className="section-card">
            <div className="section-header">
              <div>
                <h2 className="section-title">Metrics Overview</h2>
                <p className="section-subtitle">Summary charts that highlight risk distribution and fan-out impact.</p>
              </div>
            </div>

            {hasRealMetrics ? (
              <ImpactMetrics data={chartData} riskDistribution={riskDist} />
            ) : (
              <div className="glass-panel" style={{ padding: 32, textAlign: 'center', color: 'var(--text-secondary)' }}>
                Analysis required to compute metrics
              </div>
            )}
          </section>

          <section className="health-card">
            <div className="section-header">
              <div>
                <h2 className="section-title">System Health</h2>
                <p className="section-subtitle">Live status for platform services and processing nodes.</p>
              </div>
            </div>

            {systemHealth ? (
              <div>
                <div className="health-line">
                  <span className="health-text"><Database size={14} /> Neo4j</span>
                  <span className={systemHealth.checks?.neo4j?.status === 'ok' ? 'status-ok' : 'status-fail'}>{systemHealth.checks?.neo4j?.status?.toUpperCase() || 'UNKNOWN'}</span>
                </div>
                <div className="health-line">
                  <span className="health-text"><Box size={14} /> Qdrant Vector</span>
                  <span className={systemHealth.checks?.qdrant?.status === 'ok' ? 'status-ok' : 'status-fail'}>{systemHealth.checks?.qdrant?.status?.toUpperCase() || 'UNKNOWN'}</span>
                </div>
                <div className="health-line">
                  <span className="health-text"><Server size={14} /> Redis / Celery</span>
                  <span className={systemHealth.broker_connected ? 'status-ok' : 'status-fail'}>{systemHealth.broker_connected ? 'OK' : 'OFFLINE'}</span>
                </div>
                <div className="health-line">
                  <span className="health-text"><Activity size={14} /> Workers</span>
                  <span className={systemHealth.worker_online ? 'status-ok' : 'status-fail'}>{systemHealth.worker_online ? `ONLINE (${systemHealth.checks?.worker?.count})` : 'UNAVAILABLE'}</span>
                </div>
              </div>
            ) : (
              <div style={{ color: 'var(--text-secondary)', fontSize: 13 }}>Loading health metrics...</div>
            )}
          </section>
        </aside>
      </section>
    </div>
  );
};
