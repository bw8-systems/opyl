from opyl.compile import lex
from opyl.compile import parse
from opyl.compile import stream

tokens = lex.tokenize(r"enum Color {}")
decl = parse.OpalParser(stream.Stream(tokens)).parse_enum_declaration()

# print(gen.generate([decl]))
