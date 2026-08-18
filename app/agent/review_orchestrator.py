from app.tools.git_diff_tool import GitDiffTool
from app.tools.code_analysis_tool import CodeAnalysisTool
from app.tools.security_analysis_tool import SecurityAnalysisTool
from app.tools.test_runner_tool import TestRunnerTool


class ReviewOrchestrator:
    def __init__(self):
        self.git_diff_tool = GitDiffTool()
        self.code_analysis_tool = CodeAnalysisTool()
        self.security_analysis_tool = SecurityAnalysisTool()
        self.test_runner_tool = TestRunnerTool()

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

        return {
            "diff": diff,
            "code_findings": code_findings,
            "security_findings": security_findings,
            "test_results": test_results,
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