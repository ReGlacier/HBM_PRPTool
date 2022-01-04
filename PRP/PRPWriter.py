from PRP import PRPDefinition, PRPDefinitionType, PRPInstruction, PRPOpCode
import struct


class PRPWriter:
    def __init__(self, out_path: str):
        self._prp_out_path: str = out_path
        self._prp_symbols_table: [str] = []

    def write(self, prp_flags: int, prp_definitions: [PRPDefinition], prp_instructions: [PRPInstruction], is_raw: bool = False, unk0x13: int = 0):
        self._index_symbols_table(prp_definitions, prp_instructions)

        with open(self._prp_out_path, "wb") as prp_file:
            header_size: int = 0x1F
            symbols_table: bytes = self._generate_symbols_table()
            data_offset: int = header_size + len(symbols_table) - 0x1F
            header: bytes = self._generate_header(prp_flags, data_offset, is_raw, unk0x13)
            prp_file.write(header)
            prp_file.write(symbols_table)
            prp_file.write(struct.pack('<i', len([x for x in prp_instructions if x.op_code == PRPOpCode.BeginObject])))  # Write count of objects

            # Write ZDefs
            prp_file.write(struct.pack('<ci', PRPOpCode.Container.value.to_bytes(1, "little"), len(prp_definitions)))
            prp_def: PRPDefinition
            for prp_def in prp_definitions:
                prp_file.write(prp_def.to_bytes(prp_flags, self._prp_symbols_table))

            # Write instructions
            prp_instruction: PRPInstruction
            for prp_instruction in prp_instructions:
                prp_file.write(prp_instruction.to_bytes(prp_flags, self._prp_symbols_table))

    def _index_symbols_table(self, prp_definitions: [PRPDefinition], prp_instructions: [PRPInstruction]):
        symbols_table: [str] = []
        result_symbols_table: [str] = []

        prp_definition: PRPDefinition
        prp_definition_index: int

        for prp_definition_index, prp_definition in enumerate(prp_definitions):
            symbols_table.append(prp_definition.def_name)
            if prp_definition.def_type in [PRPDefinitionType.StringRef_1, PRPDefinitionType.StringRef_2,
                                           PRPDefinitionType.StringRef_3, PRPDefinitionType.StringRefTab]:
                if prp_definition.def_type == PRPDefinitionType.StringRefTab:
                    prp_str: str
                    for prp_str in prp_definition.def_data:
                        symbols_table.append(prp_str)
                else:
                    symbols_table.append(prp_definition.def_data)

        prp_instruction_index: int
        prp_instruction: PRPInstruction

        for prp_instruction_index, prp_instruction in enumerate(prp_instructions):
            if prp_instruction.op_code in [PRPOpCode.String, PRPOpCode.NamedString, PRPOpCode.StringOrArray_E,
                                           PRPOpCode.StringOrArray_8E]:
                symbols_table.append(prp_instruction.op_data['data'])
            elif prp_instruction.op_code == PRPOpCode.StringArray:
                symbol_str: str
                for symbol_str in prp_instruction.op_data:
                    symbols_table.append(symbol_str)

        for symbol_str in symbols_table:
            if symbol_str not in self._prp_symbols_table:
                self._prp_symbols_table.append(symbol_str)

    def _generate_header(self, flags: int, data_offset: int, is_raw: bool = False, unk0x13: int = 0) -> bytes:
        hdr: bytes = bytes()
        hdr += b"IOPacked v0.1\x00"
        hdr += struct.pack('<biiii', is_raw, flags, unk0x13, len([x for x in self._prp_symbols_table if len(x) > 0]), data_offset)
        return hdr

    def _generate_symbols_table(self) -> bytes:
        st: bytes = bytes()
        for string in self._prp_symbols_table:
            st += string.encode("ascii")
            st += b"\x00"
        return st
