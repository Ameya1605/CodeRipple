# Phase 12: Learning Feedback Loop & Metrics

## Objective
Implement a reinforcement learning loop based on human feedback to improve the accuracy of risk assessments and reranking.

## Task List
1. [x] **Feedback Persistence**: Update `backend/api/feedback.py` to store human "Approve/Reject" signals on AI-generated reports.
2. [x] **Ranking Optimization**: Periodically adjust reranker weights (`RERANK_VECTOR_W`, etc.) based on which symbols users flagged as "False Positives".
3. [x] **Precision/Recall Tracking**: Implement an internal dashboard to track the AI's accuracy over time.
4. [x] **Few-Shot Ingestion**: Automatically inject "Corrected Examples" into the analysis prompt to prevent repeat mistakes.
5. [x] **Final Project Audit**: Comprehensive test pass and documentation update for v2.0.0.

## UAT Criteria
- [x] Users can click "This analysis is correct" or "This is a false positive" in the UI.
- [x] Analysis accuracy metrics are visible in the Health Dashboard (via `/api/v1/health/accuracy`).
- [x] The system demonstrates "learning" behavior (e.g., stops flagging a specific known-safe pattern after multiple dismissals by using corrected examples in few-shot prompt).
