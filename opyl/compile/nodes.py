import typing as t
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

from compile.lex import PrimitiveKind, Token


@dataclass
class Node(ABC):
    @abstractmethod
    def accept(self, visitor: "Visitor") -> None:
        raise NotImplementedError()


type Statement = (
    VarDeclaration
    | ConstDeclaration
    | ForLoop
    | WhileLoop
    | WhenStatement
    | IfStatement
    | ReturnStatement
    | Expression
)

type Expression = (
    Identifier
    | IntegerLiteral
    | PrefixExpression
    | BinaryExpression
    | CallExpression
    | SubscriptExpression
)


class InfixOperator(Enum):
    Invocation = PrimitiveKind.LeftParenthesis
    Subscript = PrimitiveKind.LeftBracket
    MemberAccess = PrimitiveKind.Period
    ScopeResolution = PrimitiveKind.ColonColon


class BinaryOperator(Enum):
    Addition = PrimitiveKind.Plus
    Subtraction = PrimitiveKind.Hyphen
    Multiplication = PrimitiveKind.Asterisk
    Division = PrimitiveKind.ForwardSlash
    Exponentiation = PrimitiveKind.Caret
    Equality = PrimitiveKind.EqualEqual

    GreaterThan = PrimitiveKind.RightAngle
    LessThan = PrimitiveKind.LeftAngle

    ScopeResolution = PrimitiveKind.ColonColon

    def precedence(self) -> int:
        return {
            self.Addition: 1,
            self.Subtraction: 1,
            self.Multiplication: 2,
            self.Division: 2,
            self.Exponentiation: 3,
            self.GreaterThan: 6,
            self.LessThan: 6,
            self.Equality: 7,
            self.ScopeResolution: 12,
        }[self]

    def is_right_associative(self) -> bool:
        return {
            self.Addition: False,
            self.Subtraction: False,
            self.Multiplication: False,
            self.Division: False,
            self.Exponentiation: True,
            self.GreaterThan: False,
            self.LessThan: False,
            self.Equality: False,
            self.ScopeResolution: False,
        }[self]

    @classmethod
    def values(cls) -> set[PrimitiveKind]:
        return {member.value for member in cls}

    @classmethod
    def is_binary_op(cls, any: Token) -> t.TypeGuard[PrimitiveKind] | bool:
        return isinstance(any, PrimitiveKind) and any in cls


class PrefixOperator(Enum):
    ArithmeticPlus = PrimitiveKind.Plus
    ArithmeticMinus = PrimitiveKind.Hyphen
    LogicalNegate = PrimitiveKind.Exclamation

    def precedence(self) -> int:
        return 6

    @classmethod
    def is_prefix_op(cls, any: Token) -> t.TypeGuard[PrimitiveKind] | bool:
        return isinstance(any, PrimitiveKind) and any in cls


@dataclass
class BinaryExpression(Node):
    operator: BinaryOperator
    left: Expression
    right: Expression

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.binary(self)


@dataclass
class CallExpression(Node):
    function: Expression
    arguments: list[Expression]

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.call_expr(self)


@dataclass
class SubscriptExpression(Node):
    base: Expression
    index: Expression

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.subscript(self)


@dataclass
class PrefixExpression(Node):
    operator: PrefixOperator
    expr: Expression

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.prefix(self)


@dataclass
class Identifier(Node):
    name: str

    def accept(self, visitor: "Visitor"):
        visitor.identifier(self)


@dataclass
class IntegerLiteral(Node):
    integer: int

    @t.override
    def accept(self, visitor: "Visitor"):
        visitor.integer(self)


class InferredType:
    ...


type Type = Identifier


@dataclass
class Field(Node):
    name: Identifier
    type: Type

    def accept(self, visitor: "Visitor"):
        visitor.field(self)


@dataclass
class ParamSpec(Node):
    is_anon: bool
    ident: Identifier
    is_mut: bool
    type: Type

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.param_spec(self)


@dataclass
class GenericParamSpec(Node):
    field: Field


@dataclass
class FunctionSignature(Node):
    name: Identifier
    params: list[ParamSpec]
    return_type: Identifier | None  # TODO: from a type perspective, all functions have a return type...

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.signature(self)


@dataclass
class MethodSignature(Node):
    name: Identifier
    generic_params: list[GenericParamSpec]
    params: list[ParamSpec]
    return_type: str | None


type Declaration = (
    FunctionDeclaration
    # | MethodDeclaration  # TODO: Move elsewhere. This can't go at module level.
    | ConstDeclaration
    | VarDeclaration
    | EnumDeclaration
    | StructDeclaration
    | UnionDeclaration
    | TraitDeclaration
)


@dataclass
class FunctionDeclaration(Node):
    name: Identifier
    signature: FunctionSignature
    body: list[Statement]
    # TODO: etc

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.function(self)


@dataclass
class MethodDeclaration(Node):
    name: Identifier
    signature: MethodSignature
    body: list[Statement]
    # TODO: etc


@dataclass
class ConstDeclaration(Node):
    name: Identifier
    type: Type
    initializer: Expression

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.const(self)


@dataclass
class VarDeclaration(Node):
    name: Identifier
    is_mut: bool
    type: Type | None
    initializer: Expression

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.variable(self)


