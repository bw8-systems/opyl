from pprint import pprint
from pathlib import Path
from opyl.support.stream import Source
from opyl.support.combinator import PR
from opyl.compile import lex
from opyl.compile import parse
from opyl.compile import symbols
from opyl.compile.error import report_lex_errors, report_parse_error


def compile(source_fpath: Path, text: str):
    source = Source(text, source_fpath)
    lex_result = lex.tokenize(source=text, file_handle=source_fpath)

    report_lex_errors(lex_result.errors, source)

    match parse.parse(lex_result.stream):
        case PR.Match(decls):
            pprint(decls)
        case PR.NoMatch:
            print("No Match! (wtf?)")
            exit()
        case PR.Error(err, span):
            report_parse_error(err, span, source)
            exit()

    global_symbols = symbols.build_global_symbols()
