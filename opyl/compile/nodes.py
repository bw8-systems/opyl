from dataclasses import dataclass

from . import tokens
from .stream import Span

type Statement = VarDeclaration
type TopLevelDeclaration = EnumDeclaration | VarDeclaration


@dataclass
class Node:
    span: Span


@dataclass
class Identifier(Node):
    name: str


@dataclass
class IntegerLiteral(Node):
    integer: int


# Expression probably needs to be a base or a union
@dataclass
class Expression(Node):
    ...


@dataclass
class Type(Node):
    name: str


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
    name: str
    type: Type
    initializer: Expression


@dataclass
class VarDeclaration(Node):
    maybe_mut: tokens.Keyword | None
    name: str
    type: Type  # TODO: Using strings here may be bad idea.
    initializer: Expression


@dataclass
class EnumDeclaration(Node):
    identifier: str
    members: list[str]


@dataclass
class StructDeclaration(Node):
    name: str
    generic_params: GenericParamSpec
    trait_impls: list[
        str
    ]  # TODO: Hm, the implemented traits could be generic, so just a string isn't sufficient.
    fields: list[Field]
    methods: list[MethodDeclaration]
    functions: list[FunctionDeclaration]


@dataclass
class UnionDeclaration(Node):
    name: str
    members: list[Type]  # TODO: The TODO above applies here too.
    generic_params: GenericParamSpec
    trait_impls: list[str]  # TODO: See TODO above.
    methods: list[MethodDeclaration]
    functions: list[FunctionDeclaration]


@dataclass
class TraitDeclaration(Node):
    name: str
    bases: list[Identifier]
    generic_params: list[GenericParamSpec]
    methods: list[MethodSignature]
    functions: list[FunctionSignature]
