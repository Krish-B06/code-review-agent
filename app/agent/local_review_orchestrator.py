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

        # Group by issue type
        grouped = {}
        for finding in findings:
            # Extract the issue type (e.g., "missing return type hint")
            if "missing return type hint" in finding:
                key = "Missing Type Hints"
                if key not in grouped:
                    grouped[key] = []
                # Extract function name
                func_name = finding.split("`")[1] if "`" in finding else "unknown"
                line_num = finding.split(":")[1] if ":" in finding else "?"
                grouped[key].append(func_name)

            elif "missing docstring" in finding:
                key = "Missing Docstrings"
                if key not in grouped:
                    grouped[key] = []
                func_name = finding.split("`")[1] if "`" in finding else "unknown"
                grouped[key].append(func_name)

        # Create summary findings
        summary = []
        if "Missing Type Hints" in grouped:
            funcs = ", ".join(set(grouped["Missing Type Hints"]))
            summary.append(
                f"**Missing Return Type Hints** | Add `-> ReturnType` to: {funcs}"
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
            missing_type_hints = []
            for line_num, line in enumerate(lines, 1):
                if re.match(r"\s*def\s+\w+\s*\(", line):
                    if "->" not in line and "def " in line:
                        func_name = re.search(r"def\s+(\w+)", line)
                        if func_name:
                            missing_type_hints.append(func_name.group(1))

            if missing_type_hints:
                findings.append(
                    f"**Type Hints Missing** | Add return types to: `{', '.join(missing_type_hints)}`"
                )

            # Check for bare except blocks with exact line
            except_issues = []
            for line_num, line in enumerate(lines, 1):
                if re.search(r"except\s*:", line):
                    except_issues.append(f"line {line_num}")
                elif "except Exception" in line:
                    except_issues.append(f"line {line_num} (generic Exception)")

            if except_issues:
                findings.append(
                    f"**Exception Handling** | Fix bare except clauses at {', '.join(except_issues)}"
                )

            # Check for missing docstrings
            missing_docs = []
            for line_num, line in enumerate(lines, 1):
                if re.match(r"\s*def\s+\w+", line):
                    next_lines = lines[line_num : min(line_num + 3, len(lines))]
                    has_docstring = any('"""' in l or "'''" in l for l in next_lines)
                    if not has_docstring:
                        func_name = re.search(r"def\s+(\w+)", line)
                        if func_name:
                            missing_docs.append(func_name.group(1))

            if missing_docs:
                findings.append(
                    f"**Missing Docstrings** | Add to: `{', '.join(missing_docs)}`"
                )

        except Exception as e:
            pass

        return findings

    def _analyze_diff_quality(self, diff):
        """Analyze the diff for architectural concerns - grouped summary."""
        suggestions = []
        print_issues = []
        todo_issues = []

        for line_num, line in enumerate(diff.split("\n"), 1):
            # Collect print statements
            if "print(" in line and line.startswith("+"):
                print_issues.append(line_num)

            # Collect TODO/FIXME
            if ("TODO" in line or "FIXME" in line) and line.startswith("+"):
                todo_issues.append(line_num)

            # Import star
            if "import *" in line and line.startswith("+"):
                module = re.search(r"from\s+(\S+)\s+import\s+\*", line)
                if module:
                    suggestions.append(
                        f"**Avoid wildcard imports** | Use explicit imports instead of `from {module.group(1)} import *`"
                    )

        # Group print statements
        if print_issues:
            sample = f"line {print_issues[0]}" if len(print_issues) == 1 else f"{len(print_issues)} lines"
            suggestions.append(
                f"**Replace print() with logging** | Found {len(print_issues)} print() calls ({sample}) - use `import logging` instead"
            )

        # Group TODO/FIXME
        if todo_issues:
            sample = f"line {todo_issues[0]}" if len(todo_issues) == 1 else f"{len(todo_issues)} locations"
            suggestions.append(
                f"**Remove TODO/FIXME comments** | Implement immediately or open GitHub issues ({sample})"
            )

        large_file_additions = len([l for l in diff.split("\n") if l.startswith("+")])
        if large_file_additions > 100:
            suggestions.append(
                f"**Consider smaller PRs** | This PR has {large_file_additions} additions - break into smaller focused changes"
            )

        return suggestions

    def format_review_comment(self, review):
        """Format review as concise, scannable markdown."""
        code_findings = review.get("code_findings", [])
        security_findings = review.get("security_findings", [])
        suggested_fixes = review.get("suggested_fixes", [])

        # Build sections
        sections = []

        # Code Quality
        if code_findings:
            sections.append("### Code Quality\n" + "\n".join(f"- {f}" for f in code_findings))
        else:
            sections.append("### Code Quality\n- ✅ No issues detected")

        # Security
        if security_findings:
            sections.append("### Security\n" + "\n".join(f"- {f}" for f in security_findings))
        else:
            sections.append("### Security\n- ✅ No concerns detected")

        # Recommendations
        if suggested_fixes:
            sections.append("### Action Items\n" + "\n".join(f"- {f}" for f in suggested_fixes))

        # Test Status
        sections.append(f"### Tests\n- **{review.get('validation_status', 'unknown').upper()}** ✅")

        body = "\n\n".join(sections)

        return (
            f"## Code Review\n\n"
            f"{review.get('summary', '')}\n\n"
            f"{body}"
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
