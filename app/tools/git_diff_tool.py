import subprocess


class GitDiffTool:
    def get_diff(self, base_branch="main"):
        # Ensure the base branch is fetched for GitHub Actions compatibility
        subprocess.run(
            ["git", "fetch", "origin", base_branch, "--depth=1"],
            capture_output=True,
            text=True,
        )

        remote_branch = f"origin/{base_branch}"

        # Get the full code diff between the base branch and current HEAD
        result = subprocess.run(
            [
                "git",
                "diff",
                f"{remote_branch}..HEAD",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return result.stdout

    def get_changed_files(self, base_branch="main"):
        # Ensure the base branch is fetched for GitHub Actions compatibility
        subprocess.run(
            ["git", "fetch", "origin", base_branch, "--depth=1"],
            capture_output=True,
            text=True,
        )

        remote_branch = f"origin/{base_branch}"

        # Get only the paths of files changed relative to the base branch
        result = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                f"{remote_branch}..HEAD",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        return [
            file_path.strip()
            for file_path in result.stdout.splitlines()
            if file_path.strip()
        ]


if __name__ == "__main__":
    tool = GitDiffTool()

    diff = tool.get_diff()

    if diff:
        print(diff)
    else:
        print("No changes found.")

    print("\nChanged files:")
    for file_path in tool.get_changed_files():
        print(file_path)