from scanner import Scanner
from parser import Parser
from CppToPythonBytecode import CppToPythonBytecode
from pprint import pp
import re

KNOWN_HEADERS = {
    'stdio.h', 'cstdio', 'iostream', 'string', 'cstring',
    'vector', 'map', 'set', 'algorithm', 'cmath', 'math.h',
    'utility', 'tuple', 'optional', 'memory', 'functional',
    'stack', 'queue', 'deque', 'list', 'numeric', 'climits',
    'cassert', 'stdexcept', 'sstream', 'fstream', 'bitset',
}

def preprocess(source: str) -> str:
    includes = set()
    lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith('#include'):
            m = re.search(r'#include\s*[<"]([^>"]+)[>"]', stripped)
            if m:
                header = m.group(1)
                includes.add(header)
                if header not in KNOWN_HEADERS:
                    print(f"[warn] unsupported header: <{header}>")
        else:
            lines.append(line)
    return '\n'.join(lines)

def main():
    source = """
        #include <stdio.h>
        #include <vector>

        int main() {
            cout << "Hello " << 67 << endl;
            return 0;
        }
    """
    source = preprocess(source)
    tokens = Scanner(source).scan()
    ast_nodes = Parser(tokens).parse()
    translator = CppToPythonBytecode(ast_nodes)
    code_obj = translator.compile()
    namespace = {}
    exec(code_obj, namespace)
    if "main" in namespace:
        result = namespace["main"]()
        print("Program Output:", result)

if __name__ == "__main__":
    main()
