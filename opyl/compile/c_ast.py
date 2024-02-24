import enum
from dataclasses import dataclass


class Identifier:
    name: str


type Type = BasicType | DerivedType

type BasicType = ArithmeticType | PointerType
type DerivedType = AggregateType | UnionType | FunctionType | PointerType

type ArithmeticType = IntegralType | FloatingType
type IntegralType = CharacterType | IntegerType | EnumeratedType

type FloatingType = RealFloatingType | ComplexFloatingType

type AggregateType = ArrayType | StructureType


@dataclass
class UnionType:
    name: Identifier | None  # Anonymous union
    members: list[tuple[Type, Identifier]]


@dataclass
class FunctionType:
    name: Identifier
    return_type: Type
    parameters: list[tuple[Type, Identifier | None]]


@dataclass
class PointerType:
    base: Type


@dataclass
class CharacterType:
    char: str


class IntegerSignedness(enum.Enum):
    Signed = enum.auto()
    Unsigned = enum.auto()


class IntegerWidth(enum.Enum):
    Short = "short"
    Int = "int"
    Long = "long"
    LongLong = "long long"


@dataclass
class IntegerType:
    signedness: IntegerSignedness
    width: IntegerWidth


@dataclass
class EnumeratedType:
    identifier: Identifier | None  # Anonymous enum
    members: list[tuple[Identifier, IntegralType | None]]


class FloatingPointSize(enum.Enum):
    Float = "float"
    Double = "double"


@dataclass
class RealFloatingType:
    size: FloatingPointSize


@dataclass
class ComplexFloatingType: ...


@dataclass
class ArrayType:
    identifier: Identifier
    base: Type
    length: IntegralType


@dataclass
class StructureType:
    identifier: Identifier | None  # Anonymous struct
    members: list[tuple[Type, Identifier]]


for thing in FloatingPointSize:
    print(thing)
