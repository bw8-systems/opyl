from dataclasses import dataclass

from opyl.compile.token import Identifier
from opyl.compile.types import Type


@dataclass
class TypeBinding:
    name: Identifier
    type: Type


type TypeEnvironment = list[TypeBinding]


def build_global_symbols() -> TypeEnvironment: ...
