# import enum
# import dataclasses
# from opyl.compile import ast
# from opyl.compile.token import Identifier
# from opyl.support.union import Result


# class SymbolErrorKind(enum.Enum):
#     Redefinition = enum.auto()


# @dataclasses.dataclass
# class SymbolError:
#     kind: SymbolErrorKind


# class SymbolKind(enum.Enum):
#     Type = enum.auto()
#     Variable = enum.auto()
#     Constant = enum.auto()
#     Function = enum.auto()


# @dataclasses.dataclass
# class Symbol:
#     identifier: Identifier
#     kind: SymbolKind
#     parent: "SymbolTable | None" = None


# @dataclasses.dataclass
# class SymbolTable:
#     symbols: dict[Identifier, Symbol] = dataclasses.field(default_factory=dict)

#     def add(self, symbol: Symbol) -> Result.Type[None, SymbolError]:
#         if symbol.identifier in self.symbols:
#             return Result.Err(SymbolError(kind=SymbolErrorKind.Redefinition))

#         self.symbols[symbol.identifier] = symbol
#         return Result.Ok(None)


# def build_decl_symbols(decls: list[ast.Declaration]):
#     global_table = SymbolTable()

#     for decl in decls:
#         match decl:
#             case ast.FunctionDeclaration(ident, _, body):
#                 global_table.add(
#                     Symbol(
#                         ident, kind=SymbolKind.Function, table=build_stmt_symbols(body)
#                     )
#                 )
#             case ast.ConstDeclaration(ident, _, _):
#                 global_table.add(Symbol(ident, kind=SymbolKind.Constant))
#             case ast.VarDeclaration(ident, _, _, _):
#                 global_table.add(Symbol(ident, kind=SymbolKind.Variable))
#             case ast.EnumDeclaration(ident, _):
#                 # TODO: add enum members to symbol table.
#                 global_table.add(Symbol(ident, kind=SymbolKind.Type))
#             case ast.StructDeclaration(ident, _, _):
#                 # TODO: add struct members to symbol table.
#                 global_table.add(Symbol(ident, kind=SymbolKind.Type))
#             case ast.TypeDefinition(ident, _):
#                 global_table.add(Symbol(ident, kind=SymbolKind.Type))
#             case ast.TraitDeclaration(ident, _):
#                 # TODO: Add trait decls to symbol table.
#                 global_table.add(Symbol(ident, kind=SymbolKind.Type))


# def resolve_types():
#     _known_types: dict[int, ResolvedType] = {0: ResolvedBoolean()}
