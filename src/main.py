from scanner import Scanner
from parser import Parser
from pprint import pp

def main():
    source = """
    int main() {
        int x = 5;
        x = x + 2;
        return x;
    }
    """

    tokens = Scanner(source).scan()
    parser = Parser(tokens)
    ast = parser.parse()

    pp(ast)

if __name__ == "__main__":
    main()
