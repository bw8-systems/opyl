import typing as t


def wrapper(members: tuple[tuple[str, type], ...]):
    return t.NamedTuple("SomeType", members)


Point = wrapper((("foo", int), ("bar", int)))
p = Point(1, 2)
