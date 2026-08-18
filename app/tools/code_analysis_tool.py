import ast
import re


class CodeAnalysisTool:
    def analyze_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            source_code = file.read()

        tree = ast.parse(source_code)

        findings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                findings.extend(
                    self._check_function_name(node)
                )

            elif isinstance(node, ast.ClassDef):
                findings.extend(
                    self._check_class_name(node)
                )

            elif isinstance(node, ast.Name):
                findings.extend(
                    self._check_variable_name(node)
                )

        return findings

    def _check_function_name(self, node):
        findings = []

        if not self._is_snake_case(node.name):
            findings.append(
                {
                    "type": "naming",
                    "severity": "low",
                    "message": (
                        f"Function '{node.name}' "
                        "should use snake_case."
                    ),
                    "line": node.lineno,
                }
            )

        return findings

    def _check_class_name(self, node):
        findings = []

        if not self._is_pascal_case(node.name):
            findings.append(
                {
                    "type": "naming",
                    "severity": "low",
                    "message": (
                        f"Class '{node.name}' "
                        "should use PascalCase."
                    ),
                    "line": node.lineno,
                }
            )

        return findings

    def _check_variable_name(self, node):
        findings = []

        if isinstance(node.ctx, ast.Store):
            if (
                not self._is_snake_case(node.id)
                and node.id != "_"
            ):
                findings.append(
                    {
                        "type": "naming",
                        "severity": "low",
                        "message": (
                            f"Variable '{node.id}' "
                            "should use snake_case."
                        ),
                        "line": node.lineno,
                    }
                )

        return findings

    @staticmethod
    def _is_snake_case(name):
        return bool(
            re.match(
                r"^[a-z_][a-z0-9_]*$",
                name,
            )
        )

    @staticmethod
    def _is_pascal_case(name):
        return bool(
            re.match(
                r"^[A-Z][a-zA-Z0-9]*$",
                name,
            )
        )


if __name__ == "__main__":
    tool = CodeAnalysisTool()

    findings = tool.analyze_file(
        "app/services/student_service.py"
    )

    if not findings:
        print("No naming issues found.")
    else:
        for finding in findings:
            print(finding)