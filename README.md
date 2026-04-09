# Celestia: A Beginner-Friendly Programming Language
 
Celestia is an educational programming language designed to introduce beginners to the fundamentals of programming. Built in Python, it provides a simple environment for learning about variables, type systems, and symbol tables. The language supports three data types: num, String, and Boolean. Users can declare variables, assign values to them, and update them while maintaining type safety. Celestia demonstrates core compiler concepts including lexical analysis, syntax analysis, semantic analysis, and symbol table management through an interpreter that reads and processes program statements line by line.
 
 
## Installation
 
To get started with Celestia, you need Python 3.6 or higher installed on your system. Clone the repository and navigate to the project folder.
 
```bash
git clone https://github.com/yourusername/celestia.git
cd celestia
python3 --version 
```
 
## Testing
 
Run the interpreter with all built-in test suites by executing the main Python file:
 
```bash
python3 celestia_interpreter.py
```
 
This will automatically run three test suites covering basic variable declarations, variable updates, and type error handling. All 28 test cases should pass. The output will show symbol table snapshots before and after updates, as well as error messages for invalid operations.
