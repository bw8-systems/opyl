from opyl.compile import lex
from opyl.compile import new_parse as parse
from opyl.compile import generate as gen

tokens = lex.tokenize("let foo: int")
decl = parse.OpalParser(parse.Stream(tokens)).parse_variable_declaration()

print(gen.generate([decl]))
