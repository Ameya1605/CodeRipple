# Phase 11: Repository Health Scoring Dashboard

## Objective
Aggregate risk and analysis data into a high-level dashboard to provide engineering leaders with a "health score" for their repositories.

## Task List
1. [ ] **Health Scoring Engine**: Implement an algorithm to calculate a repository-level score based on:
    - Average fan-out of symbols.
    - Percentage of symbols on the critical path without tests.
    - Circular dependency density.
    - High-churn high-risk symbol count.
2. [ ] **Aggregated API**: Create `GET /api/v1/repos/{repo_id}/health` to return time-series health data.
3. [ ] **Trend Analysis**: Compare health scores across commits to identify "architectural decay".
4. [ ] **Leaderboard UI**: Create a React view showing health scores across all repositories in the organization.
5. [ ] **Exportable Reports**: (Optional) PDF/JSON export for monthly engineering reviews.

## UAT Criteria
- [ ] Dashboard shows a "Health Score" (0-100) for each repository.
- [ ] A "Top Risks" list identifies the 5 most problematic symbols in the repo.
- [ ] Graph shows the health trend over the last 30 days.
