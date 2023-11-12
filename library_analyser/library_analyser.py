import yaml
import argparse
import subprocess
import os
import sys
import filecmp
import shutil
from comparison import Comparator, ComparisonResults


def parse_args():
    """Prepare the parser of command-line arguments and parse them."""
    parser = argparse.ArgumentParser(
        description="Compare multiple versions of C libraries using Diffkemp."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="path to the configuration file, see README.md for details",
    )
    parser.add_argument(
        "--diffkemp", required=True, help="path to the DiffKemp executable"
    )
    parser.add_argument(
        "--libraries",
        required=True,
        help="path to the directory containing the libraries",
    )
    parser.add_argument(
        "--snapshots",
        required=True,
        help="path to the directory where library snapshots will be stored",
    )
    parser.add_argument(
        "--builds",
        required=True,
        help="path to the directory where built libraries will be stored",
    )
    parser.add_argument(
        "--output",
        help="path to the file where the results will be stored",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="rebuild the snapshots even if they already exist",
    )
    parser.add_argument(
        "--recompare",
        action="store_true",
        help="rerun all snapshot comparison even if the results already exist",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print out all executed commands",
    )
    parser.add_argument(
        "--print-stats",
        action="store_true",
        help="print out statistics about the results",
    )
    parser.add_argument(
        "--additional-args",
        help="Additional arguments to pass to Diffkemp compare"
    )
    return parser.parse_args()


def build_snapshots(args, library_config):
    """Build snapshots of a given library based on its config."""
    library_name = library_config["name"]
    source_dir = os.path.join(args.libraries, library_name)
    snapshots_dir = os.path.join(args.snapshots, library_name)
    builds_dir = os.path.join(args.builds, library_name)

    # Create the appropriate directory for the build and snapshots
    os.makedirs(snapshots_dir, exist_ok=True)
    os.makedirs(builds_dir, exist_ok=True)

    # Check if there is an existing function list
    # and if it is the same as the current one.
    tmp_function_list_path = os.path.join("/tmp", "function-list")
    function_list_path = os.path.join(snapshots_dir, "function-list")
    with open(tmp_function_list_path, "w") as function_list_file:
        for function_name in library_config["functions"]:
            function_list_file.write(f"{function_name}\n")
    can_skip_builds = False
    if os.path.isfile(function_list_path):
        if filecmp.cmp(tmp_function_list_path, function_list_path):
            can_skip_builds = True
        os.remove(function_list_path)
    shutil.move(tmp_function_list_path, function_list_path)

    # Build the library for each git tag if necessary
    for tag in library_config["tags"]:
        tag_dir = os.path.join(snapshots_dir, tag)
        build_dir = os.path.join(builds_dir, tag)

        # Skip this tag if already built and --rebuild is not set
        if os.path.isdir(tag_dir) and not args.rebuild and can_skip_builds:
            print(f"Skipping the build of {library_name} @ {tag}.")
            continue
        print(f"Building {library_name} @ {tag}.")

        # Copy library source files to the build directory
        shutil.rmtree(build_dir, ignore_errors=True)
        shutil.copytree(source_dir, build_dir)

        # Run git reset to be able to do a clean checkout
        git_reset_command = ["git", "reset", "--hard"]
        if args.verbose:
            print(" ".join(git_reset_command))
        subprocess.check_output(
            git_reset_command,
            cwd=build_dir,
        )

        # Run git clean to remove any untracked files
        git_clean_command = ["git", "clean", "-fdx"]
        if args.verbose:
            print(" ".join(git_clean_command))
        subprocess.check_output(
            git_clean_command,
            cwd=build_dir,
        )

        # Checkout to the desired tag
        git_checkout_command = ["git", "checkout", "--recurse-submodules", tag]
        if args.verbose:
            print(" ".join(git_checkout_command))
        subprocess.check_output(
            git_checkout_command,
            cwd=build_dir,
        )

        # Run the configuration commands if necessary
        if "config-commands" in library_config:
            for command in library_config["config-commands"]:
                if args.verbose:
                    print(command)
                subprocess.check_output(
                    command,
                    cwd=build_dir,
                )

        # Construct the build command and build the library
        build_command = [
            args.diffkemp,
            "build",
            build_dir,
            tag_dir,
            function_list_path,
        ]
        if "clang-append" in library_config:
            build_command.extend(
                map(
                    lambda opt: f"--clang-append={opt}",
                    library_config["clang-append"],
                )
            )
        if "target" in library_config:
            build_command.append("--target=" + library_config["target"])
        if args.verbose:
            print(" ".join(build_command))
        subprocess.check_output(build_command)


def main():
    args = parse_args()

    with open(args.config, "r") as config_file:
        config = yaml.safe_load(config_file)

    for library_config in config:
        build_snapshots(args, library_config)

    # If the results already exist, load them
    if args.output and os.path.isfile(args.output) and not args.recompare:
        old_results = ComparisonResults(args.output)
    else:
        old_results = ComparisonResults()

    comparator = Comparator(
        args.verbose, args.diffkemp, args.snapshots, old_results
    )

    for library_config in config:
        tags = library_config["tags"]
        library = library_config["name"]
        functions = library_config["functions"]
        for old_tag, new_tag in zip(tags, tags[1:]):
            comparator.compare_snapshots(library, old_tag, new_tag, functions, args.additional_args)

    comparator.get_results().export(args.output)

    if args.print_stats:
        comparator.get_results().print_stats()


if __name__ == "__main__":
    sys.exit(main())
