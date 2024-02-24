# import typing as t
# from dataclasses import dataclass

# from opyl.support.combinator import Parser, ParseResult, Just
# from opyl.support.stream import Stream


# class Recover[In]:
#     def recover(self, input: Stream[In])


# class SkipUntil[In, Err](Recover):
#     just: Just[In, Err]


# # @dataclass
# # class Recover[In, Out, Err](Parser[In, Out, Err]):
# #     strategy: Strategy

# #     @t.override
# #     def parse(self, input: Stream[In]) -> ParseResult.Type[In, Out, Err]:
# #         ...
