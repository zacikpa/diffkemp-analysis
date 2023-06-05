# Pointer and offset instead of two pointers
- library: MbedTLS 3
- versions: 3.2.1 vs 3.3.0
- function: `mbedtls_aes_encrypt_ecb`

## Old version
The `rk` pointer points somewhere inside `buf`.

```c
typedef struct mbedtls_aes_context
{
    int nr;
    uint32_t *rk;
    uint32_t buf[68];
}
mbedtls_aes_context;
```

## New version
To get `rk`, use pointer arithmetic (`buf + rk_offset`).

```c
typedef struct mbedtls_aes_context
{
    int nr;
    size_t rk_offset; 
    uint32_t buf[68];
}
mbedtls_aes_context;
```
