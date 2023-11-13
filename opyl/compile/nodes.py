from dataclasses import dataclass
from enum import Enum

from opyl.compile.lexemes import PrimitiveKind
from .positioning import Span


@dataclass
class Node:
    span: Span


type Statement = (
    VarDeclaration
    | ForLoop
    | WhileLoop
    | WhenStatement
    | IfStatement
    | ReturnStatement
    | ContinueStatement
    | BreakStatement
)
type TopLevelDeclaration = EnumDeclaration | VarDeclaration


type Expression = IntegerLiteral | Identifier | BinaryExpression


class BinaryOperator(Enum):
    Add = PrimitiveKind.Plus
    Sub = PrimitiveKind.Hyphen
    Mul = PrimitiveKind.Asterisk
    Div = PrimitiveKind.ForwardSlash
    Pow = PrimitiveKind.Caret

    def precedence(self) -> int:
        return {
            BinaryOperator.Add: 1,
            BinaryOperator.Sub: 1,
            BinaryOperator.Mul: 2,
            BinaryOperator.Div: 2,
            BinaryOperator.Pow: 3,
        }[self]

    def is_right_associative(self) -> bool:
        return {
            BinaryOperator.Add: False,
            BinaryOperator.Sub: False,
            BinaryOperator.Mul: False,
            BinaryOperator.Div: False,
            BinaryOperator.Pow: True,
        }[self]

    @classmethod
    def values(cls) -> set[PrimitiveKind]:
        return {member.value for member in cls}


@dataclass
class BinaryExpression(Node):
    operator: BinaryOperator
    left: Expression
    right: Expression


@dataclass
class Identifier(Node):
    name: str


@dataclass
class IntegerLiteral(Node):
    integer: int


type Type = Identifier
# @dataclass
# class Type(Node):
#     name: str


@dataclass
class Field(Node):
    name: str
    type: Type


@dataclass
class ParamSpec(Node):
    is_anon: bool
    field: Field


@dataclass
class GenericParamSpec(Node):
    field: Field


@dataclass
class FunctionSignature(Node):
    name: str
    params: list[ParamSpec]
    return_type: str | None  # TODO: from a type perspective, all functions have a return type...


@dataclass
class MethodSignature(Node):
    name: str
    generic_params: list[GenericParamSpec]
    params: list[ParamSpec]
    return_type: str | None


type Declaration = (
    FunctionDeclaration
    | MethodDeclaration
    | ConstDeclaration
    | VarDeclaration
    | EnumDeclaration
    | StructDeclaration
    | UnionDeclaration
    | TraitDeclaration
)


@dataclass
class FunctionDeclaration(Node):
    signature: FunctionSignature
    body: list[Statement]
    # TODO: etc


@dataclass
class MethodDeclaration(Node):
    signature: MethodSignature
    body: list[Statement]
    # TODO: etc


@dataclass
class ConstDeclaration(Node):
    name: Identifier
    type: Type
    initializer: Expression


@dataclass
class VarDeclaration(Node):
    is_mut: bool
    name: Identifier
    type: Type  # TODO: Using strings here may be bad idea.
    initializer: Expression


@dataclass
class EnumDeclaration(Node):
    identifier: Identifier
    members: list[Identifier]


@dataclass
class StructDeclaration(Node):
    name: Identifier
    # generic_params: GenericParamSpec
    # trait_impls: list[
    #     str
    # ]  # TODO: Hm, the implemented traits could be generic, so just a string isn't sufficient.
    fields: list[Field]
    # methods: list[MethodDeclaration]
    # functions: list[FunctionDeclaration]


@dataclass
class UnionDeclaration(Node):
    name: str
    members: list[Type]  # TODO: The TODO above applies here too.
    # generic_params: GenericParamSpec
    # trait_impls: list[str]  # TODO: See TODO above.
    # methods: list[MethodDeclaration]
    # functions: list[FunctionDeclaration]


@dataclass
class TraitDeclaration(Node):
    name: str
    # bases: list[Identifier]
    # generic_params: list[GenericParamSpec]
    # methods: list[MethodSignature]
    functions: list[FunctionSignature]


@dataclass
class WhileLoop(Node):
    condition: Expression
    statements: list[Statement]


@dataclass
class ForLoop(Node):
    target: Identifier
    iterator: Expression
    statements: list[Statement]


@dataclass
class IfStatement(Node):
    if_condition: Expression
    if_statements: list[Statement]
    else_statements: list[Statement]


@dataclass
class IsClause(Node):
    pattern: Type
    statements: list[Statement]


@dataclass
class WhenStatement(Node):
    expression: Expression
    as_target: Identifier | None
    is_clauses: list[IsClause]


@dataclass
class ReturnStatement(Node):
    expression: Expression | None


@dataclass
class ContinueStatement(Node):
    ...


@dataclass
class BreakStatement(Node):
    ...
