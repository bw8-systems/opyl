from opyl import parse
from opyl import nodes


def test_mut_var_decl():
    parser = parse.OpalParser("let mut foo: Foo = bar\n")
    decls = parser.parse()

    assert len(decls) == 1
    var_decl = decls[0]

    assert isinstance(var_decl, nodes.VarDeclaration)
    assert var_decl.is_mut is True
    assert isinstance(var_decl.type, nodes.Identifier)
    assert var_decl.type.name == "Foo"
    assert isinstance(var_decl.initializer, nodes.Identifier)
    assert var_decl.initializer.name == "bar"


def test_var_decl():
    parser = parse.OpalParser("let foo: Foo = bar\n")
    decls = parser.parse()

    assert len(decls) == 1
    var_decl = decls[0]

    assert isinstance(var_decl, nodes.VarDeclaration)
    assert var_decl.is_mut is False
    assert isinstance(var_decl.type, nodes.Identifier)
    assert var_decl.type.name == "Foo"
    assert isinstance(var_decl.initializer, nodes.Identifier)
    assert var_decl.initializer.name == "bar"


def test_const():
    parser = parse.OpalParser("const FOO: Foo = baz\n")
    decls = parser.parse()

    assert len(decls) == 1
    const_decl = decls[0]

    assert isinstance(const_decl, nodes.ConstDeclaration)
    assert const_decl.name.name == "FOO"
    assert isinstance(const_decl.type, nodes.Identifier)
    assert const_decl.type.name == "Foo"
    assert isinstance(const_decl.initializer, nodes.Identifier)
    assert const_decl.initializer.name == "baz"


def test_struct_with_fields():
    parser = parse.OpalParser(
        """
        struct Range {
            start: u8
            stop: u8
        }
        """
    )
    decls = parser.parse()

    assert len(decls) == 1
    struct_decl = decls[0]

    assert isinstance(struct_decl, nodes.StructDeclaration)
    assert struct_decl.name.name == "Range"
    assert len(struct_decl.fields) == 2
    assert len(struct_decl.functions) == 0
    # TODO: Leverage field and function tests rather than checking
    # details here.


def test_struct_with_single_field():
    parser = parse.OpalParser(
        """
        struct Range {
            stop: u8
        }
        """
    )
    decls = parser.parse()

    assert len(decls) == 1
    struct_decl = decls[0]

    assert isinstance(struct_decl, nodes.StructDeclaration)
    assert struct_decl.name.name == "Range"
    assert len(struct_decl.fields) == 1
    assert len(struct_decl.functions) == 0


# TODO: Test that struct with zero fields cannot be parsed.
# Or should that be a semantic error at a later step in compilation?


def test_enum_members_on_line():
    parser = parse.OpalParser(
        """
        enum Color {
            Red, Green, Blue
        }
        """
    )
    decls = parser.parse()

    assert len(decls) == 1
    enum_decl = decls[0]

    assert isinstance(enum_decl, nodes.EnumDeclaration)
    assert enum_decl.name.name == "Color"
    assert len(enum_decl.members) == 3
    assert all(
        ident.name == expected
        for ident, expected in zip(enum_decl.members, ("Red", "Green", "Blue"))
    )


def test_enum_members_on_newlines():
    parser = parse.OpalParser(
        """
        enum Monty {
            Foo,
            Bar,
            Baz,
        }
        """
    )
    decls = parser.parse()

    assert len(decls) == 1
    enum_decl = decls[0]

    assert isinstance(enum_decl, nodes.EnumDeclaration)
    assert enum_decl.name.name == "Monty"
    assert len(enum_decl.members) == 3
    assert all(
        ident.name == expected
        for ident, expected in zip(enum_decl.members, ("Foo", "Bar", "Baz"))
    )


