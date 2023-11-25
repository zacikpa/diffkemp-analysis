# C project stability analysis using DiffKemp
This is a tool for performing experiments with DiffKemp.
It can build and subsequently compare multiple versions of a provided C project.

## Usage
The tool requires a YAML configuration file which may look as follows:
```yaml
# Name of the analyzed project
name: libsodium
# URL of the git repository where the project is maintained
git: https://github.com/jedisct1/libsodium.git
# Commands to run before the project can be built
config-commands:
  - ./autogen.sh
  - ./configure
# Additional Clang flags to use when building the project
clang-append:
  - -g
  - -O2
# The build target to use
target: no_test
# Project versions to analyze: all consecutive pairs of versions
# are compared
tags:
  - 1.0.17
  - 1.0.18
  - 1.0.19
# Functions to compare between each version pair
functions:
  - crypto_auth
  - crypto_auth_verify
```

With the configuration set (e.g., in `config.yml`), the tool itself is executed using:
```bash
python analyze.py --config config.yml --output results
```

In our example, the tool will perform the following steps:

1. It will clone the git repository of `libsodium`.

2. The tool will checkout to each provided tag and build `libsodium` into a
   DiffKemp snapshot.

4. Using Diffkemp, the tool will compare all consecutive pairs of snapshots.

The results will be exported into a file in the provided output directory in
the following form.
```yaml
1.0.17 -> 1.0.18:
  crypto_auth: syntactic
  crypto_auth_verify: unknown
1.0.18 -> 1.0.19:
  crypto_auth: syntactic
  crypto_auth_verify: nodiff
```

There are 4 kinds of results:
- `nodiff`: there was no syntactic difference nor a semantic difference
found between the two versions of the compared function,
- `syntactic`: the C source of the function changed, but Diffkemp
resolved the difference as semantics-preserving,
- `semantic`: Diffkemp reported a semantic difference between the two versions
of the function,
- `unknown`: Diffkemp was unable to compare the function versions, most likely
because the function does not exist in the older version.
