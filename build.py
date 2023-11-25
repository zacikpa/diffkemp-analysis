import subprocess
import shutil
import os


def clone_repository(verbose, repo_url, source_dir):
    """Clone a repository."""
    os.makedirs(source_dir, exist_ok=True)
    git_clone_command = ["git", "clone", repo_url, source_dir]
    if verbose:
        print(" ".join(git_clone_command))
    subprocess.check_output(git_clone_command)


def build_snapshot(verbose, diffkemp, config, tag, source_dir, build_dir, snapshot_dir):
    """Build a snapshot of a project for the release specified by a tag."""
    # Create the appropriate directory for the build and snapshot
    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(snapshot_dir, exist_ok=True)

    # Copy source files to the build directory
    shutil.rmtree(build_dir, ignore_errors=True)
    shutil.copytree(source_dir, build_dir, symlinks=True)

    # Run git reset to be able to do a clean checkout
    git_reset_command = ["git", "reset", "--hard"]
    if verbose:
        print(" ".join(git_reset_command))
    subprocess.check_output(
        git_reset_command,
        cwd=build_dir,
    )

    # Run git clean to remove any untracked files
    git_clean_command = ["git", "clean", "-fdx"]
    if verbose:
        print(" ".join(git_clean_command))
    subprocess.check_output(
        git_clean_command,
        cwd=build_dir,
    )

    # Checkout to the desired tag
    git_checkout_command = ["git", "checkout", "--recurse-submodules", tag]
    if verbose:
        print(" ".join(git_checkout_command))
    subprocess.check_output(
        git_checkout_command,
        cwd=build_dir,
    )

    # Run the configuration commands if necessary
    if "config-commands" in config:
        for command in config["config-commands"]:
            if verbose:
                print(command)
            subprocess.check_output(
                command,
                cwd=build_dir,
                shell=True,
            )

    # Export a list of functions to analyze
    function_list_path = os.path.join(snapshot_dir, "function-list")
    with open(function_list_path, "w") as function_list_file:
        for function_name in config["functions"]:
            function_list_file.write(f"{function_name}\n")

    # Construct the build command and build the project
    build_command = [
        diffkemp,
        "build",
        build_dir,
        snapshot_dir,
        function_list_path,
    ]
    if "clang-append" in config:
        build_command.extend(
            map(lambda opt: f"--clang-append={opt}", config["clang-append"])
        )
    if "target" in config:
        build_command.append("--target=" + config["target"])
    if verbose:
        print(" ".join(build_command))
    subprocess.check_output(build_command)
