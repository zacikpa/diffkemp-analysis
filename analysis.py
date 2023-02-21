import yaml
import argparse
import subprocess
import pathlib
import os
import sys
from diffkemp.snapshot import Snapshot


def function_module(snapshot_path, function):
    """Given a snapshot path and a function name, returns the module where the function is defined."""
    snapshot = Snapshot.load_from_dir(snapshot_path)
    if snapshot.get_by_name(function) is None:
        return None
    return snapshot.get_by_name(function).mod.llvm


def build_snapshots(args, library):
    """Build snapshots of the given library for all tags."""
    library_path = os.path.join(args.libraries, library['name'])

    # Create the appropriate directory for the snapshot
    pathlib.Path(os.path.join(args.snapshots, library['name'])).mkdir(parents=True, exist_ok=True)

    # Create the function list file
    function_list_path = os.path.join(args.snapshots, library['name'], 'function-list')
    with open(function_list_path, 'w') as function_list_file:
        for function in library['functions']:
            function_list_file.write(f'{function}\n')
    
    # Build the library for each git tag
    for tag in library['tags']: 
        snapshot_path = os.path.join(args.snapshots, library['name'], tag)
        build_command = [args.diffkemp, 'build', library_path, snapshot_path, function_list_path]
        build_command += ['--clang-append=' + library['clang_append']]
        build_command += ['--target=' + library['target']]
        subprocess.run(['git', 'reset', '--hard'], cwd=library_path)
        subprocess.run(['git', 'checkout', tag], cwd=library_path)
        subprocess.run(build_command)


def diffkemp_compare_snapshots(args, function, old_snapshot_path, new_snapshot_path):
    """Compare a function across two snapshots using diffkemp compare."""
    compare_command = [args.diffkemp]
    if args.verbose:
        compare_command += ['-v']
    compare_command += ['compare', '--disable-simpll-ffi', '--stdout'] 
    compare_command += ['--function', function]
    compare_command += [old_snapshot_path, new_snapshot_path]
    compare_result = subprocess.run(compare_command, capture_output=True)
    return 1 if b'differs' in compare_result.stdout else 0


def llvm_diff_snapshots(args, function, old_snapshot_path, new_snapshot_path):
    """Compare a function across two snapshots using diff on llvm IR."""
    old_module_path = function_module(old_snapshot_path, function)
    new_module_path = function_module(new_snapshot_path, function)
    compare_command = [args.llvm_diff, function, old_module_path, new_module_path]
    return subprocess.run(compare_command).returncode


def llvm_compare_snapshots(args, function, old_snapshot_path, new_snapshot_path):
    """Compare a function across two snapshots using the built-in llvm function comparator."""
    old_module_path = function_module(old_snapshot_path, function)
    new_module_path = function_module(new_snapshot_path, function)
    compare_command = [args.llvm_compare, function, old_module_path, new_module_path]
    return subprocess.run(compare_command).returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--to-compare')
    parser.add_argument('--diffkemp')
    parser.add_argument('--libraries')
    parser.add_argument('--snapshots')
    parser.add_argument('--llvm-compare')
    parser.add_argument('--llvm-diff')
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    with open(args.to_compare) as to_compare_file:
        to_compare = yaml.safe_load(to_compare_file)

    for library in to_compare:
        llvm_diff_count = 0
        llvm_compare_count = 0
        diffkemp_compare_count = 0
        weird_count = 0
        total_count = 0
        weird = []
        if args.rebuild:
            build_snapshots(args, library)
        for (old_tag, new_tag) in list(zip(library['tags'], library['tags'][1:])):
            print(old_tag, new_tag)
            old_snapshot_path = os.path.join(args.snapshots, library['name'], old_tag)
            new_snapshot_path = os.path.join(args.snapshots, library['name'], new_tag)
            for function in library['functions']:
                print('\t' + function)
                llvm_diff_code = llvm_diff_snapshots(args, function, old_snapshot_path, new_snapshot_path)
                llvm_compare_code = llvm_compare_snapshots(args, function, old_snapshot_path, new_snapshot_path)
                diffkemp_code = diffkemp_compare_snapshots(args, function, old_snapshot_path, new_snapshot_path)
                total_count += 1
                if llvm_diff_code:
                    llvm_diff_count += 1
                if llvm_compare_code:
                    llvm_compare_count += 1
                if diffkemp_code:
                    diffkemp_compare_count += 1
                print('\t\tllvm-diff:', llvm_diff_code)
                print('\t\tllvm compare:', llvm_compare_code)
                print('\t\tdiffkemp compare:', diffkemp_code)
                if not llvm_diff_code and diffkemp_code:
                    weird.append((old_tag, new_tag, function))
                    weird_count += 1
        print()
        print("llvm-diff count:", llvm_diff_count)
        print("llvm compare count:", llvm_compare_count)
        print("diffkemp compare count:", diffkemp_compare_count)
        print("total count:", total_count)
        print("weird count:", weird_count)
        print(weird)


if __name__ == '__main__':
    sys.exit(main())