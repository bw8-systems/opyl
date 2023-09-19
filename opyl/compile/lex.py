"""
Tools for tokenizing the Opal lexicon.
"""

from dataclasses import dataclass
import enum
from typing import Callable, Literal, Generic, TypeVar


class KeywordTokenKind(enum.Enum):
    """
    KeywordKind enumerates the keywords which are legal in Opal.
    """

    Const = "const"
    Struct = "struct"
    Enum = "enum"
    Typedef = "typedef"
    Module = "module"
    Uint = "uint"
    Int = "int"


class PrimitiveTokenKind(enum.Enum):
    LeftBrace = "{"
    RightBrace = "}"
    LeftBracket = "["
    RightBracket = "]"
    SemiColon = ";"
    Comma = ","
    Equals = "="
    Plus = "+"


@dataclass
class IdentifierTokenValue:
    identifier: str


@dataclass
class IntegerTokenValue:
    integer: int


TokenKind = (
    PrimitiveTokenKind | KeywordTokenKind | IdentifierTokenValue | IntegerTokenValue
)


@dataclass
class Span:
    """
    Represents start and end bounds of a token within source.
    """

    # TODO: Use "TextPosition" rather than raw integers.
    start: int
    end: int

    def __add__(self, other: "Span") -> "Span":
        if not isinstance(other, Span):
            return NotImplemented

        return Span(self.start, other.end)


@dataclass
class Token:
    kind: TokenKind
    span: Span


class LexErrorKind(enum.Enum):
    UnexpectedEOF = enum.auto()
    UnexpectedCharacter = enum.auto()
    NoMatch = enum.auto()


@dataclass
class LexError(Exception):
    """
    Base Exception type for all exceptions used by Opal lex tools.
    """

    kind: LexErrorKind


def take_while(data: str, pred: Callable[[str], bool]) -> tuple[str, int]:
    """
    Consume provided input character by character while predicate remains True.

    Parameters:
        data: str - Input to be consumed.
        pred: (str) -> bool - Predicate to check characters against.

    Returns:
        remaining, count = take_while(str, (str) -> bool)
        remaining: str - Unconsumed input.
        count: int - Number of characters consumed.
    """

    current_index = 0

    for char in data:
        should_not_continue = not pred(char)

        if should_not_continue:
            break

        current_index += 1

    if current_index == 0:
        raise LexError(LexErrorKind.NoMatch)

    return data[0:current_index], current_index


def skip_until(data: str, pattern: str) -> str:
    """
    Consume provided input character by character until pattern is found.

    Parameters:
        data: str - Input to be consumed.
        pattern: str - Pattern to search for.

    Returns:
        str - The remainder of the input.
    """

    while len(data) and not data.startswith(pattern):
        data = data[1:]

    return data[len(pattern) :]


def tokenize_identifier_or_keyword(
    data: str,
) -> tuple[IdentifierTokenValue | KeywordTokenKind, int]:
    """
    Attempt to consume Identifier or Keyword token type from input.

    Parameters:
        data: str - Input to tokenize.

    Returns:
        kind, length = tokenize_identifier_or_keyword(str)
        kind: Identifier | Keyword - Type of Token successfully lexed.
        length: int - Number of characters consumed from input.
    """

    try:
        first_character = data[0]
    except IndexError:
        raise LexError(LexErrorKind.UnexpectedEOF)

    if first_character.isdigit():
        raise LexError(LexErrorKind.UnexpectedCharacter)

    name, chars_read = take_while(data, lambda char: char == "_" or char.isalnum())

    # TODO: Use pattern matching here instead
    kind: KeywordTokenKind | IdentifierTokenValue
    try:
        kind = KeywordTokenKind(name)
    except ValueError:
        kind = IdentifierTokenValue(name)

    return kind, chars_read


def tokenize_integer(data: str) -> tuple[IntegerTokenValue, int]:
    """
    Attempt to consume an Integer token type from input.

    Parameters:
        data: str - Input to tokenize.

    Returns:
        IntegerTokenValue, int - Consumed Integer token type, then its length.
    """

    integer, chars_read = take_while(data, lambda char: char.isdigit())
    return IntegerTokenValue(int(integer)), chars_read


