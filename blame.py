from git import Repo, GitCommandError


class CommitLinkFinder:
    def __init__(self, verbose, repo_path, old_tag, new_tag, diffkemp_out):
        self.verbose = verbose
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

    def get_commits_from_blame(self, file, start_line, end_line):
        try:
            commits = self.repo.blame(
                f"{self.old_tag}..{self.new_tag}", file, L=f"{start_line},{end_line}"
            )
        except GitCommandError as e:
            return []
        return [commit[0].hexsha for commit in commits]

    def get_commits_for_diff(self, diff):
        function = diff["function"]
        start_line = None
        end_line = None
        if (
            function in self.diffkemp_definitions
            and "new" in self.diffkemp_definitions[function]
        ):
            file = self.diffkemp_definitions[function]["new"]["file"]
            if "line" in self.diffkemp_definitions[function]["new"]:
                start_line = self.diffkemp_definitions[function]["new"]["line"]
            if "end-line" in self.diffkemp_definitions[function]["new"]:
                end_line = self.diffkemp_definitions[function]["new"]["end-line"]
        elif "new-callstack" in diff and len(diff["new-callstack"]) > 0:
            file = diff["new-callstack"][-1]["file"]
        else:
            print(f"Could not determine which file defines {function}.")
            return []
        if start_line and end_line:
            blame_commits = self.get_commits_from_blame(file, start_line, end_line)
        else:
            blame_commits = []
        log_commits = self.get_commits_from_log(function, file)
        return blame_commits + log_commits

    def get_commit_links(self, function):
        if self.verbose:
            print(
                f"Getting links to commits modifying {function} between {self.old_tag} and {self.new_tag}."
            )
        if function not in self.diffkemp_results:
            if self.verbose:
                print(f"Function {function} did not change semantically.")
            return []
        diffs = self.diffkemp_results[function]["diffs"]
        commit_lists = [self.get_commits_for_diff(diff) for diff in diffs]
        commit_set = set(sum(commit_lists, []))
        commit_links = [self.sha_to_link(sha) for sha in commit_set]
        return commit_links
