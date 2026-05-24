const BASE_URL = '/api/v1';

export const apiClient = {
  health: {
    getCodebase: () => fetch(`${BASE_URL}/health/codebase`).then(r => r.json())
  },
  repos: {
    register: (data: any) => fetch(`${BASE_URL}/repos`, {
      method: 'POST', body: JSON.stringify(data), headers: {'Content-Type': 'application/json'}
    }).then(r => r.json()),
    index: (repoId: string, data: any) => fetch(`${BASE_URL}/repos/${repoId}/index`, {
      method: 'POST', body: JSON.stringify(data), headers: {'Content-Type': 'application/json'}
    }).then(r => r.json()),
    status: (repoId: string, jobId: string) => fetch(`${BASE_URL}/repos/${repoId}/status?job_id=${jobId}`).then(r => r.json())
  },
  analyze: {
    symbol: (data: any) => fetch(`${BASE_URL}/analyze/symbol`, {
      method: 'POST', body: JSON.stringify(data), headers: {'Content-Type': 'application/json'}
    }).then(r => r.json()),
    diff: (data: any) => fetch(`${BASE_URL}/analyze/diff`, {
      method: 'POST', body: JSON.stringify(data), headers: {'Content-Type': 'application/json'}
    }).then(r => r.json())
  },
  symbols: {
    search: (q: string) => fetch(`${BASE_URL}/symbols/search?q=${encodeURIComponent(q)}`).then(r => r.json())
  },
  graph: {
    blastRadius: (qname: string) => fetch(`${BASE_URL}/graph/blast-radius?qname=${encodeURIComponent(qname)}`).then(r => r.json())
  }
};
