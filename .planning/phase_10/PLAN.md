# Phase 10: PR Bot Integration

## Objective
Integrate the analyzer into the PR workflow, providing automated impact reports as comments on GitHub and GitLab.

## Task List
1. [ ] **GitHub Webhook Handler**: Update `backend/api/webhooks.py` to handle `pull_request` events.
2. [ ] **Comment Generator**: Create a condensed, markdown-formatted version of the analysis report for PR comments.
3. [ ] **CI Integration**: Provide a `cli.py` command to run analysis in GitHub Actions/GitLab CI.
4. [ ] **Status Checks**: Post a "Failure" status check if a change is detected as "CRITICAL" risk without new tests.
5. [ ] **Feedback Loop**: Allow developers to "Approve" or "Dismiss" the AI's risk assessment via PR reactions or comments.

## UAT Criteria
- [ ] Opening a PR triggers a background analysis job.
- [ ] A GitHub comment appears with a summary table: Symbol, Risk, Blast Radius, Suggested Reviewer.
- [ ] Critical breaking changes block the PR merge via status checks.
