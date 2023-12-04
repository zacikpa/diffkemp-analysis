from git import Repo, GitCommandError

class CommitLinkFinder:
    def __init__(self, old_repo_path, new_repo_path, diffkemp_out):
        self.old_repo = Repo(old_repo_path)
        self.new_repo = Repo(new_repo_path)
        self.old_commits = set(self.old_repo.iter_commits())
        self.repo_url = self.new_repo.remotes.origin.url.split(".git")[0]
        self.diffkemp_out = diffkemp_out

    def commit_to_link(self, commit):
        return f"{self.repo_url}/commit/{commit.hexsha}"

    def get_new_commit_links(self, function):
        diffkemp_out_results = self.diffkemp_out["results"]
        function_results = [result for result in diffkemp_out_results if result["function"] == function]
        if len(function_results) == 0:
            return []
        function_diffs = function_results[0]["diffs"]
        commits = []
        for diff in function_diffs:
            diff_function = diff["function"]
            diff_file = None
            first_line = None
            last_line = None
            if "new-callstack" in diff and len(diff["new-callstack"]) > 0 and "file" in diff["new-callstack"][-1]:
                diff_file = diff["new-callstack"][-1]["file"]
            elif diff_function in self.diffkemp_out["definitions"]:
                diff_detail = self.diffkemp_out["definitions"][diff_function]["new"]
                diff_file = diff_detail["file"]
                if "line" in diff_detail:
                    first_line = diff_detail["line"]
                if "end-line" in diff_detail:
                    last_line = diff_detail["end-line"]
            if diff_file is None:
                continue
            if first_line is not None and last_line is not None:
                commits.extend(self.get_new_commits_by_lines(diff_file, first_line, last_line))
            commits.extend(self.get_new_commits_by_function_name(diff_file, diff_function))
        return list(set(map(self.commit_to_link, commits)))

    def get_new_commits_by_lines(self, file, first_line, last_line):
        try:
            blame = self.new_repo.blame("HEAD", file, L=f"{first_line},{last_line}")
        except GitCommandError:
            return []
        commits = [commit[0] for commit in blame if commit[0] not in self.old_commits]
        return list(set(commits))
    
    def get_new_commits_by_function_name(self, file, function_name):
        try:
            blame = self.new_repo.blame("HEAD", file, L=f":{function_name}")
        except GitCommandError:
            return []
        commits = [commit[0] for commit in blame if commit[0] not in self.old_commits]
        return list(set(commits))