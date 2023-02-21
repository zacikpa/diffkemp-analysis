#include "llvm/IR/LLVMContext.h"
#include "llvm/Support/SourceMgr.h"
#include "llvm/IR/Module.h"
#include "llvm/IRReader/IRReader.h"
#include "llvm/Transforms/Utils/FunctionComparator.h"
#include "llvm/Support/Debug.h"
#include "llvm/IR/InstrTypes.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/IntrinsicInst.h"
#include <iostream>
#include <string>

using namespace llvm;

int main(int argc, char **argv) {
    if (argc != 4) {
        std::cerr << "Invalid number of arguments" << std::endl;
        return 1;
    }
    char *fun_name = argv[1];
    char *old_mod_path = argv[2];
    char *new_mod_path = argv[3];
    LLVMContext old_ctx, new_ctx;
    SMDiagnostic old_err, new_err;
    std::unique_ptr<Module> old_mod(parseIRFile(old_mod_path, old_err, old_ctx));
    std::unique_ptr<Module> new_mod(parseIRFile(new_mod_path, new_err, new_ctx));
    Function *old_fun = old_mod->getFunction(fun_name);
    Function *new_fun = new_mod->getFunction(fun_name);
    GlobalNumberState GN;
    return FunctionComparator(old_fun, new_fun, &GN).compare();
}