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
%132 = load i8, ptr %130, align 1, !dbg !1143, !tbaa !336
%133 = load i8, ptr %3, align 1, !dbg !1147, !tbaa !336
%134 = xor i8 %133, %132, !dbg !1148
store i8 %134, ptr %129, align 1, !dbg !1149, !tbaa !336

%135 = getelementptr inbounds i8, ptr %130, i64 1, !dbg !1143
%136 = load i8, ptr %135, align 1, !dbg !1143, !tbaa !336
%137 = load i8, ptr %17, align 1, !dbg !1147, !tbaa !336
%138 = xor i8 %137, %136, !dbg !1148
%139 = getelementptr inbounds i8, ptr %129, i64 1, !dbg !1150
store i8 %138, ptr %139, align 1, !dbg !1149, !tbaa !336

%140 = getelementptr inbounds i8, ptr %130, i64 2, !dbg !1143
%141 = load i8, ptr %140, align 1, !dbg !1143, !tbaa !336
%142 = load i8, ptr %18, align 1, !dbg !1147, !tbaa !336
%143 = xor i8 %142, %141, !dbg !1148
%144 = getelementptr inbounds i8, ptr %129, i64 2, !dbg !1150
store i8 %143, ptr %144, align 1, !dbg !1149, !tbaa !336

%145 = getelementptr inbounds i8, ptr %130, i64 3, !dbg !1143
%146 = load i8, ptr %145, align 1, !dbg !1143, !tbaa !336
%147 = load i8, ptr %19, align 1, !dbg !1147, !tbaa !336
%148 = xor i8 %147, %146, !dbg !1148
%149 = getelementptr inbounds i8, ptr %129, i64 3, !dbg !1150
store i8 %148, ptr %149, align 1, !dbg !1149, !tbaa !336
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
%60 = load i32, ptr %58, align 1, !dbg !1267
%61 = load i32, ptr %3, align 1, !dbg !1270
%62 = xor i32 %61, %60, !dbg !1271
store i32 %62, ptr %57, align 1, !dbg !1275
```
