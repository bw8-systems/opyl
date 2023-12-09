from compile import parse
from compile import lex
from compile import lexemes
from compile.combinators import TokenStream
from compile import combinators as comb
from compile.lexemes import KeywordKind as KK

from pprint import pprint

source = "def ident(anon ident: mut Type)"
source = "enum Color { Red, Green, Blue, }"
tokens = lex.tokenize(source)
tokens = list(filter(lambda token: not isinstance(token, lexemes.Whitespace), tokens))

stream = TokenStream(tokens)

# pprint(tokens)

result = parse.enum_decl.parse(stream)
assert isinstance(result, comb.Match)
pprint(result.item.item)
