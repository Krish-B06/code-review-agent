import subprocess


class GitDiffTool:
    def get_diff(self, base_branch="main"):
        result = subprocess.run(
            [
                "git",
                "diff",
                f"{base_branch}...HEAD",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout


if __name__ == "__main__":
    tool = GitDiffTool()
    diff = tool.get_diff()

    if diff:
        print(diff)
    else:
        print("No changes found.")