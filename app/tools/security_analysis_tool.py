import re


class SecurityAnalysisTool:
    SECRET_PATTERNS = [
        (
            "possible_api_key",
            re.compile(
                r"(api[_-]?key|apikey)\s*=\s*['\"][^'\"]+['\"]",
                re.IGNORECASE,
            ),
        ),
        (
            "possible_password",
            re.compile(
                r"(password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]",
                re.IGNORECASE,
            ),
        ),
        (
            "possible_token",
            re.compile(
                r"(token|secret)\s*=\s*['\"][^'\"]+['\"]",
                re.IGNORECASE,
            ),
        ),
    ]

    def analyze_file(self, file_path):
        findings = []

        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                findings.extend(
                    self._check_line(line, line_number)
                )

        return findings

    def _check_line(self, line, line_number):
        findings = []

        for finding_type, pattern in self.SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(
                    {
                        "type": "security",
                        "severity": "high",
                        "category": finding_type,
                        "message": (
                            "Possible hardcoded secret detected."
                        ),
                        "line": line_number,
                    }
                )

        return findings


if __name__ == "__main__":
    tool = SecurityAnalysisTool()

    findings = tool.analyze_file(
        "app/services/student_service.py"
    )

    if not findings:
        print("No security issues found.")
    else:
        for finding in findings:
            print(finding)