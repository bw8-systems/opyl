import typing as t
from dataclasses import dataclass
import enum

from opyl.compile import nodes
from opyl.compile.nodes import FunctionDeclaration


class SymbolKind(enum.Enum):
    Module = enum.auto()
    VariableOrConstant = enum.auto()
    Function = enum.auto()
    Type = enum.auto()


@dataclass
class Symbol:
    # TODO: Use node.Identifier instead of str
    ident: str
    kind: SymbolKind
    table: "SymbolTable | None" = None


class SymbolTable(nodes.Visitor):
    def __init__(self, node: nodes.Node):
        self.symbols = dict[str, Symbol]()  # TODO: Use nodes.Identifier instead of str
        node.accept(self)

    def __setitem__(self, name: str, symbol: Symbol):
        self.symbols[name] = symbol

    @t.override
    def module(self, node: nodes.ModuleDeclaration) -> None:
        for decl in node.declarations:
            decl.accept(self)

    @t.override
    def struct(self, node: nodes.StructDeclaration) -> None:
        for field in node.fields:
            self.symbols[field.name.name] = Symbol(
                ident=field.name.name,
                kind=SymbolKind.VariableOrConstant,
            )

        for func in node.functions:
            self.symbols[func.name.name] = Symbol(
                ident=func.name.name, kind=SymbolKind.Function, table=SymbolTable(func)
            )

    @t.override
    def enum(self, node: nodes.EnumDeclaration) -> None:
        for member in node.members:
            self.symbols[member.name] = Symbol(
                ident=member.name,
                kind=SymbolKind.VariableOrConstant,
            )

    @t.override
    def trait(self, node: nodes.TraitDeclaration) -> None:
        for sig in node.functions:
            self.symbols[sig.name.name] = Symbol(
                ident=sig.name.name,
                kind=SymbolKind.Type,  # Is a signature a type or a function or something new?
            )

    @t.override
    def function(self, node: FunctionDeclaration) -> None:
        for param in node.signature.params:
            self.symbols[param.field.name.name] = Symbol(
                ident=param.field.name.name,
                kind=SymbolKind.VariableOrConstant,
            )

        for stmt in node.body:
            stmt.accept(self)
