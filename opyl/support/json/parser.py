import typing as t

from opyl.support.stream import Stream
from opyl.support.combinator import Just, startswith, Parser, ParseResult

from opyl.support.json import json


just = Just[str, t.Any]


class Json(
    Parser[
        str,
        t.Literal[json.JsonKind.Null]
        | json.Boolean
        | json.String
        | json.Number
        | json.Array
        | json.Object,
        t.Any,
    ]
):
    @t.override
    def parse(
        self, input: Stream[str]
    ) -> ParseResult.Type[
        str,
        t.Literal[json.JsonKind.Null]
        | json.Boolean
        | json.String
        | json.Number
        | json.Array
        | json.Object,
        t.Any,
    ]:
        return (null | boolean | string | number | array | object).parse(input)


token = Json()

null = (
    startswith("null").to(json.Null)
    # .map(lambda item: t.cast(t.Literal[json.JsonKind.Null], item))
)
boolean = (startswith("true") | startswith("false")).map(bool).map(json.Boolean)

string = boolean.to("string").map(json.String)
number = string.to(4).map(json.Number)

member = string.then_ignore(just(":")).then(token)

object = (
    member.separated_by(just(","))
    .delimited_by(just("{"), just("}"))
    .map(dict)
    .map(json.Object)
)

array = (
    just("[")
    .ignore_then(token.separated_by(just(",")))
    .then_ignore(just("]"))
    .map(json.Array)
)


json_test = """{
    "foo": true,
    "bar": false,
}"""

stream = Stream.from_source(json_test)
print(stream)
