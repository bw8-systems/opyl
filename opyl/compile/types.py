from dataclasses import dataclass
import enum

from opyl.compile import ast


type Type = Primitive | Struct | Enum | Alias | Reference | Array | Function


class Primitive(enum.Enum):
    Error = enum.auto()
    Boolean = ast.BuiltInType.Bool
    Str = ast.BuiltInType.Str
    Char = ast.BuiltInType.Char
    UInt8 = ast.BuiltInType.U8
    UInt16 = ast.BuiltInType.U16
    UInt32 = ast.BuiltInType.U32
    Int8 = ast.BuiltInType.I8
    Int16 = ast.BuiltInType.I16
    Int32 = ast.BuiltInType.I32


@dataclass
class Struct:
    node: ast.StructDeclaration


@dataclass
class Enum:
    node: ast.EnumDeclaration


@dataclass
class Alias:
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
