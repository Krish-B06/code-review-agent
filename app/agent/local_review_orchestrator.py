
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

    def _group_and_summarize_findings(self, findings):
        """Group similar findings for clarity and reduce noise."""
        if not findings:
            return []

        grouped = {}

        for finding in findings:
            if "missing return type hint" in finding:
                key = "Missing Type Hints"
                if key not in grouped:
                    grouped[key] = []

                func_name = (
                    finding.split("`")[1]
                    if "`" in finding
                    else "unknown"
                )
                grouped[key].append(func_name)

            elif "missing docstring" in finding:
                key = "Missing Docstrings"
                if key not in grouped:
                    grouped[key] = []

                func_name = (
                    finding.split("`")[1]
                    if "`" in finding
                    else "unknown"
                )
                grouped[key].append(func_name)

        summary = []

        if "Missing Type Hints" in grouped:
            funcs = ", ".join(set(grouped["Missing Type Hints"]))
            summary.append(
                f"**Missing Return Type Hints** | "
                f"Add `-> ReturnType` to: {funcs}"
            )

        if "Missing Docstrings" in grouped:
            funcs = ", ".join(set(grouped["Missing Docstrings"]))
            summary.append(
                f"**Missing Docstrings** | Add docstrings to: {funcs}"
            )

        return summary

    def _analyze_code_patterns(self, filepath):
        """Intelligent pattern analysis with exact line numbers."""
        findings = []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Check for long methods with exact locations.
            method_pattern = r"def\s+(\w+)\s*\("
            methods = list(re.finditer(method_pattern, content))

            for i, method_match in enumerate(methods):
                start_line = (
                    content[: method_match.start()].count("\n") + 1
                )

                end_line = (
                    content[: methods[i + 1].start()].count("\n") + 1
                    if i + 1 < len(methods)
                    else len(lines)
                )

                method_length = end_line - start_line

                if method_length > 20:
                    findings.append(
                        f"**{filepath}:{start_line}-{end_line}** | "
                        f"Method `{method_match.group(1)}()` is "
                        f"{method_length} lines - refactor into smaller functions"
                    )

            # Check for missing type hints.
            missing_type_hints = []

            for line_num, line in enumerate(lines, 1):
                if re.match(r"\s*def\s+\w+\s*\(", line):
                    if "->" not in line and "def " in line:
                        func_name = re.search(r"def\s+(\w+)", line)

                        if func_name:
                            missing_type_hints.append(
                                func_name.group(1)
                            )

            if missing_type_hints:
                findings.append(
                    f"**Type Hints Missing** | "
                    f"Add return types to: "
                    f"`{', '.join(missing_type_hints)}`"
                )

            # Check for bare except blocks.
            except_issues = []

            for line_num, line in enumerate(lines, 1):
                if re.search(r"except\s*:", line):
                    except_issues.append(f"line {line_num}")

                elif "except Exception" in line:
                    except_issues.append(
                        f"line {line_num} (generic Exception)"
                    )

            if except_issues:
                findings.append(
                    f"**Exception Handling** | "
                    f"Fix bare except clauses at "
                    f"{', '.join(except_issues)}"
                )

            # Check for missing docstrings.
            missing_docs = []

            for line_num, line in enumerate(lines, 1):
                if re.match(r"\s*def\s+\w+", line):
                    next_lines = lines[
                        line_num : min(line_num + 3, len(lines))
                    ]

                    has_docstring = any(
                        '"""' in l or "'''" in l
                        for l in next_lines
                    )

                    if not has_docstring:
                        func_name = re.search(
                            r"def\s+(\w+)",
                            line,
                        )

                        if func_name:
                            missing_docs.append(
                                func_name.group(1)
                            )

            if missing_docs:
                findings.append(
                    f"**Missing Docstrings** | "
                    f"Add to: `{', '.join(missing_docs)}`"
                )

        except Exception:
            # A single file should not cause the entire review to fail.
            pass

        return findings

    def _analyze_diff_quality(self, diff):
        """Analyze the diff for architectural concerns."""
        suggestions = []
        print_issues = []
        todo_issues = []

        for line_num, line in enumerate(diff.split("\n"), 1):
            # Collect newly added print statements.
            if "print(" in line and line.startswith("+"):
                print_issues.append(line_num)

            # Collect newly added TODO/FIXME comments.
            if (
                ("TODO" in line or "FIXME" in line)
                and line.startswith("+")
            ):
                todo_issues.append(line_num)

            # Detect wildcard imports.
            if "import *" in line and line.startswith("+"):
                module = re.search(
                    r"from\s+(\S+)\s+import\s+\*",
                    line,
                )

                if module:
                    suggestions.append(
                        f"**Avoid wildcard imports** | "
                        f"Use explicit imports instead of "
                        f"`from {module.group(1)} import *`"
                    )

        # Group print statements.
        if print_issues:
            sample = (
                f"line {print_issues[0]}"
                if len(print_issues) == 1
                else f"{len(print_issues)} lines"
            )

            suggestions.append(
                f"**Replace print() with logging** | "
                f"Found {len(print_issues)} print() calls "
                f"({sample}) - use `import logging` instead"
            )

        # Group TODO/FIXME comments.
        if todo_issues:
            sample = (
                f"line {todo_issues[0]}"
                if len(todo_issues) == 1
                else f"{len(todo_issues)} locations"
            )

            suggestions.append(
                f"**Remove TODO/FIXME comments** | "
                f"Implement immediately or open GitHub issues "
                f"({sample})"
            )

        large_file_additions = len(
            [
                line
                for line in diff.split("\n")
                if line.startswith("+")
            ]
        )

        if large_file_additions > 100:
            suggestions.append(
                f"**Consider smaller PRs** | "
                f"This PR has {large_file_additions} additions - "
                f"break into smaller focused changes"
            )

        return suggestions

    def format_review_comment(self, review):
        """Format review with crisp, clear guidance for developers."""
        code_findings = review.get("code_findings", [])
        security_findings = review.get("security_findings", [])
        suggested_fixes = review.get("suggested_fixes", [])

        status = review.get(
            "validation_status",
            "unknown",
        ).upper()

        if status == "PASSED":
            status_line = "✅ **Tests: PASSED**"
        else:
            status_line = (
                "❌ **Tests: FAILED** - Fix before merging"
            )

        sections = []

        # Show changed files.
        changed_files = review.get("changed_files", [])

        if changed_files:
            sections.append(
                "## Files Reviewed\n"
                + "\n".join(
                    f"- `{file_path}`"
                    for file_path in changed_files
                )
            )

        # Code quality issues.
        if code_findings:
            quality_items = []

            for finding in code_findings:
                if isinstance(finding, dict):
                    file_path = finding.get("file")
                    message = finding.get("message", str(finding))
                    line = finding.get("line")

                    location = ""

                    if file_path:
                        location = f"`{file_path}`"

                    if line:
                        location += f":{line}"

                    if location:
                        quality_items.append(
                            f"- {location} — {message}"
                        )
                    else:
                        quality_items.append(
                            f"- {message}"
                        )
                else:
                    quality_items.append(
                        f"- {finding}"
                    )

            sections.append(
                "## Issues Found\n"
                + "\n".join(quality_items)
            )
        else:
            sections.append(
                "## Issues Found\n- ✅ None"
            )

        # Action items.
        if suggested_fixes:
            action_items = []

            for i, fix in enumerate(
                suggested_fixes,
                1,
            ):
                action_items.append(
                    f"{i}. {fix}"
                )

            sections.append(
                "## Next Steps\n"
                + "\n".join(action_items)
            )

        # Security issues.
        if security_findings:
            security_items = []

            for finding in security_findings:
                if isinstance(finding, dict):
                    file_path = finding.get("file")
                    message = finding.get(
                        "message",
                        str(finding),
                    )
                    line = finding.get("line")

                    location = ""

                    if file_path:
                        location = f"`{file_path}`"

                    if line:
                        location += f":{line}"

                    if location:
                        security_items.append(
                            f"- {location} — {message}"
                        )
                    else:
                        security_items.append(
                            f"- {message}"
                        )
                else:
                    security_items.append(
                        f"- {finding}"
                    )

            sections.append(
                "## ⚠️ Security Issues\n"
                + "\n".join(security_items)
            )

        return (
            f"## Review Summary\n\n"
            f"{review.get('summary', '')}\n\n"
            f"{status_line}\n\n"
            f"{''.join(s + chr(10) + chr(10) for s in sections)}"
            f"---\n"
            f"*Auto-generated by Code Review Agent*"
        )

    def review(self):
        """Perform intelligent local code review."""
        diff = self.git_diff_tool.get_diff()

        # Dynamically discover files changed relative to main.
        changed_files = self.git_diff_tool.get_changed_files()

        # Only Python files can currently be analyzed by the
        # Python AST-based analysis tools.
        python_files = [
            file_path
            for file_path in changed_files
            if Path(file_path).suffix == ".py"
            and Path(file_path).exists()
        ]

        all_code_findings = []
        all_security_findings = []

        # Review every changed Python file.
        for file_path in python_files:
            code_findings = (
                self.code_analysis_tool.analyze_file(
                    file_path
                )
            )

            pattern_findings = (
                self._analyze_code_patterns(
                    file_path
                )
            )

            security_findings = (
                self.security_analysis_tool.analyze_file(
                    file_path
                )
            )

            # Prefer pattern findings when available.
            file_code_findings = (
                pattern_findings
                if pattern_findings
                else code_findings
            )

            # Add file context to dictionary-based findings.
            for finding in file_code_findings:
                if isinstance(finding, dict):
                    finding["file"] = file_path

            for finding in security_findings:
                if isinstance(finding, dict):
                    finding["file"] = file_path

            all_code_findings.extend(
                file_code_findings
            )

            all_security_findings.extend(
                security_findings
            )

        # Analyze the complete diff.
        diff_suggestions = (
            self._analyze_diff_quality(diff)
        )

        all_suggestions = diff_suggestions.copy()

        # Run the project's test suite.
        test_results = (
            self.test_runner_tool.run_tests()
        )

        tests_passed = test_results.get(
            "passed",
            False,
        )

        status = (
            "passed"
            if tests_passed
            else "failed"
        )

        issues_count = (
            len(all_code_findings)
            + len(all_security_findings)
        )

        if status == "failed":
            summary = (
                "🔴 **Tests are failing** - "
                "Please fix before requesting merge review."
            )

        elif issues_count == 0 and tests_passed:
            summary = (
                "🟢 **Ready to merge!** "
                "Code quality looks good, all tests passing."
            )

        elif issues_count == 0:
            summary = (
                "🟢 **Code quality approved** - "
                "Tests passing, no issues found."
            )

        else:
            priority = (
                "⚠️ **HIGH**"
                if all_security_findings
                else "**MEDIUM**"
            )

            summary = (
                f"{priority} **{issues_count} issue(s) to fix** "
                "- See details below."
            )

        if not all_suggestions:
            if issues_count == 0:
                all_suggestions = []
            else:
                all_suggestions = [
                    "Address the issues listed above before merging"
                ]

        review_result = {
            "diff": diff,
            "changed_files": changed_files,
            "code_findings": all_code_findings,
            "security_findings": all_security_findings,
            "test_results": test_results,
            "summary": summary,
            "suggested_fixes": all_suggestions,
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