# TODO: Test enum with members and braces all on one line
# TODO: Test trailing comma on last member
def test_simple_union():
    parser = parse.OpalParser(
        """
        union Enums = Color | Monty
        """
    )
    decls = parser.parse()

    assert len(decls) == 1
    union_decl = decls[0]

    assert isinstance(union_decl, nodes.UnionDeclaration)
    assert union_decl.name.name == "Enums"
    assert len(union_decl.members) == 2
    assert all(
        ident.name == expected
        for ident, expected in zip(union_decl.members, ("Color", "Monty"))
    )
    # TODO: This test is fragile.
    # Assumes that the members - which could be any valid Type - are Identifiers
    assert len(union_decl.functions) == 0


def test_union_with_body():
    parser = parse.OpalParser(
        """
        union WithMethods = Range | u8 {
            def hella() {}
        }
        """
    )
    decls = parser.parse()

    assert len(decls) == 1
    union_decl = decls[0]

    assert isinstance(union_decl, nodes.UnionDeclaration)
    assert len(union_decl.members) == 2
    assert all(
        ident.name == expected
        for ident, expected in zip(union_decl.members, ("Range", "u8"))
    )
    # TODO: This test is fragile.
    # Assumes that the members - which could be any valid Type - are Identifiers
    assert len(union_decl.functions) == 1


def test_empty_function_decl():
    parser = parse.OpalParser("def empty() {}\n")
    decls = parser.parse()

    assert len(decls) == 1
    func_decl = decls[0]

    assert isinstance(func_decl, nodes.FunctionDeclaration)
    assert len(func_decl.body) == 0
    assert func_decl.signature.return_type is None
    # TODO: Leverage function signature tests rather than test for details here


def test_trait():
    parser = parse.OpalParser(
        """
        trait Iterable {
            def next()
        }
        """
    )
    decls = parser.parse()

    assert len(decls) == 1
    trait_decl = decls[0]

    assert isinstance(trait_decl, nodes.TraitDeclaration)
    assert trait_decl.name.name == "Iterable"
    assert len(trait_decl.functions) == 1


def test_if_statement():
    parser = parse.OpalParser("if expr { other }\n")
    stmt = parser.if_statement().parse()

    assert isinstance(stmt.if_condition, nodes.Identifier)
    assert len(stmt.if_statements) == 1
    assert isinstance(stmt.if_statements[0], nodes.Identifier)


def test_if_else_statement():
    parser = parse.OpalParser("if expr { other } else { another }\n")
    stmt = parser.if_statement().parse()

    assert isinstance(stmt.if_condition, nodes.Identifier)
    assert len(stmt.if_statements) == 1
    assert isinstance(stmt.if_statements[0], nodes.Identifier)
    assert len(stmt.else_statements) == 1
    assert isinstance(stmt.else_statements[0], nodes.Identifier)
    assert stmt.else_statements[0].name == "another"


# TODO: Check more whitespace variations for... everything
# As of 11/21/23 only newlines should have an effect


def test_function_with_params_no_return():
    parser = parse.OpalParser(
        """
        def main(foo: Foo, bar: mut Bar, anon baz: Baz) {
            let local: u32 = a

            if expr {
                other
            } else {
                another
            }

            return 0
        }
        """
    )
    decls = parser.parse()

    assert len(decls) == 1
    func_decl = decls[0]

    assert isinstance(func_decl, nodes.FunctionDeclaration)
    assert len(func_decl.signature.params) == 3
    # TODO: Leverage param spec test rather than checking details here
    assert len(func_decl.body) == 3
    assert isinstance(func_decl.body[0], nodes.VarDeclaration)
    assert isinstance(func_decl.body[1], nodes.IfStatement)
    assert isinstance(func_decl.body[2], nodes.ReturnStatement)
    # TODO: Leverage statement tests rather than checking details here


def test_when_as_else():
    parser = parse.OpalParser(
        """
        when arbitrary_value as av {
            is Foo {}
        }
        """
    )

    # TODO: Add utility for doing this more simply. This strips
    # newlines prior to the parsing target (when statement in this case)
    stmt = parser.when_statement().after_newlines().parse()

    assert (
        isinstance(stmt.expression, nodes.Identifier)
        and stmt.expression.name == "arbitrary_value"
    )
    assert isinstance(stmt.target, nodes.Identifier) and stmt.target.name == "av"
    assert len(stmt.is_clauses) == 1
    # assert len(stmt.else_statements) == 1
