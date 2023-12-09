from git import Repo, GitCommandError


class CommitLinkFinder:
    def __init__(self, repo_path, old_tag, new_tag, diffkemp_out):
        self.repo = Repo(repo_path)
        self.repo_url = self.repo.remotes.origin.url.split(".git")[0]
        self.old_tag = old_tag
        self.new_tag = new_tag
        self.diffkemp_results = self.list_to_dict(diffkemp_out["results"], "function")
        self.diffkemp_definitions = diffkemp_out["definitions"]

    @staticmethod
    def list_to_dict(list, key):
        return {item[key]: item for item in list}

    def sha_to_link(self, sha):
        return f"{self.repo_url}/commit/{sha}"

    def get_commits_from_log(self, function, file):
        try:
            commits = self.repo.git.log(
                "-q",
                "--pretty=format:%H",
                f"-L:{function}:{file}",
                f"{self.old_tag}..{self.new_tag}",
            )
        except GitCommandError:
            return []
        return commits.split()

    def get_commits_for_function(self, function):
        try:
            file = self.diffkemp_definitions[function]["new"]["file"]
        except KeyError:
            return []
        return self.get_commits_from_log(function, file)

    def get_commit_links(self, function):
        if function not in self.diffkemp_results:
            return []
        functions = [d["function"] for d in self.diffkemp_results[function]["diffs"]]
        commit_lists = [self.get_commits_for_function(f) for f in functions]
        commit_set = set(sum(commit_lists, []))
        commit_links = [self.sha_to_link(sha) for sha in commit_set]
        return commit_links
