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
        """Intelligent pattern analysis with exact line numbers."""
        findings = []
        try:
            with open(filepath, "r") as f:
                content = f.read()
                lines = content.split("\n")

            # Check for long methods with exact locations
            method_pattern = r"def\s+(\w+)\s*\("
            methods = list(re.finditer(method_pattern, content))
            for i, method_match in enumerate(methods):
                start_line = content[: method_match.start()].count("\n") + 1
                end_line = (
                    content[: methods[i + 1].start()].count("\n") + 1
                    if i + 1 < len(methods)
                    else len(lines)
                )
                method_length = end_line - start_line
                if method_length > 20:
                    findings.append(
                        f"**{filepath}:{start_line}-{end_line}** | Method `{method_match.group(1)}()` is {method_length} lines - refactor into smaller functions"
                    )

            # Check for missing type hints on specific functions
            for line_num, line in enumerate(lines, 1):
                if re.match(r"\s*def\s+\w+\s*\(", line):
                    if "->" not in line and "def " in line:
                        func_name = re.search(r"def\s+(\w+)", line)
                        if func_name:
                            findings.append(
                                f"**{filepath}:{line_num}** | Function `{func_name.group(1)}()` missing return type hint: `-> <type>`"
                            )

            # Check for bare except blocks with exact line
            for line_num, line in enumerate(lines, 1):
                if re.search(r"except\s*:", line):
                    findings.append(
                        f"**{filepath}:{line_num}** | Bare `except:` clause - specify exception type: `except ValueError as e:`"
                    )
                elif "except Exception" in line:
                    findings.append(
                        f"**{filepath}:{line_num}** | Generic `Exception` catch - catch specific exceptions instead"
                    )

            # Check for missing docstrings
            for line_num, line in enumerate(lines, 1):
                if re.match(r"\s*def\s+\w+", line):
                    # Check if next non-empty line is a docstring
                    next_lines = lines[line_num : min(line_num + 3, len(lines))]
                    has_docstring = any('"""' in l or "'''" in l for l in next_lines)
                    if not has_docstring:
                        func_name = re.search(r"def\s+(\w+)", line)
                        if func_name:
                            findings.append(
                                f"**{filepath}:{line_num}** | Function `{func_name.group(1)}()` missing docstring"
                            )

        except Exception as e:
            pass

        return findings

    def _analyze_diff_quality(self, diff):
        """Analyze the diff for architectural concerns with locations."""
        suggestions = []

        for line_num, line in enumerate(diff.split("\n"), 1):
            # TODO/FIXME comments
            if ("TODO" in line or "FIXME" in line) and line.startswith("+"):
                suggestions.append(
                    f"**Diff line {line_num}** | Remove TODO/FIXME - implement now or open a GitHub issue"
                )

            # Import star
            if "import *" in line and line.startswith("+"):
                module = re.search(r"from\s+(\S+)\s+import\s+\*", line)
                if module:
                    suggestions.append(
                        f"**Diff line {line_num}** | Avoid `import *` from `{module.group(1)}` - use explicit imports"
                    )

            # Print statements
            if "print(" in line and line.startswith("+"):
                suggestions.append(
                    f"**Diff line {line_num}** | Replace `print()` with logging module: `import logging; logging.info(...)`"
                )

        large_file_additions = len([l for l in diff.split("\n") if l.startswith("+")])
        if large_file_additions > 100:
            suggestions.append(
                f"**PR Size** | Large diff with {large_file_additions} additions - consider breaking into multiple smaller PRs"
            )

        return suggestions

    def format_review_comment(self, review):
        suggested_fixes = "\n".join(
            f"- {item}" for item in review.get("suggested_fixes", [])
        )
        if not suggested_fixes:
            suggested_fixes = "- ✅ No issues - code looks good!"

        code_findings = review.get("code_findings", [])
        security_findings = review.get("security_findings", [])

        code_section = (
            "\n".join(f"- {f}" for f in code_findings)
            if code_findings
            else "- ✅ No code quality issues detected"
        )
        security_section = (
            "\n".join(f"- {f}" for f in security_findings)
            if security_findings
            else "- ✅ No security concerns detected"
        )

        return (
            "## Code Review Summary\n\n"
            f"{review.get('summary', '')}\n\n"
            "### Code Quality Issues\n"
            f"{code_section}\n\n"
            "### Security Analysis\n"
            f"{security_section}\n\n"
            "### Recommendations\n"
            f"{suggested_fixes}\n\n"
            f"### Test Status\n**{review.get('validation_status', 'unknown').upper()}** ✅"
        )

    def review(self):
        """Perform intelligent local code review with precise locations."""
        diff = self.git_diff_tool.get_diff()

        # Detailed analysis with line numbers
        code_findings = self.code_analysis_tool.analyze_file(
            "app/services/student_service.py"
        )
        pattern_findings = self._analyze_code_patterns("app/services/student_service.py")
        security_findings = self.security_analysis_tool.analyze_file(
            "app/services/student_service.py"
        )
        diff_suggestions = self._analyze_diff_quality(diff)
        test_results = self.test_runner_tool.run_tests()

        # Combine findings (remove duplicates but keep detailed versions)
        all_code_findings = pattern_findings if pattern_findings else code_findings
        all_suggestions = diff_suggestions.copy()

        tests_passed = test_results.get("passed", False)
        status = "passed" if tests_passed else "failed"

        # Build intelligent summary
        issues_count = len(all_code_findings) + len(security_findings)
        if issues_count == 0 and tests_passed:
            summary = "✅ **Approved** - Code is clean, tests pass, no issues found."
        elif issues_count == 0 and not tests_passed:
            summary = "❌ **Tests failing** - Fix test failures before merging."
        else:
            summary = f"⚠️ **Review Required** - Found {issues_count} issue(s). Details below."

        # Add actionable suggestions
        if not all_suggestions:
            if issues_count == 0:
                all_suggestions = ["Code meets quality standards"]
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