@dataclass
class EnumDeclaration(Node):
    name: Identifier
    members: list[Identifier]

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.enum(self)


@dataclass
class StructDeclaration(Node):
    name: Identifier
    # generic_params: GenericParamSpec
    # trait_impls: list[
    #     str
    # ]  # TODO: Hm, the implemented traits could be generic, so just a string isn't sufficient.
    fields: list[Field]
    # methods: list[MethodDeclaration]
    functions: list[FunctionDeclaration]

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.struct(self)


@dataclass
class UnionDeclaration(Node):
    name: Identifier
    members: list[Type]  # TODO: The TODO above applies here too.
    # generic_params: GenericParamSpec
    # trait_impls: list[str]  # TODO: See TODO above.
    # methods: list[MethodDeclaration]
    functions: list[FunctionDeclaration]

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.union(self)


@dataclass
class TraitDeclaration(Node):
    name: Identifier
    # bases: list[Identifier]
    # generic_params: list[GenericParamSpec]
    # methods: list[MethodSignature]
    functions: list[FunctionSignature]

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.trait(self)


@dataclass
class ContinueStatement(Node):
    def accept(self, visitor: "Visitor") -> None:
        raise NotImplementedError()


@dataclass
class BreakStatement(Node):
    def accept(self, visitor: "Visitor") -> None:
        raise NotImplementedError()


type LoopStatement = Statement | BreakStatement | ContinueStatement


@dataclass
class WhileLoop(Node):
    condition: Expression
    statements: list[LoopStatement]

    @t.override
    def accept(self, visitor: "Visitor"):
        visitor.while_loop(self)


@dataclass
class ForLoop(Node):
    target: Identifier
    iterator: Expression
    statements: list[LoopStatement]

    @t.override
    def accept(self, visitor: "Visitor"):
        visitor.for_loop(self)


@dataclass
class IfStatement(Node):
    if_condition: Expression
    if_statements: list[Statement]
    else_statements: list[Statement]

    @t.override
    def accept(self, visitor: "Visitor") -> None:
        visitor.if_statement(self)


@dataclass
class IsClause(Node):
    target: Type
    statements: list[Statement]

    def accept(self, visitor: "Visitor") -> None:
        visitor.is_clause(self)


@dataclass
class WhenStatement(Node):
    expression: Expression
    target: Identifier | None
    is_clauses: list[IsClause]
    else_statements: list[Statement]

    @t.override
    def accept(self, visitor: "Visitor"):
        visitor.when(self)


@dataclass
class ReturnStatement(Node):
    expression: Expression | None

    def accept(self, visitor: "Visitor") -> None:
        raise NotImplementedError()


@dataclass
class ModuleDeclaration(Node):
    declarations: list[Declaration]

    @abstractmethod
    def accept(self, visitor: "Visitor") -> None:
        visitor.module(self)


class Visitor(ABC):
    @abstractmethod
    def const(self, node: ConstDeclaration) -> None:
        raise NotImplementedError()

    @abstractmethod
    def variable(self, node: VarDeclaration) -> None:
        raise NotImplementedError()

    @abstractmethod
    def module(self, node: ModuleDeclaration) -> None:
        raise NotImplementedError()

    @abstractmethod
    def enum(self, node: EnumDeclaration) -> None:
        raise NotImplementedError()

    @abstractmethod
    def struct(self, node: StructDeclaration) -> None:
        raise NotImplementedError()

    @abstractmethod
    def union(self, node: UnionDeclaration) -> None:
        raise NotImplementedError()

    @abstractmethod
    def trait(self, node: TraitDeclaration) -> None:
        raise NotImplementedError()

    @abstractmethod
    def function(self, node: FunctionDeclaration) -> None:
        raise NotImplementedError()

    @abstractmethod
    def identifier(self, node: Identifier) -> None:
        raise NotImplementedError()

    @abstractmethod
    def field(self, node: Field) -> None:
        raise NotImplementedError()

    @abstractmethod
    def for_loop(self, node: ForLoop) -> None:
        raise NotImplementedError()

    @abstractmethod
    def when(self, node: WhenStatement) -> None:
        raise NotImplementedError()

    @abstractmethod
    def while_loop(self, node: WhileLoop) -> None:
        raise NotImplementedError()

    @abstractmethod
    def if_statement(self, node: IfStatement) -> None:
        raise NotImplementedError()

    @abstractmethod
    def is_clause(self, node: IsClause) -> None:
        raise NotImplementedError()

    @abstractmethod
    def integer(self, node: IntegerLiteral) -> None:
        raise NotImplementedError()

    @abstractmethod
    def signature(self, node: FunctionSignature) -> None:
        raise NotImplementedError()

    @abstractmethod
    def param_spec(self, node: ParamSpec) -> None:
        raise NotImplementedError()

    @abstractmethod
    def prefix(self, node: PrefixExpression) -> None:
        raise NotImplementedError()

    @abstractmethod
    def binary(self, node: BinaryExpression) -> None:
        raise NotImplementedError()

    @abstractmethod
    def call_expr(self, node: CallExpression) -> None:
        raise NotImplementedError()

    @abstractmethod
    def subscript(self, node: SubscriptExpression) -> None:
        raise NotImplementedError()
