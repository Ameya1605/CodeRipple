from backend.query.response_validator import ValidatedResponse
from backend.bot.pr_commenter import PRCommenter

def test_pr_comment_template():
    val = ValidatedResponse(
        risk_tier="HIGH",
        summary="This change affects critical database pathways.",
        test_gap_suggestions=[
            {"chunk_id": "core.db.read", "suggestion": "Add test for empty result set"},
            {"chunk_id": "api.users.get", "suggestion": "Mock database failure"}
        ],
        hallucinations_stripped=True
    )
    
    md = PRCommenter.render_markdown(val)
    
    assert "⚠️ Dependency Impact Analysis: **HIGH RISK**" in md
    assert "This change affects critical database pathways." in md
    assert "`core.db.read`" in md
    assert "Mock database failure" in md
    assert "invalid code chunks" in md
