from dataclasses import dataclass


from compile.expr import Expression
from compile.token import Identifier
from support.union import Maybe


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

type Type = Identifier


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
class GenericParamSpec:
    field: Field


@dataclass
class FunctionSignature:
    name: Identifier
    params: list[ParamSpec]
    return_type: Maybe.Type[Identifier]


@dataclass
class MethodSignature:
    name: Identifier
    generic_params: list[GenericParamSpec]
    params: list[ParamSpec]
    return_type: Maybe.Type[str]


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
class FunctionDeclaration:
    name: Identifier
    signature: FunctionSignature
    body: list[Statement]
    # TODO: etc


@dataclass
class MethodDeclaration:
    name: Identifier
    signature: MethodSignature
    body: list[Statement]
    # TODO: etc


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
    # generic_params: GenericParamSpec
    # trait_impls: list[
    #     str
    # ]  # TODO: Hm, the implemented traits could be generic, so just a string isn't sufficient.
    fields: list[Field]
    # methods: list[MethodDeclaration]
    functions: list[FunctionDeclaration]


@dataclass
class UnionDeclaration:
    name: Identifier
    members: list[Type]  # TODO: The TODO above applies here too.
    # generic_params: GenericParamSpec
    # trait_impls: list[str]  # TODO: See TODO above.
    # methods: list[MethodDeclaration]
    functions: list[FunctionDeclaration]


@dataclass
class TraitDeclaration:
    name: Identifier
    # bases: list[Identifier]
    # generic_params: list[GenericParamSpec]
    # methods: list[MethodSignature]
    functions: list[FunctionSignature]


@dataclass
class ContinueStatement:
    ...


@dataclass
class BreakStatement:
    ...


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


@dataclass
class ModuleDeclaration:
    declarations: list[Declaration]
