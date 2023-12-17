from support.stream import Stream
from compile.lex import string

source = '"test'
stream = Stream[str].from_source(source)

print(string.parse(stream))
