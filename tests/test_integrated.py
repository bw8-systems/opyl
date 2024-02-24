from pathlib import Path
import pytest

from opyl.compile import lex
from opyl.compile import parse
from opyl.support.combinator import PR
from opyl.io import file

TEST_CASES = Path("tests/test_cases/").glob("*.opal")


# TODO: Make a test case for this
# enum TestEnum {
#     Foo.f5
# }


@pytest.mark.parametrize("source_path,", TEST_CASES)
def test_cases(source_path: Path):
    text = file.File.open(source_path).unwrap().read().unwrap()
    lex_result = lex.tokenize(text)
    assert len(lex_result.errors) == 0

    parse_result = parse.parse(lex_result.stream)
    assert isinstance(parse_result, PR.Match)
    assert len(parse_result.item) != 0
