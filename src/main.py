from scanner import Scanner
from parser import Parser
from CppToPythonBytecode import CppToPythonBytecode
from pprint import pp


def main():
    source = """
    int helper(int x) {
        int result = 0;

        // while + ++
        while (x > 0) {
            if (x % 2 == 0) {
                result = result + x;
            } else {
                result = result + (x * 2);
            }
            x--;
        }

        return result;
    }

    int main() {
        int total = 0;

        // for + ++
        for (int i = 0; i < 5; i++) {
            int val = helper(i);

            if (val > 5) {
                total = total + val;
            } else {
                total = total + (val + 1);
            }
        }

        return total;
    }
    """

    # scan
    tokens = Scanner(source).scan()

    # parse
    parser = Parser(tokens)
    ast_nodes = parser.parse()

    print("=== Parser AST ===")
    pp(ast_nodes)

    # translate → python bytecode
    translator = CppToPythonBytecode(ast_nodes)
    code_obj = translator.compile()

    print("\n=== Bytecode ===")
    translator.dump_bytecode()

    # execute
    namespace = {}
    exec(code_obj, namespace)

    # call main()
    if "main" in namespace:
        result = namespace["main"]()
        print("\nProgram Output:", result)


if __name__ == "__main__":
    main()