import json
import re

from app.llm.provider_factory import ProviderFactory
from app.tools.git_diff_tool import GitDiffTool
from app.tools.code_analysis_tool import CodeAnalysisTool
from app.tools.security_analysis_tool import SecurityAnalysisTool
from app.tools.test_runner_tool import TestRunnerTool


class ReviewOrchestrator:
    def __init__(self, provider_name="openai", llm=None):
        self.git_diff_tool = GitDiffTool()
        self.code_analysis_tool = CodeAnalysisTool()
        self.security_analysis_tool = SecurityAnalysisTool()
        self.test_runner_tool = TestRunnerTool()
        self.llm = llm if llm is not None else ProviderFactory.create(provider_name)

    def build_review_prompt(self, diff, code_findings, security_findings, test_results):
        return (
            "You are a senior code reviewer. Review the following pull request data.\n\n"
            "Return valid JSON only with exactly these keys: "
            "summary, suggested_fixes, validation_status.\n\n"
            f"Diff:\n{diff}\n\n"
            f"Code findings:\n{code_findings}\n\n"
            f"Security findings:\n{security_findings}\n\n"
            f"Test results:\n{test_results}\n\n"
            "summary: one crisp sentence.\n"
            "suggested_fixes: list of concise fix actions.\n"
            "validation_status: 'passed' if tests pass, otherwise 'failed'."
        )

    def parse_llm_review(self, raw_review):
        if not raw_review:
            return {}

        cleaned = raw_review.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start : end + 1])
                except json.JSONDecodeError:
                    return {}
            return {}

    def format_review_comment(self, review):
        suggested_fixes = "\n".join(
            f"- {item}" for item in review.get("suggested_fixes", [])
        )
        if not suggested_fixes:
            suggested_fixes = "- None"

        return (
            "## Code Review Summary\n\n"
            f"{review.get('summary', '')}\n\n"
            "### Suggested fixes\n"
            f"{suggested_fixes}\n\n"
            f"### Validation status\n{review.get('validation_status', 'failed')}"
        )

    def review(self):
        diff = self.git_diff_tool.get_diff()

        code_findings = self.code_analysis_tool.analyze_file(
            "app/services/student_service.py"
        )

        security_findings = (
            self.security_analysis_tool.analyze_file(
                "app/services/student_service.py"
            )
        )

        test_results = self.test_runner_tool.run_tests()
        prompt = self.build_review_prompt(
            diff,
            code_findings,
            security_findings,
            test_results,
        )

        raw_review = self.llm.generate(prompt)
        parsed_review = self.parse_llm_review(raw_review)

        review_result = {
            "diff": diff,
            "code_findings": code_findings,
            "security_findings": security_findings,
            "test_results": test_results,
            "summary": parsed_review.get("summary", ""),
            "suggested_fixes": parsed_review.get("suggested_fixes", []),
            "validation_status": parsed_review.get("validation_status", "failed"),
            "llm_review": parsed_review.get("summary", ""),
        }
        review_result["comment"] = self.format_review_comment(review_result)
        return review_result


if __name__ == "__main__":
    orchestrator = ReviewOrchestrator()

    review = orchestrator.review()

    print("=== CODE REVIEW ===")
    print()
    print("Changed code:")
    print(review["diff"])

    print()
    print("Code findings:")
    for finding in review["code_findings"]:
        print(finding)

    print()
    print("Security findings:")
    for finding in review["security_findings"]:
        print(finding)

    print()
    print("Tests passed:")
    print(review["test_results"]["passed"])