def skip_whitespace(data: str) -> int:
    """
    Consume whitespace input.

    Parameters:
        data: str - Input to consume.

    Returns:
        int - Number of whitespace characters consumed.
    """

    try:
        _, chars_read = take_while(data, lambda char: char.isspace())
    except LexError as exc:
        # TODO: Rethink exception handling in cases like this. This is an
        # ideal pattern matching scenario and it'd be best to avoid using
        # exceptions for implicit flow control like this. (From caller's
        # perspective)
        if exc.kind is LexErrorKind.NoMatch:
            return 0
        raise

    return chars_read


def skip_comments(data: str) -> int:
    """
    Consume comments input.

    Parameters:
        data: str - Input to consume.

    Returns:
        int - Number of comment characters consumed.
    """

    if data.startswith("//"):
        leftovers = skip_until(data, "\n")
        return len(data) - len(leftovers)

    return 0


def skip(data: str) -> int:
    """
    Consume comments and whitespace from input.

    Parameters:
        data: str - Input to be consumed.

    Returns:
        int - Number of comment and whitespace characters consumed.
    """

    remaining = data

    while True:
        whitespace_count = skip_whitespace(remaining)
        remaining = remaining[whitespace_count:]
        comment_count = skip_comments(remaining)
        remaining = remaining[comment_count:]

        if whitespace_count + comment_count == 0:
            return len(data) - len(remaining)


def token(data: str) -> tuple[TokenKind, int] | None:
    """
    Consume token from input, if it exists.

    Parameters:
        data: str - Input to tokenize.

    Returns:
        None - Input is exhausted.
        TokenKind | KeywordKind | str, int - Kind of consumed token, and its length.
    """

    try:
        next_char = data[0]
    except IndexError:
        return None

    token_kind: TokenKind
    length: int

    if next_char in (member.value for member in PrimitiveTokenKind):
        token_kind = PrimitiveTokenKind(next_char)
        length = 1

    elif next_char.isdigit():
        token_kind, length = tokenize_integer(data)

    elif next_char == "_" or next_char.isalpha():
        token_kind, length = tokenize_identifier_or_keyword(data)

    else:
        raise LexError(LexErrorKind.UnexpectedCharacter)

    return token_kind, length


class Tokenizer:
    """
    Represents an input to be tokenized

    Parameters:
        source: str - The input to be tokenized.

    Attributes:
        current_index: int - Index into source, where lexing is occurring.
        remaining_text: str - Unconsumed portion of source.
    """

    def __init__(self, source: str):
        self.current_index = 0
        self.remaining_text = source

    def __repr__(self) -> str:
        if len(self.remaining_text) < 15:
            return f'Tokenizer("{self.remaining_text}")'
        return f'Tokenizer("{self.remaining_text[0:15]}...")'

    def next_token(self) -> Token | None:
        """
        Consume one token from front of input, if it exists.

        Returns:
            None - Input has been exhausted.
            Token - Consumed Token.
        """

        self.skip_whitespace()

        if not len(self.remaining_text):
            return None

        start = self.current_index

        token_kind_or_none = self._next_token()
        if token_kind_or_none is None:
            return None

        end = self.current_index

        return Token(kind=token_kind_or_none, span=Span(start, end))

    def skip_whitespace(self) -> None:
        """
        Consume whitespace and comments from remaining input.
        """

        skipped = skip(self.remaining_text)
        self.chomp(skipped)

    def _next_token(self) -> TokenKind | None:
        """
        Consume token from remaining input, if it exists.

        Returns:
            None - Input is exhausted.
            TokenKind - Type of Token consumed.

        Raises:
            UnexpectedCharacter - Remaining input contained character which is illegal in all Tokens.
        """

        result = token(self.remaining_text)
        if result is None:
            return None

        token_kind, chars_read = result
        self.chomp(chars_read)

        return token_kind

    def chomp(self, count: int) -> None:
        """
        Remove characters from remaining input.

        Parameters:
            count: int - Number of characters to remove.

        """

        self.remaining_text = self.remaining_text[count:]
        self.current_index += count


def tokenize(data: str) -> list[Token]:
    """
    Produce a list of Tokens from the provided input.

    Parameters:
        data: str - Input to be tokenized.

    Returns:
        list[Tokens] - List of Tokens.
    """

    tokenizer = Tokenizer(data)
    tokens: list[Token] = []

    while True:
        result = tokenizer.next_token()

        if result is None:
            break

        tokens.append(result)

    return tokens
