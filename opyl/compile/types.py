from dataclasses import dataclass
import enum

from opyl.compile import ast


type Type = Primitive | Struct | Enum | Alias | Reference | Array | Function


class Primitive(enum.Enum):
    String = enum.auto()
    Character = enum.auto()
    UInt8 = enum.auto()
    UInt16 = enum.auto()
    UInt32 = enum.auto()
    Int8 = enum.auto()
    Int16 = enum.auto()
    Int32 = enum.auto()


@dataclass
class Struct(enum.Enum):
    node: ast.StructDeclaration


@dataclass
class Enum(enum.Enum):
    node: ast.EnumDeclaration


@dataclass
class Alias(enum.Enum):
    base: Type


@dataclass
class Reference:
    base: Type
    is_mut: bool


@dataclass
class Array:
    base: Type
    size: int


@dataclass
class Function:
    node: ast.FunctionSignature
