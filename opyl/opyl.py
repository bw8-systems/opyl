from compile import lex

tokens = lex.tokenize("Foo bar baz 3 + 2")

for token in tokens:
    print(token)
