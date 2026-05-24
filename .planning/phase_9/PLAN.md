# Phase 9: Blame-Aware Reviewer Attribution

## Objective
Identify the best human reviewers for a change based on who has the most "ownership" of the impacted dependents.

## Task List
1. [ ] **Git Blame Integration**: Use `git blame` to identify the authors who modified the lines of the most critical impacted dependents.
2. [ ] **Reviewer Scoring Engine**: Rank authors based on:
    - Recency of commits to the impacted file.
    - Total number of lines owned in the impacted symbol.
    - Historic "Risk Score" of their past PRs.
3. [ ] **Cross-Repo Ownership**: Resolve email/username mappings across different repositories.
4. [ ] **UI Integration**: Display "Recommended Reviewers" at the top of the impact analysis report.
5. [ ] **Slack/Teams Integration**: (Optional) Allow sending the analysis report directly to the recommended reviewers.

## UAT Criteria
- [ ] Analysis output includes a `recommended_reviewers` list with reasonings (e.g., "Modified `db_utils.py` 2 days ago").
- [ ] Reviewers are sorted by their "Ownership Score".
- [ ] GitHub usernames are resolved if available in the repo config.
