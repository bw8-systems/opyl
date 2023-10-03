# Opal Higher Order Typing
Opal's type system is strong, static, and explicit. It favors functional approaches and as such does not feature traditional inheritance. Here are some of the higher order elements present in the type system.

## Enums
Enums are the the simplest of the non-primitive type kinds in Opal. They represent a subset of some integer domain, where each of those integral values have names which represent them. This is essentially the same as an enum in C or C++. Enum member values begin at zero and increment in the order of their inclusion in the definition.
```
enum Keyword {
    Enum,
    Protocol,
    Struct,
    Union,
    Type,
}
``` 

## Protocols
Protocols are abstract types used to define interfaces that other types can implement. These interfaces are composed of function signatures, so implementation is done by defining methods with matching signatures. Protocols do not specify any behavior, and as such protocol methods cannot be defined in a `protocol` block. Parameters using protocol types enable dynamic polymorphism in Opal. This can be useful for creating heterogenous collections. 
```
protocol Display {
    def repr(&self) -> String
}
```

## Generic Types
Generic types allow for higher order types to be parameterized at compile time by types, in a similar way to how values parameterized at run time by other data values. This is useful for code reuse. Imagine defining an `Iterator` protocol; naturally, the items yielded from the iterator will be dependent on the type implementing the protocol. In this case, it makes sense to make the "item" type generic.
```
protocol Iterator<Item> {
    def next(mut &self) -> Item
}
```
Creating concrete generic types and functions enables a form of static polymorphism, where the functions dispatched to are all determined at compile time. Whereas protocol types allow for heterogenous data structures, generic types allow for homogenous data structures.
```
let list_of_int: List<u32>
let list_of_bool: List<bool>
```
Generic type parameters can be bounded by protocols. This requires type parameters to implement a known interface in order to be considered valid.
```
protocol Writer<T: Display> {
    def write(mut &self, data: T)
}
```

## Structures
Structures package data and operations on that data. They are similar to classes, however the lack of access specifiers in Opal means that all attributes are considered public. This behavior of attributes "defaulting" to public is a feature of `struct`s in C++, whereas most languages "default" to private attributes in classes.
```
# A simple struct which implements the Display protocol.
struct TextPosition(Display) {
    absolute: u32
    line: u32
    column: u32

    def repr(&self) -> String { ... }
}

# A generic struct with type parameter T
struct List<T> {
    def append(item: T) { ... }
    def insert(item: T, index: u32) { ... }
    def pop() -> T { ... }
    def remove(index: u32) -> T { ... }
}
```

## Unions
Unions are higher order types which represent the possibility of a value to one of any number concrete types. In their simplest form, unions only group types.
```
union MyUnion = int | bool

def foo(value: u32) -> MyUnion {
    if value == 0 { return 5 }
    return True
}
```
All Opal unions are tagged. In order to treat the return type of `foo` as an `int` or a `bool`, a `when` statement must be used to check this tag. You can think of a `when` statement as a `switch`/`case` statement where the cases are types.
```
when foo() as rv {
    is int { /* rv may be used as an int here. */ }
    is bool { /* rv may be used as a bool here. */ }
}
```
Sometimes, there are operations which should be valid for any value of a union type, regardless of its concrete type. In this case, complex `struct`-like `union` blocks can be used to defined methods.
```
enum Keyword { Enum, Protocol, Struct, Union }
enum Primitive { LeftBrace, RightBrace, Colon, LeftParen, RightParen }

struct Token {
    span: Span
    kind: TokenKind
}

union TokenKind = Keyword | Primitive {
    def to_token(&self, span: Span) -> Token { ... }
}
```
In the event of a function returning a `TokenKind`, the method `to_token` can be called on it without switching on its concrete type via `when`. Unions can also be made generic, just like protocols and structures.
```
union Result<Ok, Err> = Ok | Err {
    def is_ok(&self) -> bool {
        when self {
            is Ok { return True }
            is Err { return False }
        }
    }

    def is_err(&self) -> bool {
        return !self.is_ok()
    }
}
```
As always, generic type parameters can be bounded by protocols they must implement.