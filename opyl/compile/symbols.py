import dataclasses
import enum

from opyl.compile.token import Identifier
from opyl.compile.types import Type, Primitive
from opyl.compile import types
from opyl.compile.ast import (
    Declaration,
    BuiltInType,
    VarDeclaration,
    ConstDeclaration,
    FunctionDeclaration,
    StructDeclaration,
    EnumDeclaration,
    TypeDefinition,
    TraitDeclaration,
)
from opyl.support.union import Maybe


class SymbolError(enum.Enum):
    MultiplyDefinedSymbol = enum.auto()


@dataclasses.dataclass
class SymbolTable:
    table: dict[str, Type] = dataclasses.field(default_factory=dict)

    def find(self, identifier: Identifier) -> Maybe.Type[Type]:
        try:
            return Maybe.Just(self.table[identifier.identifier])
        except KeyError:
            return Maybe.Nothing

    def add(self, identifier: Identifier, binding: Type):
        self.table[identifier.identifier] = binding


def build_global_symbols(
    decls: list[Declaration],
) -> tuple[SymbolTable, list[SymbolError]]:
    env = SymbolTable()
    errors = list[SymbolError]()

    for builtin in BuiltInType:
        env.add(Identifier(builtin.value), Primitive(builtin))

    for decl in decls:
        match decl_to_type(decl):
            case Maybe.Just((ident, ty)):
                match env.find(ident):
                    case Maybe.Nothing:
                        env.add(ident, ty)
                    case Maybe.Just():
                        errors.append(SymbolError.MultiplyDefinedSymbol)
            case Maybe.Nothing:
                ...

    return (env, errors)


def decl_to_type(decl: Declaration) -> Maybe.Type[tuple[Identifier, Type]]:
    match decl:
        case FunctionDeclaration():
            ...
        case ConstDeclaration():
            ...
        case VarDeclaration():
            ...
        case EnumDeclaration(ident):
            return Maybe.Just((ident, types.Enum(decl)))
        case StructDeclaration(ident):
            return Maybe.Just((ident, types.Struct(decl)))
        case TypeDefinition():
            ...
        case TraitDeclaration():
            ...

    return Maybe.Nothing
