from compile import parse
from compile import lex
from compile import lexemes
from compile.combinators import TokenStream
from compile import combinators as comb
from compile.lexemes import KeywordKind as KK

from pprint import pprint

source = "const ident: Type = expr"
source = "let mut ident: Type = expr"
source = "anon ident: mut Type"
source = "def ident(anon ident: mut Type)"
source = "enum Color { Red, Green, Blue }"
source = "union Color = Hsv"
source = "if expr { ident\n ident }"
tokens = lex.tokenize(source)
tokens = list(filter(lambda token: not isinstance(token, lexemes.Whitespace), tokens))

stream = TokenStream(tokens)

# pprint(tokens)

result = parse.if_stmt.parse(stream)
pprint(result)
