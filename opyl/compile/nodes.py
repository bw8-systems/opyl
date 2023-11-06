from dataclasses import dataclass

from . import tokens
from .stream import Span

type Statement = VariableDeclaration
type TopLevelDeclaration = EnumDeclaration | VariableDeclaration


# @dataclass
# class Identifier:
#     span: Span
#     identifier: str


# Expression probably needs to be a base or a union
@dataclass
class Expression:
    span: Span


@dataclass
class Type:
    span: Span
    name: str


@dataclass
class Field:
    span: Span
    name: str
    type: Type


@dataclass
class EnumDeclaration:
    span: Span
    identifier: tokens.Identifier
    members: list[tokens.Identifier]


@dataclass
class Struct:
    span: Span
    name: str
    fields: list[Field]


@dataclass
class VariableDeclaration:
    span: Span
    mut: tokens.Keyword | None
    name: str
    type: str  # TODO: Using strings here may be bad idea.
    initializer: Expression


@dataclass
class ParamSpec:
    span: Span
    is_anon: bool
    field: Field


@dataclass
class GenericParamSpec:
    span: Span
    field: Field


@dataclass
class FunctionSignature:
    span: Span
    name: str
    params: list[ParamSpec]
    return_type: str | None  # TODO: from a type perspective, all functions have a return type...


@dataclass
class MethodSignature:
    span: Span
    name: str
    generic_params: list[GenericParamSpec]
    params: list[ParamSpec]
    return_type: str | None


@dataclass
class Function:
    span: Span
    signature: FunctionSignature
    body: list[Statement]
    # TODO: etc


@dataclass
class TraitDeclaration:
    span: Span
    name: str
    bases: list[tokens.Identifier]
    generic_params: list[GenericParamSpec]
    methods: list[MethodSignature]
    functions: list[FunctionSignature]
