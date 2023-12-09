import shutil
import enum
import subprocess
import os
import sys
import yaml


DIFFKEMP_OUT_FILENAME = "diffkemp-out.yaml"


class DiffType(enum.StrEnum):
    NO_DIFF = enum.auto()
    SYNTACTIC = enum.auto()
    SEMANTIC = enum.auto()
    UNKNOWN = enum.auto()


class ComparisonResults:
    """Class for dealing with project comparison results."""

    def __init__(self, results={}):
        self.results = results

    @staticmethod
    def key(old_tag, new_tag):
        """Given two tags, construct a key for the result dictionary."""
        return f"{old_tag} -> {new_tag}"

    def add(self, old_tag, new_tag, tag_results):
        """Add comparison between two tags to the results."""
        self.results[self.key(old_tag, new_tag)] = tag_results

    def get(self, old_tag, new_tag):
        """Get comparison between two tags from the results."""
        return self.results[self.key(old_tag, new_tag)]

    @classmethod
    def load(cls, results_file):
        """Load results from a file."""
        with open(results_file, "r") as res_file:
            results = yaml.safe_load(res_file)
        return cls(results)

    def get_stats(self):
        """Return statistics about the results."""
        stats = {}
        for tag_key, tag_results in self.results.items():
            stats[tag_key] = {}
            for diff_type in DiffType:
                stats[tag_key][diff_type.value] = len(
                    [x for x in tag_results.values() if x == diff_type.value]
                )
        return stats


class Comparator:
    """Class for comparing project snapshots."""

    def __init__(
        self,
        verbose,
        diffkemp,
        config,
        snapshots_dir,
        output_dir,
        custom_patterns,
        disable_patterns,
    ):
        self.verbose = verbose
        self.diffkemp = diffkemp
        self.project_name = config["name"]
        self.snapshots_dir = snapshots_dir
        self.output_dir = output_dir
        self.custom_patterns = custom_patterns
        self.disable_patterns = disable_patterns
        self.functions = config["functions"]
        self.results = ComparisonResults()

    def compare_snapshots(self, old_tag, new_tag):
        """Compare a function across two snapshots using diffkemp."""
        old_tag_dir = os.path.join(self.snapshots_dir, old_tag)
        new_tag_dir = os.path.join(self.snapshots_dir, new_tag)

        os.makedirs(self.output_dir, exist_ok=True)
        diffkemp_out_dir = os.path.join(self.output_dir, f"{old_tag}-{new_tag}")
        shutil.rmtree(diffkemp_out_dir, ignore_errors=True)

        # Run diffkemp compare
        compare_command = [
            self.diffkemp,
            "compare",
            "--full-diff",
            old_tag_dir,
            new_tag_dir,
            "-o",
            diffkemp_out_dir,
        ]

        if self.custom_patterns:
            compare_command.extend(["--custom-patterns", self.custom_patterns])

        if self.disable_patterns:
            disable_patterns_list = [
                pattern.strip() for pattern in self.disable_patterns.split(",")
            ]
            disable_patterns_opt = map(
                lambda x: f"--disable-pattern={x}", disable_patterns_list
            )
            compare_command.extend(disable_patterns_opt)

        print(f"Comparing {old_tag} and {new_tag} of {self.project_name}.")
        if self.verbose:
            print(" ".join(compare_command))

        compare_result = subprocess.check_output(compare_command)

        # Load the yaml output
        with open(
            os.path.join(diffkemp_out_dir, DIFFKEMP_OUT_FILENAME), "r"
        ) as res_file:
            diffkemp_out = yaml.safe_load(res_file)

        tag_results = {}
        for function in self.functions:
            if f"{function}: unknown" in compare_result.decode():
                diff_type = DiffType.UNKNOWN
            elif function in map(lambda x: x["function"], diffkemp_out["results"]):
                diff_type = DiffType.SEMANTIC
            elif f"{function}.diff" in os.listdir(diffkemp_out_dir):
                diff_type = DiffType.SYNTACTIC
            else:
                diff_type = DiffType.NO_DIFF
            tag_results[function] = diff_type.value

        self.results.add(old_tag, new_tag, tag_results)

    def get_results(self):
        """Return the results object."""
        return self.results
