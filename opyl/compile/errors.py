import enum


class LexError(enum.Enum):
    IllegalCharacter = enum.auto()
    UnexpectedCharacter = enum.auto()
    UnterminatedStringLiteral = enum.auto()
    UnterminatedCharacterLiteral = enum.auto()
    MalformedIntegerLiteral = enum.auto()


class ParseError(enum.Enum):
    ...
