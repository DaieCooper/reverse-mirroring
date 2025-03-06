import logging
import os

import gitlab as gitlab_api
import github as github_api


def delete_obsolete_refs(
    repo: github_api.Repository.Repository,
    ref_type: str,
    obsolete_refs: list[str],
) -> None:
    """
    Delete an obsolete reference.

    Args:
        repo (github_api.Repository.Repository): GitHub repository instance.
        ref_type (str): Reference type, either "tags" or "heads" (for branches).
        obsolete_refs (list[str]): List of references to delete.

    Returns:
        None
    """
    for ref_name in obsolete_refs:
        try:
            ref = repo.get_git_ref(f"{ref_type}/{ref_name}")
            #ref.delete()
            logging.info("Deleted obsolete %s", ref_name)
        except github_api.GithubException as e:
            logging.error("Failed to delete %s: %s", ref_name, e)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    project_name = os.getenv("CI_PROJECT_NAME")
    gitlab_project_id = os.getenv("CI_PROJECT_ID")
    gitlab = gitlab_api.Gitlab(
        url=f'https://{os.getenv("CI_SERVER_FQDN")}',
        private_token=os.getenv("GITLAB_PERSONAL_API_PRIVATE_TOKEN"),
    )
    github = github_api.Github(
        login_or_token=os.getenv("GITHUB_PERSONAL_API_PRIVATE_TOKEN")
    )
    github_api_url = f"DaieCooper/{project_name}"
    gitlab_repo = gitlab.projects.get(gitlab_project_id)
    gitlab_branches = [branch.name for branch in gitlab_repo.branches.list(all=True)]
    gitlab_tags = [tag.name for tag in gitlab_repo.tags.list(all=True)]
    github_repo = github.get_repo(github_api_url)
    github_branches = [
        branch.name for branch in github_repo.get_branches() if not branch.protected
    ]
    github_tags = [tag.name for tag in github_repo.get_tags()]
    logging.info("%s gitlab project branches: %s", project_name, gitlab_branches)
    logging.info("%s gitlab project tags: %s", project_name, gitlab_tags)
    logging.info("%s github project branches: %s", project_name, github_branches)
    logging.info("%s github project tags: %s", project_name, github_tags)
    obsolete_branches = list(set(github_branches) - set(gitlab_branches))
    obsolete_tags = list(set(github_tags) - set(gitlab_tags))
    logging.info("Obsolete branches: %s", obsolete_branches)
    logging.info("Obsolete tags: %s", obsolete_tags)
    delete_obsolete_refs(github_repo, "tags", obsolete_tags)
    delete_obsolete_refs(github_repo, "heads", obsolete_branches)
