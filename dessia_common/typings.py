from typing import TypeVar, Generic, Dict, Any, Tuple


T = TypeVar('T')


class Subclass(Generic[T]):
    pass


class InstanceOf(Generic[T]):
    pass


class MethodType(Generic[T]):
    def __init__(self, class_: T, name: str):
        self.class_ = class_
        self.name = name


# Types Aliases
JsonSerializable = Dict[str, Any]
RGBColor = Tuple[float, float, float]


# Measures
class Measure(float):
    units = ''


class Distance(Measure):
    units = 'm'


class Force(Measure):
    units = 'N'


class Torque(Measure):
    units = 'Nm'


class Mass(Measure):
    units = 'kg'


class Stress(Measure):
    units = 'Pa'
