from pprint import pprint
from compile.parse import OpalParser

from compile import chumsky

exit()
OpalParser("name: Type").field().parse()
OpalParser("name: Type").param_spec().parse()
OpalParser("anon name: Type").param_spec().parse()
OpalParser("name: mut Type").param_spec().parse()
OpalParser("anon name: mut Type").param_spec().parse()
OpalParser("def foo()").signature().parse()
OpalParser("def foo(param: Type)").signature().parse()
OpalParser("def foo(param: Type, name: Opal)").signature().parse()
OpalParser("def foo(param: Type, name: Opal) -> Bar").signature().parse()
OpalParser("Foo").type().parse()
OpalParser("const FOO: Foo = foo").const_decl().parse()
OpalParser("let integer: Integer = 5").var_decl().parse()
OpalParser("let mut integer: Integer = 5").var_decl().parse()
OpalParser("when foo {}").when_statement().parse()
OpalParser("when foo {is Type {}}").when_statement().parse()
OpalParser("when foo as f {}").when_statement().parse()
OpalParser("5").expression_statement().parse()
OpalParser("foo").expression_statement().parse()
OpalParser("5 + 2").expression_statement().parse()
OpalParser("is Type {}").is_arm().parse()
OpalParser("else {}").else_block().parse()
OpalParser("for idx in iter {}").for_loop().parse()
OpalParser("while expr {}").while_loop().parse()
OpalParser("struct Span {foo: Foo}").parse()

source = """
def main(args: Arguments) -> ExitStatus {
    for i in Range(10) {
        print(fibonacci(i))
    }
    return ExitStatus::Success
}
"""

parsed = OpalParser(source).parse()
pprint(parsed)
