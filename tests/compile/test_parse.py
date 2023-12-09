import pytest

from opyl import parse
from opyl import combinators
from opyl import lexemes
from opyl import lex
from opyl import nodes


def _strip_whitespace(source: str) -> combinators.TokenStream:
    tokens = list(
        filter(
            lambda token: not isinstance(token, lexemes.Whitespace),
            lex.tokenize(source),
        )
    )
    return combinators.TokenStream(tokens)


def test_valid_const_decl():
    stream = _strip_whitespace("const ident: Type = expr")

    result = parse.const_decl(stream)
    assert isinstance(result, combinators.Parse.Match)

    const = result.item
    assert isinstance(const, nodes.ConstDeclaration)
    assert const.name.name == "ident"

    assert isinstance(const.type, nodes.Identifier)
    assert const.type.name == "Type"

    assert isinstance(const.initializer, nodes.Identifier)
    assert const.initializer.name == "expr"


@pytest.mark.parametrize(
    ("source",),
    [("const ident = expr",), ("const ident: Type",), ("const",), ("const ident",)],
)
def test_invalid_const_decl(source: str):
    stream = _strip_whitespace(source)

    result = parse.const_decl(stream)
    assert isinstance(result, combinators.Parse.Errors)


def test_valid_let_mut_decl():
    ident = "ident"
    type = "Type"
    expr = "expr"

    stream = _strip_whitespace(f"let mut {ident}: {type} = {expr}")
    result = parse.let_decl(stream)

    assert isinstance(result, combinators.Parse.Match)
    item = result.item

    assert item.is_mut is True
    assert item.name.name == ident
    assert isinstance(item.type, nodes.Identifier) and item.type.name == type
    assert (
        isinstance(item.initializer, nodes.Identifier) and item.initializer.name == expr
    )


def test_valid_let_decl():
    ident = "ident"
    type = "Type"
    expr = "expr"

    stream = _strip_whitespace(f"let {ident}: {type} = {expr}")
    result = parse.let_decl(stream)

    assert isinstance(result, combinators.Parse.Match)
    item = result.item

    assert item.is_mut is False
    assert item.name.name == ident
    assert isinstance(item.type, nodes.Identifier) and item.type.name == type
    assert (
        isinstance(item.initializer, nodes.Identifier) and item.initializer.name == expr
    )


@pytest.mark.parametrize(
    ("source",),
    [
        ("let ident = expr",),
        ("let ident: Type",),
        ("let",),
        ("let ident",),
        ("let mut ident = expr",),
        ("let mut ident: Type",),
        ("let mut",),
        ("let mut ident",),
    ],
)
def test_invalid_let_decl(source: str):
    stream = _strip_whitespace(source)

    result = parse.let_decl(stream)
    assert isinstance(result, combinators.Parse.Errors)


@pytest.mark.parametrize(
    ("source", "anon", "mut"),
    [
        ("ident: Type", False, False),
        ("ident: mut Type", False, True),
        ("anon ident: Type", True, False),
        ("anon ident: mut Type", True, True),
    ],
)
def test_valid_param_spec(source: str, anon: bool, mut: bool):
    stream = _strip_whitespace(source)

    result = parse.param_spec(stream)
    assert isinstance(result, combinators.Parse.Match)

    item = result.item
    assert item.is_anon is anon
    assert item.is_mut is mut


@pytest.mark.parametrize(
    ("source"),
    [
        "ident Type",
        "ident: mut",
        "anon: Type",
        "anon ident:",
    ],
)
def test_invalid_param_spec(source: str):
    stream = _strip_whitespace(source)

    result = parse.param_spec(stream)
    assert isinstance(result, combinators.Parse.Errors)


def test_valid_signature():
    source = "def func(anon param: mut Type) -> foo"
    stream = _strip_whitespace(source)

    result = parse.func_sig(stream)
    print(result)
    assert isinstance(result, combinators.Parse.Match)

    item = result.item
    assert item.name.name == "func"
    assert len(item.params) == 1

    param = item.params[0]
    assert param.ident.name == "param"
    assert param.is_anon is True
    assert param.is_mut is True

    assert item.return_type is None


def test_valid_signature_return_type():
    source = "def func(anon param: mut Type) ->"
    stream = _strip_whitespace(source)

    result = parse.func_sig(stream)
    print(result)
    assert isinstance(result, combinators.Parse.Match)

    item = result.item
    assert item.name.name == "func"
    assert len(item.params) == 1

    param = item.params[0]
    assert param.ident.name == "param"
    assert param.is_anon is True
    assert param.is_mut is True

    assert isinstance(item.return_type, nodes.Identifier)
    assert item.return_type.name == "ReturnType"


def test_valid_signature_multi_param():
    source = "def func(anon param: mut Type, foo: Foo)"
    stream = _strip_whitespace(source)

    result = parse.func_sig(stream)
    print(result)
    assert isinstance(result, combinators.Parse.Match)

    item = result.item
    assert item.name.name == "func"
    assert len(item.params) == 2

    param_one = item.params[0]
    assert param_one.ident.name == "param"
    assert param_one.is_anon is True
    assert param_one.is_mut is True

    param_two = item.params[1]
    assert param_two.ident.name == "foo"
    assert param_two.is_anon is False
    assert param_two.is_mut is False

    assert item.return_type is None


def test_valid_signature_trailing_comma():
    source = "def func(anon param: mut Type, foo: Foo,)"
    stream = _strip_whitespace(source)

    result = parse.func_sig(stream)
    print(result)
    assert isinstance(result, combinators.Parse.Match)

    item = result.item
    assert item.name.name == "func"
    assert len(item.params) == 2

    param_one = item.params[0]
    assert param_one.ident.name == "param"
    assert param_one.is_anon is True
    assert param_one.is_mut is True

    param_two = item.params[1]
    assert param_two.ident.name == "foo"
    assert param_two.is_anon is False
    assert param_two.is_mut is False

    assert item.return_type is None
