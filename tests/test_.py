import enum


class Priority(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    ASAP = 4

print(Priority["LOW"].value)