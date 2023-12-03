#!/usr/bin/python3

import sys
import os
import yaml
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Obtain a difference between two results files from analyze.py."
    )
    parser.add_argument(
        "first",
        help="path to the first results file",
    )
    parser.add_argument(
        "second",
        help="path to the second results file",
    )
    parser.add_argument(
        "--output",
        default="diff.yml",
        help="path to the file where the diff will be stored",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not os.path.exists(args.first):
        print(f"File {args.first} does not exist.")
        sys.exit(1)
    if not os.path.exists(args.second):
        print(f"File {args.second} does not exist.")
        sys.exit(1)

    with open(args.first, "r") as first_file:
        first = yaml.safe_load(first_file)
    with open(args.second, "r") as second_file:
        second = yaml.safe_load(second_file)

    if first.keys() != second.keys():
        print("The two files do not contain the same release comparisons.")
        sys.exit(1)

    if not all(
        first[release].keys() == second[release].keys() for release in first.keys()
    ):
        print("The two files do not contain the same function comparisons.")
        sys.exit(1)

    output = {}
    for release, functions in first.items():
        release_output = {}
        for function, result in functions.items():
            if result != second[release][function]:
                release_output[function] = {
                    "first": result,
                    "second": second[release][function],
                }
        if release_output:
            output[release] = release_output

    results_dir = os.path.dirname(args.output)
    if results_dir and not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)

    with open(args.output, "w") as output_file:
        yaml.safe_dump(output, output_file)
