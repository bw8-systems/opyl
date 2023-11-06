# from . import parse as parse


# def generate(decls: t.Sequence[parse.TopLevelDeclaration]):
#     for decl in decls:
#         match decl:
#             case parse.VariableDeclaration(_, name, type):
#                 return f"const {type} {name};"
#             case parse.FunctionDeclaration():
#                 ...
#             case parse.EnumDeclaration():
#                 return generate_enum(decl)


# def generate_enum(decl: parse.EnumDeclaration) -> str:
#     lines = [f"enum {decl.identifier.identifier} {{"]

#     for member in decl.members:
#         lines.append(f"{member.identifier}, ")

#     lines.append("}")

#     return "\n".join(lines)
