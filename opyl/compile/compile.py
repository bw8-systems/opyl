from pprint import pprint

from opyl.support.stream import Source
from opyl.compile import lex
from opyl.compile.error import report_lex_errors


def compile(source_fname: str, text: str):
    source = Source(text, source_fname)
    lex_result = lex.tokenize(text, source_fname)
    report_lex_errors(lex_result.errors, source)
    pprint(lex_result.stream.spans)
    # match parse.parse(lex_result.stream):
    #     case PR.Match(item):
    #         ...
    #         # pprint(item)
    #     case PR.NoMatch:
    #         ...
    #     case PR.Error(err, span):
    #         fmt = format_error(err, span, source)
    #         # print(fmt)
