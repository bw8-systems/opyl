import typing as t

from . import new_parse as parse


def generate(decls: t.Sequence[parse.TopLevelDeclaration]):
    for decl in decls:
        match decl:
            case parse.VariableDeclaration(_, name, type):
                return f"const {type} {name};"
            case parse.FunctionDeclaration():
                ...
