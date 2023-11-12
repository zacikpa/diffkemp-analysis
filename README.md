# Diffkemp analysis
This is a useful tool for performing experiments with Diffkemp. 
It can build and subsequently compare multiple versions of provided C projects.

## Usage
The tool requires a YAML configuration file which may look as follows:
```yaml
- name: mbedtls                  # The first project to analyze
  tags:                          # Versions to compare
    - mbedtls-3.0.0
    - mbedtls-3.1.0
    - mbedtls-3.2.0
  functions:                     # Functions to compare
    - mbedtls_aes_crypt_ecb
    - mbedtls_aes_crypt_cbc
    - mbedtls_aes_crypt_xts
  clang-append:                  # Clang flags to use when building the project
    - -g
  target: no_test                # The build target to use

- name: gnutls
  tags:
    - gnutls_3_3_20
    - gnutls_3_3_21
    - gnutls_3_3_22
  functions:
    - chacha_crypt
    - cbc_encrypt
    - cbc_decrypt
  clang-append:
    - -g
```

With the configuration set (e.g., in `config.yml`), the tool itself is executed using:
```bash
python analyze.py \
       --config config.yml \
       --diffkemp ${DIFFKEMP_EXECUTABLE} \
       --sources ${DIR_SOURCES} \
       --builds ${DIR_BUILDS} \
       --snapshots ${DIR_SNAPSHOTS}  \
       --output results.yml \
       --print-stats
```

In our example, the tool will perform the following steps:

1. It will look for project sources in `<DIR_SOURCES>/mbedtls/` and
`<DIR_SOURCES>/gnutls/`. Each project directory must be a git repository and
it must be possible to checkout each compared release as a tag. For instance,
it must be possible to checkout `mbedtls-3.0.0` in the `mbedtls` soruce
directory.

2. The tool will checkout to each release and copy the sources to `<DIR_BUILDS>`
(e.g., to `<DIR_BUILDS>/mbedtls/mbedtls-3.0.0`).

3. From each build directory, Diffkemp will compile the project into a snapshot
in `<DIR_SNAPSHOTS>` (e.g., to `<DIR_SNAPSHOTS>/mbedtls/mbedtls-3.0.0/`).

4. Using Diffkemp, the tool will compare all consecutive pairs of releases for
each project.

The results will be output into `results.yml` in the following form:
```yaml
mbedtls:
  mbedtls-3.0.0 -> mbedtls-3.1.0:
    mbedtls_aes_crypt_ecb: nodiff
    mbedtls_aes_crypt_cbc: syntactic 
    mbedtls_aes_crypt_xts: semantic
  mbedtls-3.1.0 -> mbedtls-3.2.0:
    mbedtls_aes_crypt_ecb: nodiff
    mbedtls_aes_crypt_cbc: nodiff 
    mbedtls_aes_crypt_xts: nodiff
gnutls:
  gnutls-3_3_20 -> gnutls_3_3_21:
    chacha_crypt: semantic
    cbc_encrypt: syntactic
    cbc_decrypt: syntactic
  gnutls-3_3_21 -> gnutls_3_3_22:
    chacha_crypt: unknown
    cbc_encrypt: syntactic
    cbc_decrypt: syntactic
```

Additionally, if `--print-stats` is set, the tool will print basic result statistics
for each project.

There are 4 kinds of results:
- `nodiff`: there was no syntactic difference between the two versions of the
compared function,
- `syntactic`: the C source of the function changed, but Diffkemp resolved the
difference as semantics-preserving,
- `semantic`: Diffkemp found a semantic difference between the two versions of the
function,
- `unknown`: Diffkemp was unable to compare the function versions.
