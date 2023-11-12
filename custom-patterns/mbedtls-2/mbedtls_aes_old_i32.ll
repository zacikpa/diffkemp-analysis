; Metadata
!0 = !{ !"pattern-start" }

; Functions
declare void @diffkemp.old.mbedtls_platform_zeroize(ptr, i64)

define void @diffkemp.old.mbedtls_aes_old_i32(ptr, ptr) {
  %3 = alloca i32, align 4
  call void @diffkemp.old.mbedtls_platform_zeroize(ptr %3, i64 4), !diffkemp.pattern !0
  ret void
}

define void @diffkemp.new.mbedtls_aes_old_i32(ptr, ptr) {
  ret void
}
