"""
Tools for tokenizing the Opal lexicon.
"""

import enum
from typing import Callable

from compile import token

var: token.Token
ls: list[token.Token] = []

class LexError(enum.Enum):
    UnexpectedEOF = enum.auto()
    UnexpectedCharacter = enum.auto()
    NoMatch = enum.auto()


type LexResult[T] = T | LexError


def take_while(data: str, pred: Callable[[str], bool]) -> LexResult[tuple[str, int]]:
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
        return LexError.NoMatch

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
) -> LexResult[tuple[token.KeywordKind | str, int]]:
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
        return LexError.UnexpectedEOF

    if first_character.isdigit():
        return LexError.UnexpectedCharacter

    match take_while(data, lambda char: char == "_" or char.isalnum()):
        case (name, chars_read):
            ...
        case LexError() as error:
            return error

    # TODO: Use pattern matching here instead
    token_kind: token.KeywordKind | str
    try:
        token_kind = token.KeywordKind(name)
    except ValueError:
        token_kind = name

    return token_kind, chars_read


def tokenize_integer(data: str) -> LexResult[tuple[int, int]]:
    """
    Attempt to consume an Integer token type from input.

    Parameters:
        data: str - Input to tokenize.

    Returns:
        IntegerTokenValue, int - Consumed Integer token type, then its length.
    """

    match take_while(data, str.isdigit):
        case (integer, chars_read):
            return int(integer), chars_read
        case LexError() as error:
            return error


def skip_whitespace(data: str) -> LexResult[int]:
    """
    Consume whitespace input.

    Parameters:
        data: str - Input to consume.

    Returns:
        int - Number of whitespace characters consumed.
    """

    match take_while(data, str.isspace):
        case (_, chars_read):
            return chars_read
        case LexError.NoMatch:
            return 0
        case LexError() as error:
            return error


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


def skip(data: str) -> LexResult[int]:
    """
    Consume comments and whitespace from input.

    Parameters:
        data: str - Input to be consumed.

    Returns:
        int - Number of comment and whitespace characters consumed.
    """

    remaining = data

    while True:
        match skip_whitespace(remaining):
            case LexError() as error:
                return error
            case whitespace_count:
                ...

        remaining = remaining[whitespace_count:]
        comment_count = skip_comments(remaining)
        remaining = remaining[comment_count:]

        if whitespace_count + comment_count == 0:
            return len(data) - len(remaining)


def _token(data: str) -> LexResult[tuple[token.TokenKind | int | str, int] | None]:
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

    if next_char in [member.value for member in token.PrimitiveKind]:
        return token.PrimitiveKind(next_char), 1

    elif next_char.isdigit():
        return tokenize_integer(data)

    elif next_char == "_" or next_char.isalpha():
        return tokenize_identifier_or_keyword(data)

    else:
        return LexError.UnexpectedCharacter


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

    def next_token(self) -> LexResult[token.Token | None]:
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

        result = self._next_token()
        if result is None or isinstance(result, LexError):
            return result

        if isinstance(result, token.IntegerKind):
            return token.IntegerToken(
                kind=result, value=result, span=token.Span(start, self.current_index)
            )
        if isinstance(result, token.IdentifierKind):
            return token.IdentifierToken(
                kind=result, value=result, span=token.Span(start, self.current_index)
            )
        if isinstance(result, token.PrimitiveKind):
            return token.PrimitiveToken(
                kind=result, span=token.Span(start, self.current_index)
            )

        return token.KeywordToken(kind=result, span=token.Span(start, self.current_index))

    def skip_whitespace(self) -> LexResult[None]:
        """
        Consume whitespace and comments from remaining input.
        """

        match skip(self.remaining_text):
            case LexError() as error:
                return error
            case skipped:
                self.chomp(skipped)

    def _next_token(self) -> LexResult[token.TokenKind | None]:
        """
        Consume token from remaining input, if it exists.

        Returns:
            None - Input is exhausted.
            TokenKind - Type of Token consumed.
        """

        match _token(self.remaining_text):
            case None | LexError() as off_nominal:
                return off_nominal
            case token_kind, chars_read:
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


def tokenize(data: str) -> LexResult[list[token.Token]]:
    """
    Produce a list of Tokens from the provided input.

    Parameters:
        data: str - Input to be tokenized.

    Returns:
        list[Tokens] - List of Tokens.
    """

    tokenizer = Tokenizer(data)
    tokens = list[token.Token]()

    while True:
        result = tokenizer.next_token()
        if result is None:
            break
        if isinstance(result, LexError):
            return result
        tokens.append(result)

    return tokens
