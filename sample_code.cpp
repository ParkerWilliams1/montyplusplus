// Simple C++ test file for scanner
#include <iostream>
#include <string>

int main() {
    // Variable declarations and assignments
    int a = 10;
    int b = 20;
    int result = 0;
    
    // Arithmetic operations
    result = a + b;
    result = a - b;
    result = a * b;
    result = a / b;
    result = a % b;
    
    // Comparison operators
    if (a == b) {
        std::cout << "a equals b" << std::endl;
    }
    if (a != b) {
        std::cout << "a not equal to b" << std::endl;
    }
    if (a < b) {
        std::cout << "a less than b" << std::endl;
    }
    if (a <= b) {
        std::cout << "a less than or equal to b" << std::endl;
    }
    if (a > b) {
        std::cout << "a greater than b" << std::endl;
    }
    if (a >= b) {
        std::cout << "a greater than or equal to b" << std::endl;
    }
    
    // Shift operators
    int x = 5;
    int left_shift = x << 2;
    int right_shift = x >> 1;
    
    // While loop
    int counter = 0;
    while (counter < 5) {
        std::cout << "Counter: " << counter << std::endl;
        counter++;
    }
    
    // For loop
    for (int i = 0; i < 10; i++) {
        if (i % 2 == 0) {
            std::cout << i << " is even" << std::endl;
        } else {
            std::cout << i << " is odd" << std::endl;
        }
    }
    
    // String handling
    std::string message = "Hello, World!";
    std::string empty = "";
    std::string quoted = "He said: \"Hello there!\"";
    
    // Function calls with scope resolution
    std::cout << message << std::endl;
    std::cin >> x;
    
    // Multiple operators in one line
    int y = (a + b) * (x - y) / 2;
    
    // Complex expressions
    if ((a > 0 && b < 100) || (x == 5 && y != 10)) {
        std::cout << "Complex condition met" << std::endl;
    }
    
    /* 
       Multi-line comment test
       This should be ignored by the scanner
    */
    
    // Nested braces and parentheses
    {
        int inner_var = 42;
        {
            int deeper_var = 100;
            std::cout << deeper_var << std::endl;
        }
    }
    
    // Commas in various contexts
    int arr[] = {1, 2, 3, 4, 5};
    function_call(a, b, result);
    
    // Colon usage
    int ternary = (a > b) ? a : b;
    
    return 0;
}

// Another function
void processData(int data[], int size) {
    for (int i = 0; i < size; i++) {
        data[i] = data[i] * 2;
    }
}

// Class definition (partial)
class Calculator {
private:
    int last_result;
    
public:
    Calculator() : last_result(0) {}
    
    int add(int a, int b) {
        last_result = a + b;
        return last_result;
    }
    
    int getLastResult() const {
        return last_result;
    }
};
