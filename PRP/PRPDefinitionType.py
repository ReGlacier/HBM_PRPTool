from enum import IntEnum


class PRPDefinitionType(IntEnum):
    Array_Int32 = 2,
    Array_Float32 = 3,
    StringRef_1 = 0xC,
    StringRef_2 = 0xE,
    StringRef_3 = 0x10,
    StringRefTab = 0x11,
    ERR_UNKNOWN = 0xFFFF

    @staticmethod
    def from_byte(value: int):
        if value == 2:
            return PRPDefinitionType.Array_Int32
        if value == 3:
            return PRPDefinitionType.Array_Float32
        if value == 0xC:
            return PRPDefinitionType.StringRef_1
        if value == 0xE:
            return PRPDefinitionType.StringRef_2
        if value == 0x10:
            return PRPDefinitionType.StringRef_3
        if value == 0x11:
            return PRPDefinitionType.StringRefTab

        return PRPDefinitionType.ERR_UNKNOWN
