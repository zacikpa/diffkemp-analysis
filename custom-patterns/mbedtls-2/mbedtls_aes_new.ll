; Metadata
!0 = !{ !"pattern-start" }

; Structures
%struct.anon = type { [4 x i32], [4 x i32] }

; Functions
declare void @diffkemp.new.mbedtls_platform_zeroize(ptr, i64)

define void @diffkemp.old.mbedtls_aes_new(ptr, ptr) {
  ret void
}

define void @diffkemp.new.mbedtls_aes_new(ptr, ptr) {
  %3 = alloca %struct.anon, align 4
  call void @diffkemp.new.mbedtls_platform_zeroize(ptr %3, i64 32), !diffkemp.pattern !0
  ret void
}
