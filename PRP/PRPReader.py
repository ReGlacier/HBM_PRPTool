from PRP import PRPDefinition, PRPDefinitionType, PRPInstruction, PRPByteCode, PRPOpCode, PRPStructureError, PRPBadDefinitionError
from typing import Optional
import struct


class PRPReader:
    def __init__(self, prp_file_path: str):
        self._prp_path = prp_file_path
        self._prp_magic_bytes: bytes = bytes()
        self._prp_is_raw: bool = False
        self._prp_flags: int = 0x0
        self._prp_total_keys_count: int = 0
        self._prp_data_offset: int = 0
        self._prp_string_table: [str] = []
        self._prp_objects_presented: int = 0
        self._prp_definitions: [PRPDefinition] = []
        self._prp_properties: Optional[PRPByteCode] = None

    @property
    def flags(self) -> int:
        return self._prp_flags

    @property
    def definitions(self) -> [PRPDefinition]:
        return self._prp_definitions

    @property
    def instructions(self) -> [PRPInstruction]:
        if self._prp_properties is not None:
            return self._prp_properties.instructions

        raise RuntimeError("You should call parse() method before use this property!")

    def parse(self):
        with open(self._prp_path, "rb") as prp_file:
            # Read header
            self._prp_magic_bytes = prp_file.read(0xE)
            self._prp_is_raw = bool.from_bytes(prp_file.read(0x1), "little")
            self._prp_flags = int.from_bytes(prp_file.read(0x4), "little")
            prp_file.seek(0x4, 1)
            self._prp_total_keys_count = int.from_bytes(prp_file.read(0x4), "little")
            self._prp_data_offset = int.from_bytes(prp_file.read(0x4), "little")
            # Validate header
            if not self._prp_magic_bytes == b"IOPacked v0.1\x00":
                return

            # Read symbols table
            prp_file.seek(0x1F, 0)  # Seek to symbols region
            tmp_symbol_buffer: [] = []

            while len(self._prp_string_table) != self._prp_total_keys_count + 1:
                c = prp_file.read(0x1)
                if c == b'\x00':
                    self._prp_string_table.append(''.join(tmp_symbol_buffer))
                    tmp_symbol_buffer = []
                else:
                    tmp_symbol_buffer.append(c.decode("ascii"))

            # Read objects counter
            self._prp_objects_presented = int.from_bytes(prp_file.read(0x4), "little")

            # Read ZDefinitions
            # 1. Exchange root container
            prp_zdef_container_root_op_code_byte = int.from_bytes(prp_file.read(0x1), "little")
            prp_zdef_container_root_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_container_root_op_code_byte)
            if not prp_zdef_container_root_op_code == PRPOpCode.Container:
                raise PRPStructureError(f"Expected PRPOpCode.Container but got {prp_zdef_container_root_op_code_byte}", prp_file.tell())

            # 2. Read entry by entry
            self._prp_definitions = []
            prp_zdef_entries_count: int = int.from_bytes(prp_file.read(0x4), "little")
            if prp_zdef_entries_count <= 0:
                raise PRPStructureError(f"Bad ZDef entries count in PRP file!", prp_file.tell())

            for entry_idx in range(0, prp_zdef_entries_count):
                # 1. Read op-code
                prp_zdef_name_decl_op_code_byte = int.from_bytes(prp_file.read(0x1), "little")
                prp_zdef_name_decl_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_name_decl_op_code_byte)
                if not prp_zdef_name_decl_op_code == PRPOpCode.String:
                    raise PRPStructureError(f"Expected PRPOpCode.String but got {prp_zdef_container_root_op_code_byte}", prp_file.tell())

                prp_zdef_name_token_index: int = int.from_bytes(prp_file.read(0x4), "little")
                if prp_zdef_name_token_index < 0 or prp_zdef_name_token_index >= len(self._prp_string_table):
                    raise IndexError(f"Bad string token index (out of bounds): {prp_zdef_name_token_index}")

                prp_zdef_name: str = self._prp_string_table[prp_zdef_name_token_index]

                prp_zdef_type_kind_op_code_byte = int.from_bytes(prp_file.read(0x1), "little")
                prp_zdef_type_kind_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_type_kind_op_code_byte)
                if not prp_zdef_type_kind_op_code == PRPOpCode.Int32:
                    raise PRPStructureError(f"Expected PRPOpCode.Int32 but got {prp_zdef_type_kind_op_code_byte}", prp_file.tell())

                prp_zdef_type_kind_value: int = int.from_bytes(prp_file.read(0x4), "little")
                prp_zdef_type_kind: PRPDefinitionType = PRPDefinitionType.from_byte(prp_zdef_type_kind_value)
                if prp_zdef_type_kind == PRPDefinitionType.ERR_UNKNOWN:
                    raise PRPStructureError(f"Got bad ZDEFINTION type kind {prp_zdef_type_kind_value}", prp_file.tell())

                if prp_zdef_type_kind == PRPDefinitionType.Array_Int32:
                    prp_zdef_value_arr_i32_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                    prp_zdef_value_arr_i32_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_value_arr_i32_op_code_value)
                    if not prp_zdef_value_arr_i32_op_code == PRPOpCode.Int32:
                        raise PRPStructureError(f"Got bad ZDef<ArrI32> decl", prp_file.tell())

                    prp_zdef_value_arr_i32_capacity: int = int.from_bytes(prp_file.read(0x4), "little")
                    prp_zdef_value_arr_i32_begin_array_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                    prp_zdef_value_arr_i32_begin_array_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_value_arr_i32_begin_array_op_code_value)
                    if not prp_zdef_value_arr_i32_begin_array_op_code == PRPOpCode.Array:
                        raise PRPStructureError(f"Expected Array op-code but got {prp_zdef_value_arr_i32_begin_array_op_code_value}", prp_file.tell())
                    prp_zdef_value_arr_i32_capacity_arr: int = int.from_bytes(prp_file.read(0x4), "little")

                    if not prp_zdef_value_arr_i32_capacity_arr == prp_zdef_value_arr_i32_capacity:
                        raise PRPBadDefinitionError("ArrayInt32 capacity and BeginArray op-code length are not same")

                    prp_zdef_value_arr_i32_entries: [int] = []
                    for i32_entry_idx in range(0, prp_zdef_value_arr_i32_capacity_arr):
                        prp_zdef_arr_i32_entry_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                        prp_zdef_arr_i32_entry_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_arr_i32_entry_op_code_value)
                        if not prp_zdef_arr_i32_entry_op_code == PRPOpCode.Int32:
                            raise PRPStructureError(f"Expected Int32 decl but got {prp_zdef_arr_i32_entry_op_code_value}", prp_file.tell())

                        prp_zdef_value_arr_i32_entries.append(int.from_bytes(prp_file.read(0x4), "little"))

                    prp_zdef_arr_i32_end_array_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                    prp_zdef_arr_i32_end_array_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_arr_i32_end_array_op_code_value)
                    if not prp_zdef_arr_i32_end_array_op_code == PRPOpCode.EndArray:
                        raise PRPStructureError(f"Expected EndArray op code but got {prp_zdef_arr_i32_end_array_op_code_value}", prp_file.tell())

                    self._prp_definitions.append(PRPDefinition(prp_zdef_name, prp_zdef_type_kind, prp_zdef_value_arr_i32_entries))
                elif prp_zdef_type_kind == PRPDefinitionType.Array_Float32:
                    # Read base length
                    prp_zdef_value_arr_i32_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                    prp_zdef_value_arr_i32_op_code: PRPOpCode = PRPOpCode.from_byte(
                        prp_zdef_value_arr_i32_op_code_value)
                    if not prp_zdef_value_arr_i32_op_code == PRPOpCode.Int32:
                        raise PRPStructureError(f"Got bad ZDef<ArrF32> decl", prp_file.tell())

                    # Read array decl length
                    prp_zdef_value_arr_i32_capacity: int = int.from_bytes(prp_file.read(0x4), "little")
                    prp_zdef_value_arr_i32_begin_array_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                    prp_zdef_value_arr_i32_begin_array_op_code: PRPOpCode = PRPOpCode.from_byte(
                        prp_zdef_value_arr_i32_begin_array_op_code_value)
                    if not prp_zdef_value_arr_i32_begin_array_op_code == PRPOpCode.Array:
                        raise PRPStructureError(
                            f"Expected Array op-code but got {prp_zdef_value_arr_i32_begin_array_op_code_value}",
                            prp_file.tell())
                    prp_zdef_value_arr_i32_capacity_arr: int = int.from_bytes(prp_file.read(0x4), "little")

                    if not prp_zdef_value_arr_i32_capacity_arr == prp_zdef_value_arr_i32_capacity:
                        raise PRPBadDefinitionError("ArrayInt32 capacity and BeginArray op-code length are not same")

                    prp_zdef_value_arr_f32_entries: [float] = []
                    for i32_entry_idx in range(0, prp_zdef_value_arr_i32_capacity_arr):
                        prp_zdef_arr_i32_entry_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                        prp_zdef_arr_i32_entry_op_code: PRPOpCode = PRPOpCode.from_byte(
                            prp_zdef_arr_i32_entry_op_code_value)
                        if not prp_zdef_arr_i32_entry_op_code == PRPOpCode.Float32:
                            raise PRPStructureError(
                                f"Expected Int32 decl but got {prp_zdef_arr_i32_entry_op_code_value}", prp_file.tell())

                        prp_f32_val: float
                        (prp_f32_val) = struct.unpack('<f', prp_file.read(0x4))
                        prp_zdef_value_arr_f32_entries.append(prp_f32_val)

                    prp_zdef_arr_i32_end_array_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                    prp_zdef_arr_i32_end_array_op_code: PRPOpCode = PRPOpCode.from_byte(
                        prp_zdef_arr_i32_end_array_op_code_value)
                    if not prp_zdef_arr_i32_end_array_op_code == PRPOpCode.EndArray:
                        raise PRPStructureError(
                            f"Expected EndArray op code but got {prp_zdef_arr_i32_end_array_op_code_value}",
                            prp_file.tell())

                    self._prp_definitions.append(PRPDefinition(prp_zdef_name, prp_zdef_type_kind, prp_zdef_value_arr_f32_entries))
                elif prp_zdef_type_kind in [PRPDefinitionType.StringRef_1, PRPDefinitionType.StringRef_2, PRPDefinitionType.StringRef_3]:
                    prp_zdef_value_str_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                    prp_zdef_value_str_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_value_str_op_code_value)
                    if not prp_zdef_value_str_op_code == PRPOpCode.String:
                        raise PRPStructureError(f"Expected StringRef but got {prp_zdef_value_str_op_code_value}", prp_file.tell())

                    prp_zdef_value_str_ref_index: int = int.from_bytes(prp_file.read(0x4), "little")
                    if prp_zdef_value_str_ref_index < 0 or prp_zdef_value_str_ref_index >= len(self._prp_string_table):
                        raise IndexError(f"String ref is out of bounds ({prp_zdef_value_str_ref_index})")

                    self._prp_definitions.append(PRPDefinition(prp_zdef_name, prp_zdef_type_kind,
                                                               self._prp_string_table[prp_zdef_value_str_ref_index]))
                elif prp_zdef_type_kind == PRPDefinitionType.StringRefTab:
                    prp_zdef_value_str_ref_tab_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                    prp_zdef_value_str_ref_tab_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_value_str_ref_tab_op_code_value)
                    if not prp_zdef_value_str_ref_tab_op_code == PRPOpCode.Container:
                        raise PRPStructureError(f"Expected Container but got {prp_zdef_value_str_ref_tab_op_code_value}", prp_file.tell())

                    prp_zdef_value_str_ref_tab_capacity: int = int.from_bytes(prp_file.read(0x4), "little")
                    prp_zdef_value_str_ref_value: [str] = []

                    for str_ref_entry_idx in range(0, prp_zdef_value_str_ref_tab_capacity):
                        # 1. Read string btopc
                        prp_zdef_value_str_ref_tab_entry_op_code_value = int.from_bytes(prp_file.read(0x1), "little")
                        prp_zdef_value_str_ref_tab_entry_op_code: PRPOpCode = PRPOpCode.from_byte(prp_zdef_value_str_ref_tab_entry_op_code_value)
                        if not prp_zdef_value_str_ref_tab_entry_op_code == PRPOpCode.String:
                            raise PRPStructureError(f"Expected String but got {prp_zdef_value_str_ref_tab_entry_op_code_value}", prp_file.tell())

                        # 2. Exchange string
                        if (self._prp_flags >> 3) & 1:
                            # By index
                            prp_zdef_value_str_ref_tab_entry_index: int = int.from_bytes(prp_file.read(0x4), "little")
                            if prp_zdef_value_str_ref_tab_entry_index < 0 or prp_zdef_value_str_ref_tab_entry_index >= len(
                                    self._prp_string_table):
                                raise IndexError(
                                    f"String ref is out of bounds ({prp_zdef_value_str_ref_tab_entry_index})")

                            prp_zdef_value_str_ref_value.append(
                                self._prp_string_table[prp_zdef_value_str_ref_tab_entry_index])
                        else:
                            # By raw contents
                            prp_zdef_value_str_ref_tab_entry_length: int = int.from_bytes(prp_file.read(0x4), "little")
                            prp_zdef_value_str_ref_value.append(prp_file.read(prp_zdef_value_str_ref_tab_entry_length).decode("ascii"))

                    self._prp_definitions.append(PRPDefinition(prp_zdef_name, prp_zdef_type_kind, prp_zdef_value_str_ref_value))
                else:
                    raise NotImplementedError(f"Type kind {prp_zdef_type_kind_value} not implemented yet")

            # Read ByteCode
            self._prp_properties = PRPByteCode(prp_file.read())
            self._prp_properties.prepare(self._prp_flags, self._prp_string_table)

            # Uncomment to debug
            # with open("dump.json", "a+") as json_out:
            #     import json
            #     json_out.write(json.dumps([x.__dict__() for x in self._prp_properties.instructions], indent=4, sort_keys=False))
