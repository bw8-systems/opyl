from pprint import pprint

from compile import pratt
from compile import lex
from compile import lexemes
from compile import parse
from compile.positioning import Stream

source = "(2+(foo*2+3-(foo+bar)))"
source = "foo(1 * some, 4 / (var + 6), name ^ 6)"
source = "function_call()"
source = "array[index]"
tokens = list(
    filter(
        lambda token: not isinstance(token, lexemes.Whitespace),
        lex.tokenize(source),
    )
)
parser = pratt.ExpressionParser(Stream(tokens))
parsed = parser.parse()

pprint(parsed)
