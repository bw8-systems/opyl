from collections.abc import Sequence
from dataclasses import dataclass
import enum

from compile import node


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


class SymbolTableBuilder(node.NodeVisitor):
    def __init__(self):
        self.table = SymbolTable()

    def visit_keyword(self, keyword: node.Keyword) -> None:
        raise NotImplementedError

    def visit_integer(self, integer: node.Integer) -> None:
        raise NotImplementedError

    def visit_identifier(self, ident: node.Identifier) -> None:
        raise NotImplementedError

    def visit_expression(self, expr: node.Expression) -> None:
        raise NotImplementedError

    def visit_primitive_type(self, type: node.PrimitiveType) -> None:
        raise NotImplementedError

    def visit_identifier_type(self, type: node.IdentifierType) -> None:
        raise NotImplementedError

    def visit_array_type(self, type: node.ArrayType) -> None:
        raise NotImplementedError

    def visit_field(self, field: node.Field) -> None:
        raise NotImplementedError

    def visit_typedef(self, typedef: node.Typedef) -> None:
        raise NotImplementedError

    def visit_const(self, const: node.Const) -> None:
        raise NotImplementedError

    def visit_enum(self, enum: node.Enum) -> None:
        raise NotImplementedError

    def visit_struct(self, struct: node.Struct) -> None:
        raise NotImplementedError

    def visit_module(self, module: node.Module) -> None:
        raise NotImplementedError


def get_symbols(tree: Sequence[node.Node]) -> SymbolTable:
    builder = SymbolTableBuilder()

    for declaration in tree:
        declaration.accept(builder)

    return builder.table
