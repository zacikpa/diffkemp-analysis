# Multiple variables grouped into a struct
- library: MbedTLS 2
- versions: 2.24.0 vs 2.25.0
- function: `mbedtls_md5`

## Old version
Each variable stands separately.

```c
uint32_t X[16], A, B, C, D;
```

## New version
The variables are held within an anonymous struct.

```c
struct
{
    uint32_t X[16], A, B, C, D;
} local;
```
