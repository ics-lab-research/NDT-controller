When writing code, you MUST follow these principles:

- READABILITY FIRST: Code should be easy to read and understand.
- SIMPLICITY: Keep code as simple as possible. Avoid unnecessary complexity.
- MEANINGFUL NAMES: Use descriptive names for variables, functions, etc. Names should reveal intent.
- SMALL FUNCTIONS: Functions should be small and do one thing well, typically 5-20 lines, avoiding overly tiny
  functions (e.g., fewer than 5 lines) unless they represent a clear, reusable abstraction.
- DESCRIPTIVE FUNCTION NAMES: Function names should clearly describe the action being performed.
- MINIMAL ARGUMENTS: Prefer fewer function arguments. Aim for no more than two or three.
- SELF-EXPLANATORY CODE: Minimize comments—they can become outdated. Write code that explains itself.
- USEFUL COMMENTS: When comments are necessary, they should add information not apparent from the code. ERROR
  HANDLING: Properly handle errors and exceptions to ensure robustness. Use exceptions rather than error
  codes.
- SECURITY: Consider security implications. Implement best practices to protect against vulnerabilities.
- FUNCTIONAL PROGRAMMING: Adhere to these four principles:
  1. Pure Functions
  2. Immutability
  3. Function Composition
  4. Declarative Code
- NO OOP: Do not use object-oriented programming.
- LOGGING (REQUIRED): Use loguru for Python or appropriate libraries for other languages. Log strategically at
  entry/exit points of important functions, external calls (API/database/file operations), errors with full
  context, and critical state changes. Do not log inside loops, trivial operations, or sensitive data. Use
  proper log levels (ERROR/WARNING/INFO/DEBUG).
