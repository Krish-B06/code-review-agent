import re
from pathlib import Path


class LocalReviewOrchestrator:
    """Run a local, tool-based code review."""

    def __init__(self):
        """Initialize the code review tools."""
        from app.tools.git_diff_tool import GitDiffTool
        from app.tools.code_analysis_tool import CodeAnalysisTool
        from app.tools.security_analysis_tool import SecurityAnalysisTool
        from app.tools.test_runner_tool import TestRunnerTool

        self.git_diff_tool = GitDiffTool()
        self.code_analysis_tool = CodeAnalysisTool()
        self.security_analysis_tool = SecurityAnalysisTool()
        self.test_runner_tool = TestRunnerTool()

    def _group_and_summarize_findings(self, findings):
        """Group common findings to reduce review noise."""
        if not findings:
            return []

        grouped = {}

        for finding in findings:
            if "missing return type hint" in finding:
                grouped.setdefault("Missing Type Hints", []).append(
                    self._extract_function_name(finding)
                )

            elif "missing docstring" in finding:
                grouped.setdefault("Missing Docstrings", []).append(
                    self._extract_function_name(finding)
                )

        summary = []

        if "Missing Type Hints" in grouped:
            functions = ", ".join(
                sorted(set(grouped["Missing Type Hints"]))
            )
            summary.append(
                f"**Missing return type hints**: {functions}"
            )

        if "Missing Docstrings" in grouped:
            functions = ", ".join(
                sorted(set(grouped["Missing Docstrings"]))
            )
            summary.append(
                f"**Missing docstrings**: {functions}"
            )

        return summary

    @staticmethod
    def _extract_function_name(finding):
        """Extract a function name from a finding."""
        if "`" in finding:
            parts = finding.split("`")
            if len(parts) > 1:
                return parts[1]

        return "unknown"

    def _analyze_code_patterns(self, filepath):
        """Analyze a Python file for common code-quality issues."""
        findings = []

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()

            lines = content.splitlines()

            findings.extend(
                self._check_long_methods(
                    filepath,
                    content,
                    lines,
                )
            )

            findings.extend(
                self._check_missing_type_hints(lines)
            )

            findings.extend(
                self._check_exception_handling(lines)
            )

            findings.extend(
                self._check_missing_docstrings(lines)
            )

        except (OSError, UnicodeDecodeError):
            # Ignore files that cannot be read.
            pass

        return findings

    def _check_long_methods(self, filepath, content, lines):
        """Find methods that are longer than 20 lines."""
        findings = []
        method_pattern = r"def\s+(\w+)\s*\("
        methods = list(re.finditer(method_pattern, content))

        for index, method_match in enumerate(methods):
            start_line = (
                content[:method_match.start()].count("\n") + 1
            )

            if index + 1 < len(methods):
                end_line = (
                    content[:methods[index + 1].start()].count("\n")
                    + 1
                )
            else:
                end_line = len(lines)

            method_length = end_line - start_line

            if method_length > 20:
                findings.append(
                    f"**{filepath}:{start_line}-{end_line}** | "
                    f"`{method_match.group(1)}()` is "
                    f"{method_length} lines long."
                )

        return findings

    def _check_missing_type_hints(self, lines):
        """Find functions without return type hints."""
        functions = []

        for line in lines:
            if re.match(r"\s*def\s+\w+\s*\(", line):
                if "->" not in line:
                    match = re.search(r"def\s+(\w+)", line)

                    if match:
                        functions.append(match.group(1))

        if not functions:
            return []

        return [
            "**Missing return type hints** | "
            f"Add return types to: `{', '.join(functions)}`"
        ]

    def _check_exception_handling(self, lines):
        """Find bare or overly broad exception handlers."""
        issues = []

        for line_number, line in enumerate(lines, 1):
            if re.search(r"except\s*:", line):
                issues.append(f"line {line_number}")

            elif "except Exception" in line:
                issues.append(
                    f"line {line_number} (generic Exception)"
                )

        if not issues:
            return []

        return [
            "**Exception handling** | "
            f"Review exception handling at {', '.join(issues)}"
        ]

    def _check_missing_docstrings(self, lines):
        """Find functions that appear to lack docstrings."""
        functions = []

        for line_number, line in enumerate(lines, 1):
            if not re.match(r"\s*def\s+\w+", line):
                continue

            match = re.search(r"def\s+(\w+)", line)

            if not match:
                continue

            next_lines = lines[
                line_number:min(
                    line_number + 3,
                    len(lines),
                )
            ]

            has_docstring = any(
                '"""' in current_line
                or "'''" in current_line
                for current_line in next_lines
            )

            if not has_docstring:
                functions.append(match.group(1))

        if not functions:
            return []

        return [
            "**Missing docstrings** | "
            f"Add docstrings to: `{', '.join(functions)}`"
        ]

    def _analyze_diff_quality(self, diff):
        """Analyze newly added lines for simple quality issues."""
        suggestions = []
        print_lines = []
        todo_lines = []
        wildcard_imports = []

        for line_number, line in enumerate(diff.splitlines(), 1):
            if not line.startswith("+") or line.startswith("+++"):
                continue

            if "print(" in line:
                print_lines.append(line_number)

            if "TODO" in line or "FIXME" in line:
                todo_lines.append(line_number)

            if "import *" in line:
                module = re.search(
                    r"from\s+(\S+)\s+import\s+\*",
                    line,
                )

                if module:
                    wildcard_imports.append(module.group(1))

        if print_lines:
            suggestions.append(
                f"**Logging** | Replace {len(print_lines)} "
                "new `print()` call(s) with logging."
            )

        if todo_lines:
            suggestions.append(
                f"**TODO/FIXME** | Review {len(todo_lines)} "
                "new TODO/FIXME comment(s)."
            )

        for module in sorted(set(wildcard_imports)):
            suggestions.append(
                f"**Wildcard import** | Replace "
                f"`from {module} import *` with explicit imports."
            )

        additions = sum(
            1
            for line in diff.splitlines()
            if line.startswith("+")
            and not line.startswith("+++")
        )

        if additions > 100:
            suggestions.append(
                f"**PR size** | {additions} lines added. "
                "Consider splitting the change."
            )

        return suggestions

    def _get_reviewed_python_files(self, changed_files):
        """Return changed Python files that still exist."""
        return [
            file_path
            for file_path in changed_files
            if Path(file_path).suffix == ".py"
            and Path(file_path).exists()
        ]

    def _analyze_files(self, python_files):
        """Run code and security analysis on changed Python files."""
        code_findings = []
        security_findings = []

        for file_path in python_files:
            ast_findings = self.code_analysis_tool.analyze_file(
                file_path
            )

            pattern_findings = self._analyze_code_patterns(
                file_path
            )

            file_findings = (
                pattern_findings
                if pattern_findings
                else ast_findings
            )

            for finding in file_findings:
                if isinstance(finding, dict):
                    finding["file"] = file_path

            file_security_findings = (
                self.security_analysis_tool.analyze_file(
                    file_path
                )
            )

            for finding in file_security_findings:
                if isinstance(finding, dict):
                    finding["file"] = file_path

            code_findings.extend(file_findings)
            security_findings.extend(file_security_findings)

        return code_findings, security_findings

    def _build_summary(
        self,
        code_findings,
        security_findings,
        tests_passed,
    ):
        """Build a short review summary."""
        issue_count = (
            len(code_findings)
            + len(security_findings)
        )

        if not tests_passed:
            return (
                "🔴 **Changes need attention** — "
                "tests are failing."
            )

        if issue_count == 0:
            return (
                "🟢 **Ready to merge** — "
                "tests passed and no issues were found."
            )

        if security_findings:
            priority = "🔴 HIGH"
        else:
            priority = "⚠️ MEDIUM"

        return (
            f"{priority} — **{issue_count} issue(s) found**. "
            "See the review details below."
        )

    def format_review_comment(self, review):
        """Create a concise GitHub PR review comment."""
        code_findings = review.get("code_findings", [])
        security_findings = review.get(
            "security_findings",
            [],
        )
        test_results = review.get(
            "test_results",
            {},
        )

        tests_passed = test_results.get(
            "passed",
            False,
        )

        total_issues = (
            len(code_findings)
            + len(security_findings)
        )

        if not tests_passed:
            status_text = "❌ FAIL"
        elif total_issues > 0:
            status_text = "⚠️ CHANGES REQUESTED"
        else:
            status_text = "✅ PASS"

        lines = [
            "## 🤖 Code Review",
            "",
            f"**Status:** {status_text}",
            (
                f"**Tests:** "
                f"{'✅ Passed' if tests_passed else '❌ Failed'}"
            ),
            "",
        ]

        if total_issues == 0:
            lines.extend(
                [
                    "### Result",
                    "✅ No issues found.",
                ]
            )
        else:
            lines.append(
                f"### Issues ({total_issues})"
            )

            displayed = 0
            max_findings = 5

            for finding in code_findings:
                if displayed >= max_findings:
                    break

                lines.append(
                    self._format_finding(finding)
                )
                displayed += 1

            for finding in security_findings:
                if displayed >= max_findings:
                    break

                lines.append(
                    f"- 🚨 {self._format_finding(finding)}"
                )
                displayed += 1

            remaining = total_issues - displayed

            if remaining > 0:
                lines.append(
                    f"- _{remaining} additional issue(s) detected._"
                )

        lines.extend(
            [
                "",
                "---",
                "_Generated by Code Review Agent_",
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _format_finding(finding):
        """Convert a finding into a compact review bullet."""
        if isinstance(finding, dict):
            file_path = finding.get("file", "")
            line = finding.get("line")
            message = finding.get(
                "message",
                str(finding),
            )

            location = file_path

            if line:
                location = f"{location}:{line}"

            if location:
                return f"- `{location}` — {message}"

            return f"- {message}"

        return f"- {finding}"

    def review(self):
        """Perform a complete local code review."""
        diff = self.git_diff_tool.get_diff()
        changed_files = self.git_diff_tool.get_changed_files()

        python_files = self._get_reviewed_python_files(
            changed_files
        )

        code_findings, security_findings = (
            self._analyze_files(python_files)
        )

        diff_suggestions = self._analyze_diff_quality(
            diff
        )

        test_results = self.test_runner_tool.run_tests()

        tests_passed = test_results.get(
            "passed",
            False,
        )

        status = (
            "passed"
            if tests_passed
            else "failed"
        )

        summary = self._build_summary(
            code_findings,
            security_findings,
            tests_passed,
        )

        review_result = {
            "diff": diff,
            "changed_files": changed_files,
            "code_findings": code_findings,
            "security_findings": security_findings,
            "test_results": test_results,
            "summary": summary,
            "suggested_fixes": diff_suggestions,
            "validation_status": status,
        }

        review_result["comment"] = (
            self.format_review_comment(
                review_result
            )
        )

        return review_result


if __name__ == "__main__":
    review = LocalReviewOrchestrator().review()

    print("=== CODE REVIEW ===")
    print()
    print("Changed files:")

    for file_path in review["changed_files"]:
        print(f"- {file_path}")

    print()
    print("Summary:")
    print(review["summary"])

    print()
    print("Review comment:")
    print(review["comment"])