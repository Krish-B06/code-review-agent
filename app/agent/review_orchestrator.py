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
            f"Diff:\n{diff}\n\n"
            f"Code findings:\n{code_findings}\n\n"
            f"Security findings:\n{security_findings}\n\n"
            f"Test results:\n{test_results}\n\n"
            "Provide a concise review summary with three sections: "
            "Overall assessment, Risks, and Recommended next steps."
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
        llm_review = self.llm.generate(prompt)

        return {
            "diff": diff,
            "code_findings": code_findings,
            "security_findings": security_findings,
            "test_results": test_results,
            "llm_review": llm_review,
        }


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