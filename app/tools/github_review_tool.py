import os

from github import Github


class GitHubReviewTool:
    """Post code review comments to GitHub pull requests."""

    def __init__(self):
        """Initialize the GitHub client using a personal access token."""
        token = os.getenv("GITHUB_TOKEN")

        if not token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        self.github = Github(token)

    def post_review_comment(
        self,
        repository,
        pull_request_number,
        comment,
    ):
        """Post a review comment to a GitHub pull request."""
        repo = self.github.get_repo(repository)
        pull_request = repo.get_pull(pull_request_number)

        pull_request.create_issue_comment(comment)

        return True