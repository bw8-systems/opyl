from pprint import pprint

from compile import lex
from compile import parse


tokens_or_error = lex.tokenize(
    """
    module Foo {
        struct Token {
            Span span,
            TokenKind kind,
        };
    };
    """
)

if isinstance(tokens_or_error, lex.LexError):
    print(f"Lexing failed with {tokens_or_error}")
    exit()
tokens = tokens_or_error

for token in tokens:
    pprint(token.kind)
exit()

modules = parse.parse(tokens)
if isinstance(modules, parse.ParseError):
    print(f"Error: {modules}")
    exit()

print("Printing modules:")
for module in modules:
    pprint(module)
