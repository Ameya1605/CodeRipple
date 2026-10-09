import React, { useState } from 'react';
import { apiClient } from '../api/client';
import { Database, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

interface RepoIndexerProps {
  onSuccess: (repoId: string) => void;
}

export const RepoIndexer: React.FC<RepoIndexerProps> = ({ onSuccess }) => {
  const [url, setUrl] = useState('');
  const [repoId, setRepoId] = useState('');
  const [status, setStatus] = useState<'idle' | 'indexing' | 'success' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newUrl = e.target.value;
    setUrl(newUrl);

    if (newUrl.includes('github.com')) {
      const parts = newUrl.split('/');
      if (parts.length > 4) {
        setRepoId(parts[parts.length - 1].replace('.git', ''));
      }
    }
  };

  const handleIndex = async () => {
    if (!url || !repoId) return;

    setStatus('indexing');
    setErrorMsg('');

    try {
      await apiClient.repos.index(repoId, { repo_id: repoId, url });
      setStatus('success');
      setTimeout(() => {
        onSuccess(repoId);
        setStatus('idle');
        setUrl('');
      }, 3000);
    } catch (err: any) {
      setStatus('error');
      setErrorMsg(err.message || 'Failed to start indexing');
    }
  };

  return (
    <div className="glass-panel section-card" style={{ marginBottom: '32px' }}>
      <div className="section-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ padding: '10px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.08)' }}>
            <Database size={20} color="#fff" />
          </div>
          <div>
            <h3 className="section-title" style={{ margin: 0, fontSize: 18 }}>Index New Repository</h3>
          </div>
        </div>
      </div>

      <p style={{ color: 'var(--text-secondary)', fontSize: 14, margin: '0 0 22px' }}>
        Paste a public GitHub URL to clone, AST parse, and vectorize its codebase into Sentinel AI.
      </p>

      <div className="control-grid">
        <div>
          <label className="input-label">GitHub repository URL</label>
          <input
            type="text"
            placeholder="https://github.com/username/repo"
            value={url}
            onChange={handleUrlChange}
            disabled={status === 'indexing' || status === 'success'}
            className="input-field"
          />
        </div>

        <div>
          <label className="input-label">Repository ID</label>
          <input
            type="text"
            placeholder="repo-id"
            value={repoId}
            onChange={(e) => setRepoId(e.target.value)}
            disabled={status === 'indexing' || status === 'success'}
            className="input-field"
          />
        </div>

        <button
          onClick={handleIndex}
          disabled={!url || !repoId || status === 'indexing' || status === 'success'}
          className="btn-primary"
          style={{ justifyContent: 'center' }}
        >
          {status === 'indexing' ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              Indexing...
            </>
          ) : status === 'success' ? (
            <>
              <CheckCircle2 size={18} /> Queued!
            </>
          ) : status === 'error' ? (
            <>Retry</>
          ) : (
            <>Index Repo</>
          )}
        </button>
      </div>

      {status === 'indexing' && (
        <div style={{ marginTop: '18px', color: 'var(--text-secondary)', fontSize: 13, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="feature-pill" style={{ padding: '8px' }} />
          Repository is being cloned and indexed. This may take a few minutes.
        </div>
      )}

      {status === 'error' && (
        <div style={{ marginTop: '18px', padding: '14px', background: 'var(--tier-high-bg)', color: 'var(--tier-high)', borderRadius: 12, border: '1px solid var(--tier-high-border)', display: 'flex', alignItems: 'center', gap: 10, fontSize: 14 }}>
          <AlertCircle size={16} />
          {errorMsg}
        </div>
      )}
    </div>
  );
};
