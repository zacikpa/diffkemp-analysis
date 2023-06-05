# Byte-by-byte copying refactored into memcpy 
- library: MbedTLS 3
- versions: 3.3.0 vs 3.4.0
- function: `mbedtls_aes_crypt_ecb`

## Old version
The desired bytes from a buffer are combined using bitwise operations.

```c
uint32_t x = ( (uint32_t) ( data )[( offset )    ]       ) \
           | ( (uint32_t) ( data )[( offset ) + 1] <<  8 ) \
           | ( (uint32_t) ( data )[( offset ) + 2] << 16 ) \
           | ( (uint32_t) ( data )[( offset ) + 3] << 24 )
```

The resulting LLVM IR is quite lengthy:

```llvm
%29 = getelementptr inbounds i8, ptr %1, i64 4
%30 = load i8, ptr %29, align 1
%31 = zext i8 %30 to i32

%32 = getelementptr inbounds i8, ptr %1, i64 5
%33 = load i8, ptr %32, align 1
%34 = zext i8 %33 to i32
%35 = shl nuw nsw i32 %34, 8
%36 = or i32 %35, %31

%37 = getelementptr inbounds i8, ptr %1, i64 6
%38 = load i8, ptr %37, align 1
%39 = zext i8 %38 to i32
%40 = shl nuw nsw i32 %39, 16
%41 = or i32 %36, %40

%42 = getelementptr inbounds i8, ptr %1, i64 7
%43 = load i8, ptr %42, align 1
%44 = zext i8 %43 to i32
%45 = shl nuw i32 %44, 24
%46 = or i32 %41, %45
```

## New version
A single call to `memcpy` is used to copy the content of the buffer into
a new variable. Note that MbedTLS detects the endianity of the system and the
code would be different in big-endian systems.

```c
uint32_t x;
memcpy(&x, data + offset, sizeof(x)); // in little-endian systems
```

The resulting LLVM IR is very simple.

```llvm
%13 = getelementptr inbounds i8, ptr %1, i64 4
%14 = load i32, ptr %13, align 1
```
