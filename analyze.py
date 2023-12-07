#!/usr/bin/python3

import argparse
import os
import sys
import yaml
from compare import Comparator, ComparisonResults, DiffType
from build import build_snapshot, clone_repository
from blame import CommitLinkFinder


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
        "--review-template",
        action="store_true",
        help="prepare a template for manual evaluation",
    )
    parser.add_argument(
        "--disable-patterns",
        help="comma-separated list of built-in patterns to disable",
    )
    parser.add_argument(
        "--custom-patterns", help="file with custom pattern configuration for Diffkemp"
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

    # Create the output directory
    output_dir = os.path.join(args.output, project_name)
    os.makedirs(output_dir, exist_ok=True)
    results_file_path = os.path.join(output_dir, "results.yml")

    # If the user does not want to compare the snapshots, exit
    if args.no_compare:
        return

    if os.path.exists(results_file_path):
        print("Skipping comparison, results already exist.")
        results = ComparisonResults.load(results_file_path)
    else:
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
        results = comparator.get_results()
        results.export(results_file_path)

    stats_file_path = os.path.join(output_dir, "stats.yml")
    results.export_stats(stats_file_path)

    if not args.review_template:
        return

    # Prepare templates for manual evaluation
    template_semantic = {}
    template_syntactic = {}

    print("Preparing templates for manual evaluation.")
    for old_tag, new_tag in zip(tags, tags[1:]):
        key = ComparisonResults.key(old_tag, new_tag)
        template_semantic[key] = {}
        template_syntactic[key] = {}
        diffkemp_out_dir = os.path.join(output_dir, f"{old_tag}-{new_tag}")
        diffkemp_out_file = os.path.join(diffkemp_out_dir, "diffkemp-out.yaml")
        with open(diffkemp_out_file, "r") as diffkemp_out:
            diffkemp_out = yaml.safe_load(diffkemp_out)
        commit_link_finder = CommitLinkFinder(
            args.verbose, source_dir, old_tag, new_tag, diffkemp_out
        )
        tag_results = results.get(old_tag, new_tag)
        for function, function_result in tag_results.items():
            if function_result == DiffType.SEMANTIC.value:
                template_semantic[key][function] = {
                    "category": "",
                    "comment": "",
                    "commits": commit_link_finder.get_commit_links(function),
                }
            elif function_result == DiffType.SYNTACTIC.value:
                template_syntactic[key][function] = {
                    "category": "",
                    "comment": "",
                }

    template_semantic_file_path = os.path.join(output_dir, "template-semantic.yml")
    print(f"Exporting template to {template_semantic_file_path}.")
    with open(template_semantic_file_path, "w") as template_file:
        yaml.safe_dump(template_semantic, template_file)

    template_syntactic_file_path = os.path.join(output_dir, "template-syntactic.yml")
    print(f"Exporting template to {template_syntactic_file_path}.")
    with open(template_syntactic_file_path, "w") as template_file:
        yaml.safe_dump(template_syntactic, template_file)


if __name__ == "__main__":
    sys.exit(main())
