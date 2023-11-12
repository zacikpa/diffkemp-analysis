import shutil
import enum
import subprocess
import os
import sys
import yaml


DIFFKEMP_OUT_FILENAME = "diffkemp-out.yaml"


class DiffType(enum.StrEnum):
    NoDiff = enum.auto()
    Syntactic = enum.auto()
    Semantic = enum.auto()
    Unknown = enum.auto()


class ComparisonResults:
    """Class for dealing with library comparison results."""

    def __init__(self, filename=None):
        if filename and os.path.isfile(filename):
            with open(filename, "r") as result_file:
                self.results = yaml.safe_load(result_file)
        else:
            self.results = {}

    @staticmethod
    def key(old_tag, new_tag):
        """Given two tags, construct a key for the result dictionary."""
        return f"{old_tag} -> {new_tag}"

    def exists(self, library, old_tag, new_tag, functions):
        """Check if the results contain the comparison of two snapshots."""
        return (
            library in self.results
            and self.key(old_tag, new_tag) in self.results[library]
            and set(self.results[library][self.key(old_tag, new_tag)].keys())
            == set(functions)
        )

    def add(self, library, old_tag, new_tag, tag_results):
        """Add comparison between two tags to the results."""
        if library not in self.results:
            self.results[library] = {}
        self.results[library][self.key(old_tag, new_tag)] = tag_results

    def export(self, output):
        """Export (or print out) results."""
        if output:
            print(f"Exporting results to {output}")
            with open(output, "w") as out_file:
                yaml.safe_dump(self.results, out_file)
        else:
            yaml.safe_dump(self.results, sys.stdout, sort_keys=False)

    def print_stats(self):
        """Print out statistics about the results."""

        def print_count(diff_type, count, total):
            print(f"\t\t{diff_type}: {count}\t({count / total * 100:.1f}%)")

        for library, library_results in sorted(self.results.items()):
            print(f"{library}:")
            for tag_key, tag_results in library_results.items():
                print(f"\t{tag_key}:")
                total = len(tag_results)
                for diff_type in DiffType:
                    count = len(
                        [x for x in tag_results.values() if x == diff_type]
                    )
                    print_count(diff_type, count, total)
            print("\ttotal:")
            total = sum(map(len, library_results.values()))
            for diff_type in DiffType:
                count = sum(
                    map(
                        lambda x: len(
                            [y for y in x.values() if y == diff_type]
                        ),
                        library_results.values(),
                    )
                )
                print_count(diff_type, count, total)


class Comparator:
    """Class for comparing snapshots of libraries."""

    def __init__(self, verbose, diffkemp, snapshots, results):
        self.verbose = verbose
        self.diffkemp = diffkemp
        self.snapshots = snapshots
        self.results = results

    def compare_snapshots(self, library, old_tag, new_tag, functions, additional_args):
        """Compare a function across two snapshots using diffkemp."""
        if self.results.exists(library, old_tag, new_tag, functions):
            return

        old_tag_dir = os.path.join(self.snapshots, library, old_tag)
        new_tag_dir = os.path.join(self.snapshots, library, new_tag)

        out_dir = f"{library}-{old_tag}-{new_tag}"

        # Run diffkemp compare
        compare_command = [
            self.diffkemp,
            "compare",
            "--full-diff",
            old_tag_dir,
            new_tag_dir,
            "-o",
            out_dir,
        ]

        if additional_args:
            compare_command.append(additional_args)

        print(f"Comparing {old_tag} and {new_tag}.")
        if self.verbose:
            print(" ".join(compare_command))

        compare_result = subprocess.run(compare_command, capture_output=True)
        compare_result.check_returncode()
    
        # Load the yaml output
        with open(os.path.join(out_dir, DIFFKEMP_OUT_FILENAME), "r") as res_file:
            diffkemp_out = yaml.safe_load(res_file)

        tag_results = {}
        for function in functions:
            if f"{function}: unknown" in compare_result.stdout.decode():
                diff_type = DiffType.Unknown
            elif function in map(lambda x: x["function"], diffkemp_out["results"]):
                diff_type = DiffType.Semantic
            elif f"{function}.diff" in os.listdir(out_dir):
                diff_type = DiffType.Syntactic
            else:
                diff_type = DiffType.NoDiff
            tag_results[function] = diff_type.value

        shutil.rmtree(out_dir)

        self.results.add(library, old_tag, new_tag, tag_results)

    def get_results(self):
        """Return the results object."""
        return self.results
