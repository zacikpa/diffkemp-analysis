#!/usr/bin/python3

import argparse
import yaml
import enum
from compare import ComparisonResults, DiffType

CATEGORY_KEY = "category"


class SynResult(enum.StrEnum):
    TRIVIAL = enum.auto()
    NON_TRIVIAL = enum.auto()
    WRONG = enum.auto()


class SemResult(enum.StrEnum):
    UNKNOWN = enum.auto()
    SIMPLE = enum.auto()
    COMPLEX = enum.auto()
    GENUINE = enum.auto()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize the complete results after manual review."
    )
    parser.add_argument(
        "original_results",
        help="path to the original results",
    )
    parser.add_argument(
        "semantic_review",
        help="path to the semantic manual review results",
    )
    parser.add_argument(
        "syntactic_review",
        help="path to the syntactic manual review results",
    )
    parser.add_argument(
        "--output",
        default="summary.yml",
        help="path to the directory where the summary will be stored",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    original_stats = ComparisonResults.load(args.original_results).get_stats()

    with open(args.semantic_review, "r") as f:
        semantic_review = yaml.safe_load(f)

    with open(args.syntactic_review, "r") as f:
        syntactic_review = yaml.safe_load(f)

    summary = {
        tag_key: {
            DiffType.SEMANTIC.value: {},
            DiffType.SYNTACTIC.value: {},
        }
        for tag_key in original_stats.keys()
    }

    for tag_key, tag_stats in original_stats.items():
        summary[tag_key][DiffType.NO_DIFF.value] = original_stats[tag_key][
            DiffType.NO_DIFF.value
        ]
        summary[tag_key][DiffType.UNKNOWN.value] = original_stats[tag_key][
            DiffType.UNKNOWN.value
        ]
        semantic_results = [
            semantic_review[tag_key][function][CATEGORY_KEY]
            for function in semantic_review[tag_key].keys()
        ]
        if not all(
            [
                x in [sem_result.value for sem_result in SemResult]
                for x in semantic_results
            ]
        ):
            print(f"WARNING: Unknown semantic review type in {tag_key}.")
        for semantic_review_type in SemResult:
            summary[tag_key][DiffType.SEMANTIC.value][semantic_review_type.value] = len(
                [x for x in semantic_results if x == semantic_review_type.value]
            )
        if syntactic_review is None or tag_key not in syntactic_review:
            summary[tag_key][DiffType.SYNTACTIC.value] = {
                SynResult.TRIVIAL.value: 0,
                SynResult.WRONG.value: 0,
                SynResult.NON_TRIVIAL.value: original_stats[tag_key][
                    DiffType.SYNTACTIC.value
                ],
            }
            continue
        syntactic_results = [
            syntactic_review[tag_key][function][CATEGORY_KEY]
            for function in syntactic_review[tag_key].keys()
        ]
        if not all(
            [
                x in [syn_result.value for syn_result in SynResult]
                for x in syntactic_results
            ]
        ):
            print(f"WARNING: Unknown syntactic review type in {tag_key}.")
        summary[tag_key][DiffType.SYNTACTIC.value][SynResult.TRIVIAL.value] = len(
            [x for x in syntactic_results if x == SynResult.TRIVIAL.value]
        )
        summary[tag_key][DiffType.SYNTACTIC.value][SynResult.WRONG.value] = len(
            [x for x in syntactic_results if x == SynResult.WRONG.value]
        )
        summary[tag_key][DiffType.SYNTACTIC.value][SynResult.NON_TRIVIAL.value] = (
            original_stats[tag_key][DiffType.SYNTACTIC.value]
            - summary[tag_key][DiffType.SYNTACTIC.value][SynResult.TRIVIAL.value]
            - summary[tag_key][DiffType.SYNTACTIC.value][SynResult.WRONG.value]
        )

    summary["total"] = {
        DiffType.SEMANTIC.value: {},
        DiffType.SYNTACTIC.value: {},
        DiffType.NO_DIFF.value: sum(
            [
                summary[tag_key][DiffType.NO_DIFF.value]
                for tag_key in original_stats.keys()
            ]
        ),
        DiffType.UNKNOWN.value: sum(
            [
                summary[tag_key][DiffType.UNKNOWN.value]
                for tag_key in original_stats.keys()
            ]
        ),
    }
    for review_type in SemResult:
        summary["total"][DiffType.SEMANTIC.value][review_type.value] = sum(
            [
                summary[tag_key][DiffType.SEMANTIC.value][review_type.value]
                for tag_key in original_stats.keys()
            ]
        )
    summary["total"][DiffType.SEMANTIC.value]["total"] = sum(
        [
            summary["total"][DiffType.SEMANTIC.value][review_type.value]
            for review_type in SemResult
        ]
    )

    for review_type in SynResult:
        summary["total"][DiffType.SYNTACTIC.value][review_type.value] = sum(
            [
                summary[tag_key][DiffType.SYNTACTIC.value][review_type.value]
                for tag_key in original_stats.keys()
            ]
        )
    summary["total"][DiffType.SYNTACTIC.value]["total"] = sum(
        [
            summary["total"][DiffType.SYNTACTIC.value][review_type.value]
            for review_type in SynResult
        ]
    )

    with open(args.output, "w") as output:
        yaml.safe_dump(summary, output)
