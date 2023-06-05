# Multiple relocations
- library: MbedTLS 2
- versions: 2.27.0 vs 2.28.0
- function: `mbedtls_aes_crypt_xts`

## Old version
64-bit integer is copied byte-by-byte starting from the LSB.

```c
(b)[(i) + 7] = (unsigned char) ( (n) >> 56 );
(b)[(i) + 6] = (unsigned char) ( (n) >> 48 );
(b)[(i) + 5] = (unsigned char) ( (n) >> 40 );
(b)[(i) + 4] = (unsigned char) ( (n) >> 32 );
(b)[(i) + 3] = (unsigned char) ( (n) >> 24 );
(b)[(i) + 2] = (unsigned char) ( (n) >> 16 );
(b)[(i) + 1] = (unsigned char) ( (n) >>  8 );
(b)[(i)    ] = (unsigned char) ( (n)       );
```

Part of the generated LLVM IR:
```llvm
%334 = lshr i64 %323, 56
%335 = trunc i64 %334 to i8
store i8 %335, ptr %27, align 1
%336 = lshr i64 %323, 48
%337 = trunc i64 %336 to i8
store i8 %337, ptr %28, align 2
%338 = lshr i64 %323, 40
%339 = trunc i64 %338 to i8
store i8 %339, ptr %29, align 1
%340 = lshr i64 %323, 32
%341 = trunc i64 %340 to i8
store i8 %341, ptr %30, align 4
%342 = lshr i64 %323, 24
%343 = trunc i64 %342 to i8
store i8 %343, ptr %31, align 1
%344 = lshr i64 %323, 16
%345 = trunc i64 %344 to i8
store i8 %345, ptr %32, align 2
%346 = lshr i64 %323, 8
%347 = trunc i64 %346 to i8
store i8 %347, ptr %33, align 1
%348 = trunc i64 %330 to i8
store i8 %348, ptr %7, align 16
```

## New version
The integer is copied starting from the MSB.

```c
(b)[(i)    ] = (unsigned char) ( (n)       );
(b)[(i) + 1] = (unsigned char) ( (n) >>  8 );
(b)[(i) + 2] = (unsigned char) ( (n) >> 16 );
(b)[(i) + 3] = (unsigned char) ( (n) >> 24 );
(b)[(i) + 4] = (unsigned char) ( (n) >> 32 );
(b)[(i) + 5] = (unsigned char) ( (n) >> 40 );
(b)[(i) + 6] = (unsigned char) ( (n) >> 48 );
(b)[(i) + 7] = (unsigned char) ( (n) >> 56 );
```

Part of the generated LLVM IR:
```llvm
%334 = trunc i64 %330 to i8
store i8 %334, ptr %7, align 16
%335 = lshr i64 %323, 8
%336 = trunc i64 %335 to i8
store i8 %336, ptr %33, align 1
%337 = lshr i64 %323, 16
%338 = trunc i64 %337 to i8
store i8 %338, ptr %32, align 2
%339 = lshr i64 %323, 24
%340 = trunc i64 %339 to i8
store i8 %340, ptr %31, align 1
%341 = lshr i64 %323, 32
%342 = trunc i64 %341 to i8
store i8 %342, ptr %30, align 4
%343 = lshr i64 %323, 40
%344 = trunc i64 %343 to i8
store i8 %344, ptr %29, align 1
%345 = lshr i64 %323, 48
%346 = trunc i64 %345 to i8
store i8 %346, ptr %28, align 2
%347 = lshr i64 %323, 56
%348 = trunc i64 %347 to i8
store i8 %348, ptr %27, align 1
```
