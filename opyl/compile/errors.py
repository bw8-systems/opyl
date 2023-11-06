class CompileError(Exception):
    ...


class LexError(CompileError):
    ...


class UnexpectedCharacter(LexError):
    ...


class NoMatch(LexError):
    ...


class UnexpectedEOF(LexError):
    ...


class UnclosedStringLiteral(LexError):
    ...


class IllegalCharacter(LexError):
    ...


class ParseError(CompileError):
    ...


class UnexpectedToken(ParseError):
    ...
