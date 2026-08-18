from app.agent.review_orchestrator import ReviewOrchestrator
from app.llm.llm_provider import LLMProvider


class FakeLLMProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return "Test review summary from fake provider"


def test_review_orchestrator_uses_injected_llm(monkeypatch):
    monkeypatch.setattr(
        "app.agent.review_orchestrator.GitDiffTool.get_diff",
        lambda self: "diff --git a/x b/x\n+new code",
    )
    monkeypatch.setattr(
        "app.agent.review_orchestrator.CodeAnalysisTool.analyze_file",
        lambda self, path: ["Naming issue found"],
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

    assert review["llm_review"] == "Test review summary from fake provider"
    assert "diff --git" in review["diff"]
    assert review["code_findings"] == ["Naming issue found"]
