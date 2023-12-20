# `opyl`: Opal in Python
```zsh
python opyl
```
## Road Map
- [] Tokenization of source
    - [x] Identifiers and keywords
    - [x] Single-character primitive tokens *eg* `+`, `-`
    - [x] Multi-character primitive tokens *eg* `>=`, `+=`
    - [] Character Literals *eg* `'c'`
        - [x] Basic
        - [] Escape sequences *eg* `'\n'`
    - [] String Literals *eq* `'Hello, World!'`
        - [x] Basic
        - [] Escape sequences
    - [] Integer Literals
        - [] Binary
        - [x] Decimal
        - [] Hex
        - [] Suffixes
- [] Parsing of token stream
    - [x] Basic types (primitive and builtin)
    - [] Aggregate types (arrays)
    - [x] Complex types (structs, unions, enums)
    - [x] Top-Level Declarations (functions, structs, unioms, enums)
    - [x] Control flow structures (if, while, when)
    - [] Newline agnosticism for multi-line expressions
    - [] Expression parsing
        - [x] Prefix expressions
        - [x] Infix expressions
            - [x] Calls
            - [x] Subscripting
            - [x] Binary operators
        - [x] Operator precedence
        - [x] Operator associativity
        - [] ...
- [] Error reporting, handling, and recovery.
- [] Simple Semantic Analysis
    - [] Validation of parameter ordering for position and keyword parameters.
    - [] Name resolution (Undefined references, Multiply-defined symbols)
    - [] ...
- [] Type Checking
    - [] Intrinsic type operations
    - [] Upward type inference for integer literal typing
    - [] Downward type inference for typed literals *eg* string literals
- [] Complex Semantic Analysis
    - [] Constant folding
    - [] lvalues and rvalues and such
- [] C codegen
- [] `libc` linking
- [] `"Hello, World!\n"`
- [] Traits
- [] Generics
 