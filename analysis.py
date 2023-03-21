import yaml
import argparse
import subprocess
import os
import sys
import pathlib
import shutil
import enum

DIFFKEMP_OUT_FILENAME = 'diffkemp-out.yaml'


def build_snapshots(args, library):
    """Build snapshots of the given library for all tags."""
    library_path = os.path.join(args.libraries, library['name'])

    # Create the appropriate directory for the snapshot
    pathlib.Path(
        os.path.join(args.snapshots, library['name'])
    ).mkdir(parents=True, exist_ok=True)

    # Create the function list file
    function_list_path = os.path.join(
        args.snapshots, library['name'], 'function-list')
    with open(function_list_path, 'w') as function_list_file:
        for function in library['functions']:
            function_list_file.write(f'{function}\n')

    # Build the library for each git tag
    for tag in library['tags']:
        snapshot_path = os.path.join(args.snapshots, library['name'], tag)
        build_command = [args.diffkemp, 'build',
                         library_path, snapshot_path, function_list_path,
                         '--clang-append=' + library['clang_append'],
                         '--target=' + library['target']]
        subprocess.run(['git', 'reset', '--hard'], cwd=library_path)
        subprocess.run(['git', 'checkout', tag], cwd=library_path)
        subprocess.run(build_command)


class DiffType(enum.Enum):
    NoDiff = 1
    Syntactic = 2
    Semantic = 3


def compare_snapshots(args, function, old_snapshot_path, new_snapshot_path):
    """Compare a function across two snapshots using diffkemp compare."""
    compare_command = [args.diffkemp]
    if args.verbose:
        compare_command += ['-v']
    compare_command += ['compare', '--full-diff', '--function', function,
                        old_snapshot_path, new_snapshot_path]

    # Run diffkemp compare and obtain the name of the result directory
    compare_result = subprocess.run(compare_command, capture_output=True)
    dir = compare_result.stdout.decode().strip().split()[-1]

    # Load the yaml output
    with open(os.path.join(dir, DIFFKEMP_OUT_FILENAME), 'r') as res_file:
        diffkemp_out = yaml.safe_load(res_file)

    diff_type = DiffType.NoDiff
    # The 'results' dict is non-empty for semantically different functions
    if diffkemp_out['results']:
        diff_type = DiffType.Semantic
        if len(os.listdir(dir)) == 1:
            print("Err:", function, old_snapshot_path, new_snapshot_path)
    # Diffkemp outputs a diff file for syntactically different functions
    elif len(os.listdir(dir)) > 1:
        diff_type = DiffType.Syntactic

    shutil.rmtree(dir)
    return diff_type


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--to-compare')
    parser.add_argument('--diffkemp')
    parser.add_argument('--libraries')
    parser.add_argument('--snapshots')
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    with open(args.to_compare) as to_compare_file:
        to_compare = yaml.safe_load(to_compare_file)

    for library in to_compare:
        syn_count = 0
        sem_count = 0
        total_count = 0
        if args.rebuild:
            build_snapshots(args, library)
        for (old_tag, new_tag) in zip(library['tags'], library['tags'][1:]):
            print(old_tag, new_tag)
            old_path = os.path.join(args.snapshots, library['name'], old_tag)
            new_path = os.path.join(args.snapshots, library['name'], new_tag)
            for fun in library['functions']:
                diff_type = compare_snapshots(args, fun, old_path, new_path)
                print(f'\t{fun}: {diff_type}')
                total_count += 1
                if diff_type == DiffType.Semantic:
                    sem_count += 1
                if diff_type == DiffType.Syntactic:
                    syn_count += 1
        print()
        print("Only syntactically different:", syn_count)
        print("Semantically different:", sem_count)
        print("Total number of functions compared:", total_count)


if __name__ == '__main__':
    sys.exit(main())
