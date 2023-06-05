# Buffer initialization
- library: MbedTLS 3
- versions: 3.1.0 vs 3.2.0
- function: `mbedtls_gcm_crypt_and_tag`

## Old version
The buffer is not initialized since it is used for output.

```c
unsigned char ectr[16];
```

The resulting LLVM IR:

```llvm
%9 = alloca [16 x i8], align 16
call void @llvm.lifetime.start.p0(i64 16, ptr nonnull %9) #13
```

## New version
The buffer is explicitly initialized to 0.

```c
unsigned char ectr[16] = {0};
```

The resulting LLVM IR:

```llvm
%9 = alloca [16 x i8], align 16
call void @llvm.lifetime.start.p0(i64 16, ptr nonnull %9) #13
call void @llvm.memset.p0.i64(ptr noundef nonnull align 16 dereferenceable(16) %9, i8 0, i64 16, i1 false)

```
