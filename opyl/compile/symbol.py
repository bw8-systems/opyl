from collections.abc import Sequence
from dataclasses import dataclass
import enum

from opyl.compile import nodes


class SemanticErrorKind(enum.Enum):
    MultiplyDefinedSymbol = enum.auto()
    UndefinedSymbol = enum.auto()


@dataclass
class SemanticError(Exception):
    kind: SemanticErrorKind


class SymbolKind(enum.Enum):
    ...


@dataclass
class Symbol:
    name: str
    kind: SymbolKind


class SymbolTable:
    def __init__(self):
        self.symbols: dict[str, Symbol] = {}

    def add(self, symbol: Symbol):
        if symbol.name in self.symbols:
            raise SemanticError(SemanticErrorKind.MultiplyDefinedSymbol)

        self.symbols.append(symbol)

    def get(self, key: str) -> Symbol:
        try:
            return self.symbols[key]
        except KeyError:
            raise SemanticError(SemanticErrorKind.UndefinedSymbol)


class SymbolTableBuilder(nodes.NodeVisitor):
    def __init__(self):
        self.table = SymbolTable()

    def visit_keyword(self, keyword: nodes.Keyword) -> None:
        raise NotImplementedError

    def visit_integer(self, integer: nodes.Integer) -> None:
        raise NotImplementedError

    def visit_identifier(self, ident: nodes.Identifier) -> None:
        raise NotImplementedError

    def visit_expression(self, expr: nodes.Expression) -> None:
        raise NotImplementedError

    def visit_primitive_type(self, type: nodes.PrimitiveType) -> None:
        raise NotImplementedError

    def visit_identifier_type(self, type: nodes.IdentifierType) -> None:
        raise NotImplementedError

    def visit_array_type(self, type: nodes.ArrayType) -> None:
        raise NotImplementedError

    def visit_field(self, field: nodes.Field) -> None:
        raise NotImplementedError

    def visit_typedef(self, typedef: nodes.Typedef) -> None:
        raise NotImplementedError

    def visit_const(self, const: nodes.Const) -> None:
        raise NotImplementedError

    def visit_enum(self, enum: nodes.Enum) -> None:
        raise NotImplementedError

    def visit_struct(self, struct: nodes.Struct) -> None:
        raise NotImplementedError

    def visit_module(self, module: nodes.Module) -> None:
        raise NotImplementedError


def get_symbols(tree: Sequence[nodes.Node]) -> SymbolTable:
    builder = SymbolTableBuilder()

    for declaration in tree:
        declaration.accept(builder)

    return builder.table
