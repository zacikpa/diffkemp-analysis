#!/usr/bin/python3

import argparse
import os
import sys
import yaml
from compare import Comparator
from build import build_snapshot, clone_repository


def parse_args():
    """Prepare the parser of command-line arguments and parse them."""
    parser = argparse.ArgumentParser(
        description="Compare multiple versions of a C project using Diffkemp."
    )
    parser.add_argument(
        "config",
        help="path to the configuration file, see README.md for details",
    )
    parser.add_argument(
        "--output",
        default="results",
        help="path to the directory where the results will be stored",
    )
    parser.add_argument(
        "--diffkemp", default="diffkemp", help="path to the DiffKemp executable"
    )
    parser.add_argument(
        "--sources",
        default="sources",
        help="path to the directory where project sources will be stored",
    )
    parser.add_argument(
        "--snapshots",
        default="snapshots",
        help="path to the directory where project snapshots will be stored",
    )
    parser.add_argument(
        "--builds",
        default="builds",
        help="path to the directory where built projects will be stored",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="rebuild all project versions even if the snapshots already exist",
    )
    parser.add_argument(
        "--no-compare",
        action="store_true",
        help="do not compare the project versions, only build them",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print out all executed commands",
    )
    parser.add_argument(
        "--disable-patterns", help="comma-separated list of built-in patterns to disable"
    )
    parser.add_argument(
        "--custom-patterns", help="directory with custom patterns for Diffkemp"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load the configuration file
    with open(args.config, "r") as config_file:
        config = yaml.safe_load(config_file)

    project_name = config["name"]
    tags = config["tags"]
    source_dir = os.path.join(args.sources, project_name)
    output_dir = os.path.join(args.output, project_name)
    snapshots_dir = os.path.join(args.snapshots, project_name)
    os.makedirs(snapshots_dir, exist_ok=True)

    # If the source directory does not exist, clone the repository
    if not os.path.isdir(source_dir):
        clone_repository(args.verbose, config["git"], source_dir)

    # Build all snapshots
    for tag in tags:
        build_dir = os.path.join(args.builds, project_name, tag)
        snapshot_dir = os.path.join(snapshots_dir, tag)
        if os.path.isdir(snapshot_dir) and not args.rebuild:
            print(f"Skipping the build of {project_name} @ {tag}.")
            continue
        print(f"Building {project_name} @ {tag}.")
        build_snapshot(
            args.verbose,
            args.diffkemp,
            config,
            tag,
            source_dir,
            build_dir,
            snapshot_dir,
        )

    # If the user does not want to compare the snapshots, exit
    if args.no_compare:
        return

    # Create the output directory
    output_dir = os.path.join(args.output, project_name)
    os.makedirs(output_dir, exist_ok=True)

    # Compare consecutive pairs of snapshots
    comparator = Comparator(
        args.verbose,
        args.diffkemp,
        config,
        snapshots_dir,
        output_dir,
        args.custom_patterns,
        args.disable_patterns,
    )
    for old_tag, new_tag in zip(tags, tags[1:]):
        comparator.compare_snapshots(old_tag, new_tag)

    # Export the results and statistics
    results_file_path = os.path.join(output_dir, "results.yml")
    comparator.get_results().export(results_file_path)
    stats_file_path = os.path.join(output_dir, "stats.yml")
    comparator.get_results().export_stats(stats_file_path)


if __name__ == "__main__":
    sys.exit(main())
