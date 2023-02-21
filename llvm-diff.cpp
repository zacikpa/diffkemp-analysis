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
#include <sstream>
#include <string>
#include <fstream>
#include <cstdlib>

using namespace llvm;

std::string get_function_body(Function *fun) {
    std::string body;
    raw_string_ostream ostream(body);
    ostream << *fun;
    return body;
}

std::vector<Function*> get_called_functions(Function *fun) {
    std::vector<Function *> called_functions;
    for (BasicBlock &bb : *fun) {
        for (Instruction &inst : bb) {
            if (CallInst *call = dyn_cast<CallInst>(&inst)) {
                if (!isa<IntrinsicInst>(call)) {
                    Function *called_fun = call->getCalledFunction();
                    if (called_fun) {
                        called_functions.push_back(called_fun);
                    }
                }
            }
        }
    }
    return called_functions;
}

void write_diff(Function *old_fun, Function *new_fun) {
    std::ofstream old_file, new_file;
    old_file.open("tmp_old");
    new_file.open("tmp_new");
    old_file << get_function_body(old_fun);
    new_file << get_function_body(new_fun);
    old_file.close();
    new_file.close();
    std::ostringstream diff_stream;
    std::cout << diff_stream.str() << std::endl;
    std::system(diff_stream.str().c_str());
}

int compare(Function *old_fun, Function *new_fun, std::set<StringRef> &done) {
    done.insert(old_fun->getName());
    if (get_function_body(old_fun).compare(get_function_body(new_fun))) {
        return 1;
    }
    auto old_called = get_called_functions(old_fun);
    auto new_called = get_called_functions(new_fun);
    if (old_called.size() != new_called.size()) {
        return 1;
    }
    for (size_t i = 0; i < old_called.size(); ++i) {
        if (done.count(old_called[i]->getName()) != 0) {
            continue;
        }
        if (compare(old_called[i], new_called[i], done)) {
            return 1;
        }
    }
    return 0;
}


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
    if (old_fun == nullptr || new_fun == nullptr) {
        return 1;
    }
    std::set<StringRef> done;
    return compare(old_fun, new_fun, done);
}