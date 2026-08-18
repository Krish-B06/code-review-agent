import subprocess


class TestRunnerTool:
    def run_tests(self):
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
            ],
            capture_output=True,
            text=True,
        )

        return {
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "output": result.stdout,
            "errors": result.stderr,
        }


if __name__ == "__main__":
    tool = TestRunnerTool()

    result = tool.run_tests()

    print("Tests passed:", result["passed"])
    print("Exit code:", result["exit_code"])
    print(result["output"])

    if result["errors"]:
        print("Errors:")
        print(result["errors"])