from scanner import Scanner
from parser import Parser
from CppToPythonBytecode import CppToPythonBytecode
from pprint import pp


def main():
    source = """
        int main() {
        vector<int> nums;
        nums.push_back(3);
        nums.push_back(1);
        nums.push_back(4);
        nums.push_back(1);
        nums.push_back(5);

        int total = 0;
        int i = 0;
        while (i < nums.size()) {
            total = total + nums[i];
            i++;
        }

        return total;
    }
    """

    tokens = Scanner(source).scan()

    parser = Parser(tokens)
    ast_nodes = parser.parse()

    print("=== Parser AST ===")
    pp(ast_nodes)

    translator = CppToPythonBytecode(ast_nodes)
    code_obj = translator.compile()

    print("\n=== Bytecode ===")
    translator.dump_bytecode()

    namespace = {}
    exec(code_obj, namespace)

    if "main" in namespace:
        result = namespace["main"]()
        print("\nProgram Output:", result)


if __name__ == "__main__":
    main()
