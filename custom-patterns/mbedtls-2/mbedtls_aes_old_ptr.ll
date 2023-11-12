; Metadata
!0 = !{ !"pattern-start" }

; Functions
declare void @diffkemp.old.mbedtls_platform_zeroize(ptr, i64)

define void @diffkemp.old.mbedtls_aes_old_ptr(ptr, ptr) {
  %3 = alloca ptr, align 8
  call void @diffkemp.old.mbedtls_platform_zeroize(ptr %3, i64 8), !diffkemp.pattern !0
  ret void
}

define void @diffkemp.new.mbedtls_aes_old_ptr(ptr, ptr) {
  ret void
}
