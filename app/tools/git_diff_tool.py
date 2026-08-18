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
        
        # Use two-dot diff which works in PR merge commit contexts
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


if __name__ == "__main__":
    tool = GitDiffTool()
    diff = tool.get_diff()

    if diff:
        print(diff)
    else:
        print("No changes found.")