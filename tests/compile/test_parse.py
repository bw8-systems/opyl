import pytest

from opyl import parse
from opyl.compile.parse import field
from opyl import combinators as comb
from opyl import lexemes
from opyl import lex
from opyl import nodes

# TODO: Move into tests below.
# source = "def ident(anon ident: mut Type)"
# source = "enum Color { Red, Green, Blue, }"
# tokens = lex.tokenize(source)
# tokens = list(filter(lambda token: not isinstance(token, lexemes.Whitespace), tokens))

# stream = TokenStream(tokens)

# # pprint(tokens)

# result = parse.enum_decl.parse(stream)
# assert isinstance(result, comb.Match)
# pprint(result.item.item)


def _strip_whitespace(source: str) -> comb.TokenStream:
    tokens = list(
        filter(
            lambda token: not isinstance(token, lexemes.Whitespace),
            lex.tokenize(source),
        )
    )
    return comb.TokenStream(tokens)


class TestConstDecl:
    def test_valid(self):
        stream = _strip_whitespace("const ident: Type = expr")

        result = parse.const_decl(stream)
        assert isinstance(result, comb.Parse.Match)

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
    def test_invalid(self, source: str):
        stream = _strip_whitespace(source)

        result = parse.const_decl(stream)
        assert isinstance(result, comb.Parse.Errors)


class TestLetDecl:
    def test_valid_mut(self):
        ident = "ident"
        type = "Type"
        expr = "expr"

        stream = _strip_whitespace(f"let mut {ident}: {type} = {expr}")
        result = parse.let_decl(stream)

        assert isinstance(result, comb.Parse.Match)
        item = result.item

        assert item.is_mut is True
        assert item.name.name == ident
        assert isinstance(item.type, nodes.Identifier) and item.type.name == type
        assert (
            isinstance(item.initializer, nodes.Identifier)
            and item.initializer.name == expr
        )

    def test_valid(self):
        ident = "ident"
        type = "Type"
        expr = "expr"

        stream = _strip_whitespace(f"let {ident}: {type} = {expr}")
        result = parse.let_decl(stream)

        assert isinstance(result, comb.Parse.Match)
        item = result.item

        assert item.is_mut is False
        assert item.name.name == ident
        assert isinstance(item.type, nodes.Identifier) and item.type.name == type
        assert (
            isinstance(item.initializer, nodes.Identifier)
            and item.initializer.name == expr
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
    def test_invalid(self, source: str):
        stream = _strip_whitespace(source)

        result = parse.let_decl(stream)
        assert isinstance(result, comb.Parse.Errors)


class TestParamSpect:
    @pytest.mark.parametrize(
        ("source", "anon", "mut"),
        [
            ("ident: Type", False, False),
            ("ident: mut Type", False, True),
            ("anon ident: Type", True, False),
            ("anon ident: mut Type", True, True),
        ],
    )
    def test_valid(self, source: str, anon: bool, mut: bool):
        stream = _strip_whitespace(source)

        result = parse.param_spec(stream)
        assert isinstance(result, comb.Parse.Match)

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
    def test_invalid(self, source: str):
        stream = _strip_whitespace(source)

        result = parse.param_spec(stream)
        assert isinstance(result, comb.Parse.Errors)


class TestFunctionSignature:
    def test_valid_signature(self):
        source = "def func(anon param: mut Type)"
        stream = _strip_whitespace(source)

        result = parse.func_sig(stream)
        print(result)
        assert isinstance(result, comb.Parse.Match)

        item = result.item
        assert item.name.name == "func"
        assert len(item.params) == 1

        param = item.params[0]
        assert param.ident.name == "param"
        assert param.is_anon is True
        assert param.is_mut is True

        assert item.return_type is None

    def test_valid_signature_return_type(self):
        source = "def func(anon param: mut Type) -> ReturnType"
        stream = _strip_whitespace(source)

        result = parse.func_sig(stream)
        assert isinstance(result, comb.Parse.Match)

        item = result.item
        assert item.name.name == "func"
        assert len(item.params) == 1

        param = item.params[0]
        assert param.ident.name == "param"
        assert param.is_anon is True
        assert param.is_mut is True

        assert isinstance(item.return_type, nodes.Identifier)
        assert item.return_type.name == "ReturnType"

    def test_valid_signature_multi_param(self):
        source = "def func(anon param: mut Type, foo: Foo)"
        stream = _strip_whitespace(source)

        result = parse.func_sig(stream)
        print(result)
        assert isinstance(result, comb.Parse.Match)

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

    def test_valid_signature_trailing_comma(self):
        source = "def func(anon param: mut Type, foo: Foo,)"
        stream = _strip_whitespace(source)

        result = parse.func_sig(stream)
        print(result)
        assert isinstance(result, comb.Parse.Match)

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


class TestField:
    def test_match(self):
        stream = _strip_whitespace("name: Type")
        result = field.parse(stream)
        assert isinstance(result, comb.Parse.Match)

    def test_empty(self):
        stream = _strip_whitespace("")
        result = field.parse(stream)

        assert isinstance(result, comb.Parse.Errors) and len(result.errors) == 2

    def test_missing_name(self):
        stream = _strip_whitespace(": Type")
        result = field.parse(stream)

        assert isinstance(result, comb.Parse.Errors) and len(result.errors) == 2
        # TODO: How to test for specific error messages? I don't think that unit
        # tests are the correct place to do this because it makes them fragile
        # because the error messages could be tweaked for readability / clarity
        # without actually changing what they're signalling, which is what is meant
        # to be tested for here. Perhaps, there should be a sort of error enum / group
        # to formulate things such as "Kind -> ExpectedFooAfterBar(foo=":", bar="identifier")"
        # But this could grow quite unwieldly depending on the type of errors being reported.
        # Maybe its too early to care.

    def test_missing_colon(self):
        stream = _strip_whitespace("name Type")
        result = field.parse(stream)

        assert isinstance(result, comb.Parse.Errors) and len(result.errors) == 2

    def test_missing_type(self):
        stream = _strip_whitespace("name: ")
        result = field.parse(stream)

        assert isinstance(result, comb.Parse.Errors) and len(result.errors) == 2

    def test_missing_colon_and_type(self):
        stream = _strip_whitespace("name")
        result = field.parse(stream)

        assert isinstance(result, comb.Parse.Errors) and len(result.errors) == 2
