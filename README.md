# Celestia: A Beginner-Friendly Programming Language
 
Celestia is an educational programming language designed to introduce beginners to the fundamentals of programming while also demonstrating key concepts from compiler construction. Built in Python, it provides a simplified environment for learning how programming languages work internally without the complexity of full-scale languages like C++ or Java.
 
The language supports three core data types: `num` (numeric values), `String` (text), and `Boolean` (true/false). Users can declare variables, assign values, and update them while maintaining strict type safety. This encourages correct programming habits and reinforces understanding of variable types early in the learning process.
 
Celestia implements a toy compiler pipeline:
 
- lexical analysis (tokenization)
- syntax analysis (parsing into an Abstract Syntax Tree)
- semantic analysis (type checking and validation)
- code generation (translation into Python)
In addition to variable handling, Celestia supports arithmetic expressions, print statements, conditional logic (`if/else`), and loops (`while`). Programs written in Celestia are compiled into Python code and can be executed directly.
 
---
 
## Installation
 
Python 3.6 or higher is required.
 
```bash
git clone https://github.com/yourusername/celestia.git
cd celestia
python3 --version
```
 
---
 
## How to Run
 
```bash
python3 celestia_compiler.py example.cel --run
```
 
This will compile the Celestia source file, generate a Python file (`example_compiled.py`), and execute the compiled program.
 
---
 
## Testing
 
### 1. Basic Test
 
Run:
 
```bash
python3 celestia_compiler.py example.cel --run
```
 
Expected output:
 
```
Compilation successful.
Generated file: example_compiled.py
 
Program output:
--------------------------------------------------
lisa
95.0
Great job
0.0
1.0
2.0
```
 
Verifies:
- compilation pipeline
- variable declarations and updates
- arithmetic expressions
- if/else and while control flow
- print statements
---
 
### 2. Full Feature Test
 
Run:
 
```bash
python3 celestia_compiler.py full_test.cel --run
```
 
Expected output:
 
```
Compilation successful.
Generated file: full_test_compiled.py
 
Program output:
--------------------------------------------------
20.0
Celestia
Total is high
0.0
1.0
2.0
```
 
Verifies:
- arithmetic expressions
- string handling
- boolean logic
- if/else statements
- while loops
---
 
### 3. Error Handling Test
 
Run:
 
```bash
python3 celestia_compiler.py error_test.cel --run
```
 
Expected output:
 
```
Compilation failed: Variable 'x' is undeclared
```
 
Verifies:
- undeclared variable detection
- type checking
- invalid program rejection
---
 
## Additional Commands
 
Show generated Python code:
 
```bash
python3 celestia_compiler.py example.cel --show
```
 
Save compiled output to a file:
 
```bash
python3 celestia_compiler.py example.cel --out output.py
```
 
---