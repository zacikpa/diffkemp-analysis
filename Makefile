all: llvm-compare llvm-diff

llvm-compare: llvm-compare.cpp
	g++ llvm-compare.cpp -g -lLLVM -o llvm-compare

llvm-diff: llvm-diff.cpp
	g++ llvm-diff.cpp -g -lLLVM -o llvm-diff