from app.agent.review_orchestrator import ReviewOrchestrator
from app.llm.llm_provider import LLMProvider


class FakeLLMProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return (
            '{"summary": "Looks good overall, but naming and validation should be tightened.", '
            '"suggested_fixes": ["Rename variables to snake_case", "Keep marks validation centralized"], '
            '"validation_status": "passed"}'
        )


def test_review_orchestrator_uses_injected_llm(monkeypatch):
    monkeypatch.setattr(
        "app.agent.review_orchestrator.GitDiffTool.get_diff",
        lambda self: "diff --git a/x b/x\n+new code",
    )
    monkeypatch.setattr(
        "app.agent.review_orchestrator.CodeAnalysisTool.analyze_file",
        lambda self, path: [{"message": "Naming issue found"}],
    )
    monkeypatch.setattr(
        "app.agent.review_orchestrator.SecurityAnalysisTool.analyze_file",
        lambda self, path: [],
    )
    monkeypatch.setattr(
        "app.agent.review_orchestrator.TestRunnerTool.run_tests",
        lambda self: {"passed": True, "failed": 0},
    )

    orchestrator = ReviewOrchestrator(llm=FakeLLMProvider())
    review = orchestrator.review()

    assert review["llm_review"] == "Looks good overall, but naming and validation should be tightened."
    assert review["suggested_fixes"] == [
        "Rename variables to snake_case",
        "Keep marks validation centralized",
    ]
    assert review["validation_status"] == "passed"
    assert "diff --git" in review["diff"]
    assert review["code_findings"] == [{"message": "Naming issue found"}]
