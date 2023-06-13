# Library analyser
This is a useful tool for performing experiments with Diffkemp. 
It can build and subsequently compare multiple versions of provided C projects.

## Usage
The tool requires a YAML configuration file which may look as follows:
```yaml
- name: mbedtls                  # The first library to analyze
  tags:                          # Versions to compare
    - mbedtls-3.0.0
    - mbedtls-3.1.0
    - mbedtls-3.2.0
  functions:                     # Functions to compare
    - mbedtls_aes_crypt_ecb
    - mbedtls_aes_crypt_cbc
    - mbedtls_aes_crypt_xts
  clang-append:                  # Clang flags to use when building the library
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
python library_analyser.py \
       --config config.yml \
       --diffkemp ${PATH_TO_DIFFKEMP} \
       --libraries ${DIR_WITH_LIBRARIES_SOURCES} \
       --snapshots ${DIR_TO_OUTPUT_SNAPSHOTS}  \
       --output results.yml \
       --print-stats
```

In this example, the tool will look for library sources in `<DIR_WITH_LIBRARIES_SOURCES>/mbedtls/` and
`<DIR_WITH_LIBRARIES_SOURCES>/gnutls/`. Diffkemp will compile the snapshots into directories such as
`<DIR_TO_OUTPUT_SNAPSHOTS>/mbedtls/mbedtls-3.0.0/` and compare all adjacent pairs of versions, as given
in the configuraion file.

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

Additionally, if `--print-stats` is set, the tool will print basic result statistics for each library.

There are 4 kinds of results:
- `nodiff`: there was no syntactic difference between the two versions of the compared function,
- `syntactic`: the C source of the function changed, but Diffkemp resolved the difference as semantics-preserving,
- `semantic`: Diffkemp found a semantic difference between the two versions of the function,
- `unknown`: Diffkemp was unable to compare the function versions.

