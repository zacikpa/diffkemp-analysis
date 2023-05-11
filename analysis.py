import yaml
import argparse
import subprocess
import os
import sys
import shutil
import enum

DIFFKEMP_OUT_FILENAME = "diffkemp-out.yaml"


def build_library_snapshots(args, library_config):
    """Build snapshots of a given library based on its config."""
    library_name = library_config["name"]
    source_dir = os.path.join(args.libraries, library_name)
    snapshots_dir = os.path.join(args.snapshots, library_name)

    # Create the appropriate directory for the snapshots
    os.makedirs(snapshots_dir, exist_ok=True)

    # Create the function list if it does not exist or if --rebuild is set
    function_list_path = os.path.join(snapshots_dir, "function-list")
    if not os.path.isfile(function_list_path) or args.rebuild:
        with open(function_list_path, "w") as function_list_file:
            for function_name in library_config["functions"]:
                function_list_file.write(f"{function_name}\n")

    # Build the library for each git tag if necessary
    for tag in library_config["tags"]:
        tag_dir = os.path.join(snapshots_dir, tag)

        # Skip this tag if already built and --rebuild is not set
        if os.path.isdir(tag_dir) and not args.rebuild:
            print(f"Skipping the build of {library_name} @ {tag}.")
            continue
        print(f"Building {library_name} @ {tag}.")

        # Run git reset to be able to do a clean checkout
        git_reset_command = ["git", "reset", "--hard"]
        if args.verbose:
            print(" ".join(git_reset_command))
        subprocess.check_output(
            git_reset_command,
            cwd=source_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

        # Checkout to the desired tag
        git_checkout_command = ["git", "checkout", tag]
        if args.verbose:
            print(" ".join(git_checkout_command))
        subprocess.check_output(
            git_checkout_command,
            cwd=source_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

        # Build the library using diffkemp build
        build_command = [
            args.diffkemp,
            "build",
            source_dir,
            tag_dir,
            function_list_path,
            "--clang-append=" + library_config["clang-append"],
            "--target=" + library_config["target"],
        ]
        if args.verbose:
            print(" ".join(build_command))
        subprocess.check_output(
            build_command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
        )


class DiffType(enum.StrEnum):
    NoDiff = enum.auto()
    Syntactic = enum.auto()
    Semantic = enum.auto()
    Unknown = enum.auto()


def compare_function(args, function_name, old_tag_dir, new_tag_dir):
    """Compare a function across two snapshots using diffkemp."""
    compare_command = [
        args.diffkemp,
        "compare",
        "--full-diff",
        "--function",
        function_name,
        old_tag_dir,
        new_tag_dir,
    ]

    old_tag = os.path.basename(old_tag_dir)
    new_tag = os.path.basename(new_tag_dir)
    print(f"Comparing {function_name} between {old_tag} and {new_tag}.")
    if args.verbose:
        print(" ".join(compare_command))

    # Run diffkemp compare and obtain the name of the result directory
    compare_result = subprocess.run(compare_command, capture_output=True)
    compare_result.check_returncode()

    if "unknown" in compare_result.stdout.decode():
        return DiffType.Unknown

    dir = compare_result.stdout.decode().strip().split()[-1]

    # Load the yaml output
    with open(os.path.join(dir, DIFFKEMP_OUT_FILENAME), "r") as res_file:
        diffkemp_out = yaml.safe_load(res_file)

    diff_type = DiffType.NoDiff

    # The 'results' dict is non-empty for semantically different functions,
    # Diffkemp outputs a diff file for syntactically different functions
    if diffkemp_out["results"]:
        diff_type = DiffType.Semantic
    elif len(os.listdir(dir)) > 1:
        diff_type = DiffType.Syntactic

    shutil.rmtree(dir)
    return diff_type


def compare_snapshots(args, functions, old_tag_dir, new_tag_dir):
    """Compare a list of functions across two snapshots using diffkemp."""
    results = {
        DiffType.NoDiff.value: [],
        DiffType.Syntactic.value: [],
        DiffType.Semantic.value: [],
        DiffType.Unknown.value: [],
    }
    for function_name in functions:
        diff_type = compare_function(
            args, function_name, old_tag_dir, new_tag_dir
        )
        results[diff_type.value].append(function_name)
    return results


def export_results(args, library_name, results):
    """Export (or print out) results of a single library analysis."""
    if args.output:
        os.makedirs(args.output, exist_ok=True)
        out_file_path = os.path.join(args.output, f"{library_name}.yml")
        print(f"Exporting results to {out_file_path}")
        with open(out_file_path, "w") as out_file:
            yaml.safe_dump(results, out_file)
    else:
        yaml.safe_dump(results, sys.stdout, sort_keys=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--diffkemp", required=True)
    parser.add_argument("--libraries", required=True)
    parser.add_argument("--snapshots", required=True)
    parser.add_argument("--output")
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    with open(args.config, "r") as config_file:
        config = yaml.safe_load(config_file)

    for library_config in config:
        build_library_snapshots(args, library_config)

    for library_config in config:
        tags = library_config["tags"]
        name = library_config["name"]
        results = []
        for old_tag, new_tag in zip(tags, tags[1:]):
            results.append(
                {
                    "old_tag": old_tag,
                    "new_tag": new_tag,
                    "results": compare_snapshots(
                        args,
                        library_config["functions"],
                        os.path.join(args.snapshots, name, old_tag),
                        os.path.join(args.snapshots, name, new_tag),
                    ),
                }
            )
        export_results(args, name, results)


if __name__ == "__main__":
    sys.exit(main())
