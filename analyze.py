import argparse
import subprocess
import os
import sys
import filecmp
import shutil
import yaml
from comparison import Comparator, ComparisonResults

OUTPUT_FILENAME = "results.yml"


def parse_args():
    """Prepare the parser of command-line arguments and parse them."""
    parser = argparse.ArgumentParser(
        description="Compare multiple versions of C projects using Diffkemp."
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
        "--sources",
        required=True,
        help="path to the directory containing project sources",
    )
    parser.add_argument(
        "--snapshots",
        required=True,
        help="path to the directory where project snapshots will be stored",
    )
    parser.add_argument(
        "--builds",
        required=True,
        help="path to the directory where built projects will be stored",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="path to the directory where the results will be stored",
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
        "--additional-args", help="additional arguments to pass to Diffkemp compare"
    )
    parser.add_argument(
        "--custom-patterns", help="directory with custom patterns for Diffkemp"
    )
    return parser.parse_args()


def build_snapshots(args, project_config):
    """Build snapshots of a given project based on its config."""
    project_name = project_config["name"]
    source_dir = os.path.join(args.sources, project_name)
    snapshots_dir = os.path.join(args.snapshots, project_name)
    builds_dir = os.path.join(args.builds, project_name)

    # Create the appropriate directory for the build and snapshots
    os.makedirs(snapshots_dir, exist_ok=True)
    os.makedirs(builds_dir, exist_ok=True)

    # Check if there is an existing function list
    # and if it is the same as the current one.
    tmp_function_list_path = os.path.join("/tmp", "function-list")
    function_list_path = os.path.join(snapshots_dir, "function-list")
    with open(tmp_function_list_path, "w") as function_list_file:
        for function_name in project_config["functions"]:
            function_list_file.write(f"{function_name}\n")
    can_skip_builds = False
    if os.path.isfile(function_list_path):
        if filecmp.cmp(tmp_function_list_path, function_list_path):
            can_skip_builds = True
        os.remove(function_list_path)
    shutil.move(tmp_function_list_path, function_list_path)

    # Build the project for each git tag if necessary
    for tag in project_config["tags"]:
        tag_dir = os.path.join(snapshots_dir, tag)
        build_dir = os.path.join(builds_dir, tag)

        # Skip this tag if already built and --rebuild is not set
        if os.path.isdir(tag_dir) and not args.rebuild and can_skip_builds:
            print(f"Skipping the build of {project_name} @ {tag}.")
            continue
        print(f"Building {project_name} @ {tag}.")

        # Copy source files to the build directory
        shutil.rmtree(build_dir, ignore_errors=True)
        shutil.copytree(source_dir, build_dir, symlinks=True)

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
        if "config-commands" in project_config:
            for command in project_config["config-commands"]:
                if args.verbose:
                    print(command)
                subprocess.check_output(
                    command,
                    cwd=build_dir,
                )

        # Construct the build command and build the project
        build_command = [
            args.diffkemp,
            "build",
            build_dir,
            tag_dir,
            function_list_path,
        ]
        if "clang-append" in project_config:
            build_command.extend(
                map(
                    lambda opt: f"--clang-append={opt}",
                    project_config["clang-append"],
                )
            )
        if "target" in project_config:
            build_command.append("--target=" + project_config["target"])
        if args.verbose:
            print(" ".join(build_command))
        subprocess.check_output(build_command)


def main():
    args = parse_args()

    with open(args.config, "r") as config_file:
        config = yaml.safe_load(config_file)

    for project_config in config:
        build_snapshots(args, project_config)

    # If the results already exist, load them
    output_yml = os.path.join(args.output, OUTPUT_FILENAME)
    if os.path.isfile(output_yml) and not args.recompare:
        old_results = ComparisonResults(output_yml)
    else:
        old_results = ComparisonResults()

    comparator = Comparator(args.verbose, args.diffkemp, args.snapshots, old_results)

    for project_config in config:
        tags = project_config["tags"]
        project = project_config["name"]
        functions = project_config["functions"]

        has_custom_patterns = project_config.get("custom-patterns", False)
        if has_custom_patterns and args.custom_patterns:
            custom_patterns = os.path.join(args.custom_patterns, project, "config.yml")
        else:
            custom_patterns = None

        for old_tag, new_tag in zip(tags, tags[1:]):
            comparator.compare_snapshots(
                project,
                old_tag,
                new_tag,
                functions,
                custom_patterns,
                args.output,
                args.additional_args,
            )

    comparator.get_results().export(output_yml)

    stats_file = os.path.join(args.output, "stats.yml")
    comparator.get_results().export_stats(stats_file)

    if args.print_stats:
        with open(stats_file, "r") as stats_file:
            print(stats_file.read())


if __name__ == "__main__":
    sys.exit(main())
