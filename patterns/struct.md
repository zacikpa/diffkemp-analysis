# Multiple variables grouped into a struct
- library: MbedTLS 2
- versions: 2.24.0 vs 2.25.0
- function: `mbedtls_md5`

## Old version
Each variable stands separately.

```c
uint32_t *RK, X0, X1, X2, X3, Y0, Y1, Y2, Y3;
RK = ctx->rk;
```

## New version
The variables are held within an anonymous struct.

```c
struct
{
    uint32_t X[16], A, B, C, D;
} local;
```
