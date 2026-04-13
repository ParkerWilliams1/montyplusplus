from scanner import Scanner
from parser import Parser
from CppToPythonBytecode import CppToPythonBytecode
from pprint import pp


def main():
    # Tests: vector, while, array access, push_back, size
    # Expected output: 14
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
    

    # Tests: <=, array access in conditions, integer division
    # Expected output: 3
    # source = """
    # int binarySearch(int nums[], int n, int target) {
    #     int left = 0;
    #     int right = n - 1;
    #     while (left <= right) {
    #         int mid = left + (right - left) / 2;
    #         if (nums[mid] == target) {
    #             return mid;
    #         }
    #         if (nums[mid] < target) {
    #             left = mid + 1;
    #         } else {
    #             right = mid - 1;
    #         }
    #     }
    #     return -1;
    # }

    # int main() {
    #     int nums[6];
    #     nums[0] = 1;
    #     nums[1] = 3;
    #     nums[2] = 5;
    #     nums[3] = 7;
    #     nums[4] = 9;
    #     nums[5] = 11;
    #     return binarySearch(nums, 6, 7);
    # }
    # """

    # Tests: INT_MIN literal expansion, update-then-compare pattern
    # Expected output: 6
    # source = """
    # int maxSubArray(int nums[], int n) {
    #     int maxSum = INT_MIN;
    #     int current = 0;
    #     for (int i = 0; i < n; i++) {
    #         current = current + nums[i];
    #         if (current > maxSum) {
    #             maxSum = current;
    #         }
    #         if (current < 0) {
    #             current = 0;
    #         }
    #     }
    #     return maxSum;
    # }

    # int main() {
    #     int nums[9];
    #     nums[0] = -2;
    #     nums[1] = 1;
    #     nums[2] = -3;
    #     nums[3] = 4;
    #     nums[4] = -1;
    #     nums[5] = 2;
    #     nums[6] = 1;
    #     nums[7] = -5;
    #     nums[8] = 4;
    #     return maxSubArray(nums, 9);
    # }
    # """

    # Tests: bool return type, while, multi-variable declarations, arithmetic chains
    # Expected output: 1
    # source = """
    # int isPalindrome(int x) {
    #     if (x < 0) {
    #         return 0;
    #     }
    #     int original = x;
    #     int reversed = 0;
    #     while (x != 0) {
    #         int digit = x % 10;
    #         reversed = reversed * 10 + digit;
    #         x = x / 10;
    #     }
    #     if (original == reversed) {
    #         return 1;
    #     }
    #     return 0;
    # }

    # int main() {
    #     int a = isPalindrome(121);
    #     int b = isPalindrome(123);
    #     return a + b;
    # }
    # """

    # Tests: nested for, array indexing [], +, ==, early return
    # Expected output: 0
    # source = """
    # int twoSum(int nums[], int n, int target) {
    #     for (int i = 0; i < n; i++) {
    #         for (int j = i + 1; j < n; j++) {
    #             if (nums[i] + nums[j] == target) {
    #                 return i;
    #             }
    #         }
    #     }
    #     return -1;
    # }

    # int main() {
    #     int nums[4];
    #     nums[0] = 2;
    #     nums[1] = 7;
    #     nums[2] = 11;
    #     nums[3] = 15;
    #     int result = twoSum(nums, 4, 9);
    #     return result;
    # }
    # """

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