#!/usr/bin/python3

import sys
import os
import yaml
import argparse

RESULTS_FILENAME = "results.yml"
DIFFKEMP_OUT_FILENAME = "diffkemp-out.yaml"

def parse_args():
    parser = argparse.ArgumentParser(
        description="Given results of analysis.py, prepare a template for manual evaluation."
    )
    parser.add_argument(
        "results",
        help="path to the results directory",
    )
    parser.add_argument(
        "--output",
        default="template.yml",
        help="path to the output template file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    results_filepath = os.path.join(args.results, RESULTS_FILENAME)
    diffkemp_out_filepath = os.path.join(args.results, DIFFKEMP_OUT_FILENAME)

    if not os.path.exists(results_filepath):
        print(f"File {results_filepath} does not exist.")
        sys.exit(1)
    
    if not os.path.exists(diffkemp_out_filepath):
        print(f"File {diffkemp_out_filepath} does not exist.")
        sys.exit(1)

    with open(results_filepath, "r") as results_file:
        results = yaml.safe_load(results_file)

    output = {"semantic": {}, "syntactic": {}}
    for release, functions in results.items():
        output["semantic"][release] = {}
        output["syntactic"][release] = {}
        for function, result in functions.items():
            if result in ["semantic", "syntactic"]:
                output[result][release][function] = {"category": "", "comment": ""}

    template_dir = os.path.dirname(args.output)
    if template_dir and not os.path.exists(template_dir):
        os.makedirs(template_dir, exist_ok=True)

    with open(args.output, "w") as output_file:
        yaml.safe_dump(output, output_file)
