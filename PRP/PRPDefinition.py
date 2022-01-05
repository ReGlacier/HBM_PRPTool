from PRP import PRPDefinitionType, PRPOpCode
from typing import Any
import struct


class PRPDefinition:
    def __init__(self, def_name: str, def_type: PRPDefinitionType, def_data: object = object()):
        self._def_name = def_name
        self._def_type = def_type
        self._def_data = def_data

    @staticmethod
    def from_json(json_definition):
        prp_def_name: str = json_definition['name']
        prp_def_type: PRPDefinitionType = PRPDefinitionType[json_definition['type'].split('.')[1]]
        prp_def_data = json_definition['data']

        return PRPDefinition(prp_def_name, prp_def_type, prp_def_data)

    def __dict__(self):
        return {'name': self.def_name, 'type': str(self.def_type), 'data': self.def_data}

    @property
    def def_name(self) -> str:
        return self._def_name

    @property
    def def_type(self) -> PRPDefinitionType:
        return self._def_type

    @property
    def def_data(self) -> Any:
        return self._def_data

    def to_bytes(self, prp_flags: int, prp_symbols_table: [str]) -> bytes:
        #TODO: Support packing of string by special flag in prp_flags
        res: bytes = bytes()

        res += struct.pack('<ci', PRPOpCode.String.value.to_bytes(1, "little"), prp_symbols_table.index(self.def_name))
        res += struct.pack('<ci', PRPOpCode.Int32.value.to_bytes(1, "little"), self.def_type.value)

        if self.def_type == PRPDefinitionType.Array_Int32 or self.def_type == PRPDefinitionType.Array_Float32:
            capacity: int = len(self.def_data)
            # 1. Write capacity as Int32 value
            res += struct.pack('<ci', PRPOpCode.Int32.value.to_bytes(1, "little"), capacity)
            # 2. Write Array declaration with same capacity
            res += struct.pack('<ci', PRPOpCode.Array.value.to_bytes(1, "little"), capacity)
            # 3. Write values
            for entry in self.def_data:
                if self.def_type == PRPDefinitionType.Array_Int32:
                    res += struct.pack('<ci', PRPOpCode.Int32.value.to_bytes(1, "little"), entry)
                else:
                    res += struct.pack('<cf', PRPOpCode.Float32.value.to_bytes(1, "little"), entry[0])
            res += struct.pack('<c', PRPOpCode.EndArray.value.to_bytes(1, "little"))
        elif self.def_type in [PRPDefinitionType.StringRef_1, PRPDefinitionType.StringRef_2, PRPDefinitionType.StringRef_3]:
            # Write string tag and string index
            res += struct.pack('<ci', PRPOpCode.String.value.to_bytes(1, "little"), prp_symbols_table.index(self.def_data))
        elif self.def_type == PRPDefinitionType.StringRefTab:
            # 1. Write Op-Code Container
            res += struct.pack('<ci', PRPOpCode.Container.value.to_bytes(1, "little"), len(self.def_data))
            # 2. Write each entry
            for entry in self.def_data:
                res += struct.pack('<ci', PRPOpCode.String.value.to_bytes(1, "little"), prp_symbols_table.index(entry))

        return res
