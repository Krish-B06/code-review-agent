import re
from pathlib import Path


class LocalReviewOrchestrator:
    """Intelligent code review using local analysis - no API keys required."""

    def __init__(self):
        from app.tools.git_diff_tool import GitDiffTool
        from app.tools.code_analysis_tool import CodeAnalysisTool
        from app.tools.security_analysis_tool import SecurityAnalysisTool
        from app.tools.test_runner_tool import TestRunnerTool

        self.git_diff_tool = GitDiffTool()
        self.code_analysis_tool = CodeAnalysisTool()
        self.security_analysis_tool = SecurityAnalysisTool()
        self.test_runner_tool = TestRunnerTool()

    def _analyze_code_patterns(self, filepath):
        """Intelligent pattern analysis for code quality."""
        findings = []
        try:
            with open(filepath, "r") as f:
                content = f.read()
                lines = content.split("\n")

            # Check for long methods
            method_pattern = r"def\s+(\w+)\s*\("
            methods = list(re.finditer(method_pattern, content))
            for i, method_match in enumerate(methods):
                start = content[:method_match.start()].count("\n")
                end = (
                    content[: methods[i + 1].start()].count("\n")
                    if i + 1 < len(methods)
                    else len(lines)
                )
                method_length = end - start
                if method_length > 20:
                    findings.append(
                        f"Method '{method_match.group(1)}' is {method_length} lines (consider breaking it down)"
                    )

            # Check for proper error handling
            if "except" in content and "except Exception" in content:
                findings.append("Avoid bare 'except Exception' - catch specific exceptions")

            # Check for type hints
            if "def " in content and "->" not in content:
                findings.append("Missing type hints on functions - add type annotations")

            # Check for docstrings
            if "def " in content and '"""' not in content and "'''" not in content:
                findings.append("Add docstrings to functions for better documentation")

            # Check for hardcoded values
            if re.search(r'="[0-9]{2,}"|=[0-9]{3,}', content):
                findings.append("Consider extracting magic numbers to constants")

        except Exception:
            pass

        return findings

    def _analyze_diff_quality(self, diff):
        """Analyze the diff for architectural concerns."""
        suggestions = []

        if "TODO" in diff or "FIXME" in diff:
            suggestions.append("Remove TODO/FIXME comments - implement or open an issue")

        if re.search(r"import \*", diff):
            suggestions.append("Avoid 'import *' - use explicit imports")

        if re.search(r"print\(", diff):
            suggestions.append("Replace print() with proper logging")

        large_file_additions = len([l for l in diff.split("\n") if l.startswith("+")])
        if large_file_additions > 100:
            suggestions.append(
                f"Large diff with {large_file_additions} additions - consider breaking into smaller PRs"
            )

        return suggestions

    def format_review_comment(self, review):
        suggested_fixes = "\n".join(
            f"- {item}" for item in review.get("suggested_fixes", [])
        )
        if not suggested_fixes:
            suggested_fixes = "- Looks good! No issues detected."

        code_findings = review.get("code_findings", [])
        security_findings = review.get("security_findings", [])

        code_section = (
            "- " + "\n- ".join(code_findings)
            if code_findings
            else "- No code quality issues"
        )
        security_section = (
            "- " + "\n- ".join(security_findings)
            if security_findings
            else "- No security concerns detected"
        )

        return (
            "## Code Review Summary\n\n"
            f"{review.get('summary', '')}\n\n"
            "### Code Quality\n"
            f"{code_section}\n\n"
            "### Security Analysis\n"
            f"{security_section}\n\n"
            "### Recommendations\n"
            f"{suggested_fixes}\n\n"
            f"### Tests\n**Status:** {review.get('validation_status', 'unknown')}"
        )

    def review(self):
        """Perform intelligent local code review."""
        diff = self.git_diff_tool.get_diff()

        # Standard analysis
        code_findings = self.code_analysis_tool.analyze_file(
            "app/services/student_service.py"
        )
        security_findings = self.security_analysis_tool.analyze_file(
            "app/services/student_service.py"
        )
        test_results = self.test_runner_tool.run_tests()

        # Intelligent pattern analysis
        pattern_findings = self._analyze_code_patterns("app/services/student_service.py")
        diff_suggestions = self._analyze_diff_quality(diff)

        all_code_findings = list(set(code_findings + pattern_findings))
        all_suggestions = diff_suggestions.copy()

        tests_passed = test_results.get("passed", False)
        status = "passed" if tests_passed else "failed"

        # Build intelligent summary
        issues_count = len(all_code_findings) + len(security_findings)
        if issues_count == 0 and tests_passed:
            summary = "✅ PR looks good! All tests pass with no code quality issues."
        elif issues_count == 0 and not tests_passed:
            summary = "⚠️ Tests are failing - please fix before merging."
        else:
            summary = (
                f"Found {issues_count} code/security issue(s) to address. "
                f"Tests {'passed' if tests_passed else 'failed'}."
            )

        # Add actionable suggestions
        if not all_suggestions:
            if issues_count == 0:
                all_suggestions = ["Code looks well-structured and follows best practices"]
            else:
                all_suggestions = ["Address the issues listed above before merging"]

        review_result = {
            "diff": diff,
            "code_findings": all_code_findings,
            "security_findings": security_findings,
            "test_results": test_results,
            "summary": summary,
            "suggested_fixes": all_suggestions,
            "validation_status": status,
        }
        review_result["comment"] = self.format_review_comment(review_result)
        return review_result
