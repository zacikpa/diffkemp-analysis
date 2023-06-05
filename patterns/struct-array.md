# Multiple variables grouped into an array within a new struct 
- library: MbedTLS 2
- versions: 2.24.0 vs 2.25.0
- function: `mbedtls_aes_crypt_ecb`

## Old version
Each variable stands separately.

```c
uint32_t X[16], A, B, C, D;
```

## New version
Eight variables are held within an anonymous struct with 2 fixed-size arrays.

```c
uint32_t *RK = ctx->rk;
struct
{
    uint32_t X[4];
    uint32_t Y[4];
} t;
```
