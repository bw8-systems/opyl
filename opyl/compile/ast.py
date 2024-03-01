from dataclasses import dataclass
import enum

from opyl.compile.expr import Expression
from opyl.compile.token import Identifier, Basic
from opyl.support.union import Maybe


type Statement = (
    VarDeclaration
    | ConstDeclaration
    | ForLoop
    | WhileLoop
    | WhenStatement
    | IfStatement
    | ReturnStatement
    | AssignStatement
    | Expression
)

type Type = Identifier | BuiltInType


class BuiltInType(enum.Enum):
    U8 = "u8"
    I8 = "i8"
    U16 = "u16"
    I16 = "i16"
    U32 = "u32"
    I32 = "i32"
    Str = "str"
    Char = "char"
    Bool = "bool"


@dataclass
class Field:
    name: Identifier
    type: Type


@dataclass
class ParamSpec:
    is_anon: bool
    ident: Identifier
    is_mut: bool
    type: Type


@dataclass
class FunctionSignature:
    name: Identifier
    params: list[ParamSpec]
    return_type: Maybe.Type[Identifier]


type Declaration = (
    FunctionDeclaration
    | ConstDeclaration
    | VarDeclaration
    | EnumDeclaration
    | StructDeclaration
    | TypeDefinition
    | TraitDeclaration
)


# TODO: This would be more ergonomic if it didn't wrap FunctionSignature
# and instead extracted the values to the top level.
@dataclass
class FunctionDeclaration:
    name: Identifier
    signature: FunctionSignature
    body: list[Statement]


@dataclass
class ConstDeclaration:
    name: Identifier
    type: Type
    initializer: Expression


@dataclass
class VarDeclaration:
    name: Identifier
    is_mut: bool
    type: Maybe.Type[Type]
    initializer: Expression


@dataclass
class EnumDeclaration:
    name: Identifier
    members: list[Identifier]


@dataclass
class StructDeclaration:
    name: Identifier
    fields: list[Field]
    functions: list[FunctionDeclaration]


@dataclass
class TypeDefinition:
    name: Identifier
    types: list[Type]


@dataclass
class TraitDeclaration:
    name: Identifier
    functions: list[FunctionSignature]


@dataclass
class ContinueStatement: ...


@dataclass
class BreakStatement: ...


type LoopStatement = Statement | BreakStatement | ContinueStatement


@dataclass
class WhileLoop:
    condition: Expression
    statements: list[LoopStatement]


@dataclass
class ForLoop:
    target: Identifier
    iterator: Expression
    statements: list[LoopStatement]


@dataclass
class IfStatement:
    if_condition: Expression
    if_statements: list[Statement]
    else_statements: list[Statement]


@dataclass
class IsClause:
    target: Type
    statements: list[Statement]


@dataclass
class WhenStatement:
    expression: Expression
    target: Maybe.Type[Identifier]
    is_clauses: list[IsClause]
    else_statements: list[Statement]


@dataclass
class ReturnStatement:
    expression: Maybe.Type[Expression]


class AssignmentOperator(enum.Enum):
    Equal = Basic.Equal
    Add = Basic.PlusEqual
    Subtract = Basic.HyphenEqual
    Multiply = Basic.AsteriskEqual
    Divide = Basic.ForwardSlashEqual


@dataclass
class AssignStatement:
    target: Expression
    operator: AssignmentOperator
    value: Expression
