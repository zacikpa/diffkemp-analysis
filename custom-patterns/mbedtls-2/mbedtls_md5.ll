; Metadata
!0 = !{ !"pattern-start" }

; Structures
%struct.anon = type { [16 x i32], i32, i32, i32, i32 }

; Functions
declare void @diffkemp.new.mbedtls_platform_zeroize(ptr, i64)


define void @diffkemp.old.mbedtls_md5(ptr, ptr) {
  ret void
}

define void @diffkemp.new.mbedtls_md5(ptr, ptr) {
  %3 = alloca %struct.anon, align 4
  call void @diffkemp.new.mbedtls_platform_zeroize(ptr %3, i64 80), !diffkemp.pattern !0
  ret void
}
