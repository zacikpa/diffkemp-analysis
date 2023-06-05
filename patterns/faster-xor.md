# Faster XOR
- library: MbedTLS 3
- versions: 3.3.0 vs 3.4.0
- function: `mbedtls_aes_crypt_cbc`

## Old version
The XOR operation is performed byte-by-byte on two buffers.

```c
for ( i = 0; i < 16; i++ ) {
    output[i] = (unsigned char)( input[i] ^ iv[i] );
}
```

Part of the resulting LLVM IR:

```llvm
%132 = load i8, ptr %130, align 1
%133 = load i8, ptr %3, align 1
%134 = xor i8 %133, %132
store i8 %134, ptr %129, align 1

%135 = getelementptr inbounds i8, ptr %130, i64 1
%136 = load i8, ptr %135, align 1
%137 = load i8, ptr %17, align 1
%138 = xor i8 %137, %136
%139 = getelementptr inbounds i8, ptr %129, i64 1
store i8 %138, ptr %139, align 1

%140 = getelementptr inbounds i8, ptr %130, i64 2
%141 = load i8, ptr %140, align 1
%142 = load i8, ptr %18, align 1
%143 = xor i8 %142, %141
%144 = getelementptr inbounds i8, ptr %129, i64 2
store i8 %143, ptr %144, align 1

%145 = getelementptr inbounds i8, ptr %130, i64 3
%146 = load i8, ptr %145, align 1
%147 = load i8, ptr %19, align 1
%148 = xor i8 %147, %146
%149 = getelementptr inbounds i8, ptr %129, i64 3
store i8 %148, ptr %149, align 1
```

## New version
The XOR operation is performed on 32-bit chunks of the buffers.

```c
for ( i = 0; (i + 4) <= 16; i += 4) {
    uint32_t x, y, z;
    memcpy(&x, a + i, sizeof(x));
    memcpy(&y, b + i, sizeof(y));
    z = x ^ y;
    memcpy(output + i, &z, sizeof(z));
}
```

Part of the resulting LLVM IR:

```llvm
%60 = load i32, ptr %58, align 1
%61 = load i32, ptr %3, align 1
%62 = xor i32 %61, %60
store i32 %62, ptr %57, align 1
```
