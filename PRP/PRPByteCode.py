from PRP import PRPInstruction, PRPOpCode, PRPByteCodeContext, PRPBadInstructionError
from typing import Optional
import struct


class PRPByteCode:
    CF_READ_ARRAY:     int = 1 << 0
    CF_READ_CONTAINER: int = 1 << 1
    CF_READ_OBJECT:    int = 1 << 2
    CF_END_OF_STREAM:  int = 1 << 31

    def __init__(self, byte_code: bytes):
        self._vm_instructions: [PRPInstruction] = []
        self._vm_bytecode: bytes = byte_code

    @property
    def instructions(self) -> [PRPInstruction]:
        return self._vm_instructions

    def prepare(self, vm_flags: int, vm_token_table: [str]) -> bool:
        self._vm_instructions = []
        vm_ctx: PRPByteCodeContext = PRPByteCodeContext(0)

        while vm_ctx.index < len(self._vm_bytecode):
            self.prepare_op_code(vm_ctx, vm_flags, vm_token_table)

        return vm_ctx.is_eof

    def prepare_op_code(self, vm_ctx: PRPByteCodeContext, vm_flags: int, vm_token_table: [str]):
        current_opcode_vm_instruction: Optional[PRPInstruction] = None
        current_opcode_vm_instruction_index: int = vm_ctx.index
        current_opcode_val = self._vm_bytecode[current_opcode_vm_instruction_index]
        vm_ctx += 1

        current_opcode: PRPOpCode = PRPOpCode.from_byte(current_opcode_val)
        # --- SWITCH OP-CODE ---

        if current_opcode == PRPOpCode.ERR_UNKNOWN or current_opcode == PRPOpCode.ERR_NO_TAG:
            raise PRPBadInstructionError(f"Got bad instruction at {current_opcode_vm_instruction_index} (op-code byte is {current_opcode_val})")
        elif current_opcode == PRPOpCode.Array or current_opcode == PRPOpCode.NamedArray:
            current_opcode_vm_instruction = self.prepare_op_code_array_or_named_array(current_opcode, vm_ctx, vm_flags, vm_token_table)
        elif current_opcode == PRPOpCode.BeginObject or current_opcode == PRPOpCode.BeginNamedObject:
            current_opcode_vm_instruction = self.prepare_op_code_begin_object_or_named_object(current_opcode)
        elif current_opcode == PRPOpCode.Container or current_opcode == PRPOpCode.NamedContainer:
            current_opcode_vm_instruction = self.prepare_op_code_container_or_named_container(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.EndArray:
            current_opcode_vm_instruction = self.prepare_op_code_end_array(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.EndObject:
            current_opcode_vm_instruction = self.prepare_op_code_end_object(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.EndOfStream:
            current_opcode_vm_instruction = self.prepare_op_code_end_stream(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.Reference or current_opcode == PRPOpCode.NamedReference:
            current_opcode_vm_instruction = self.prepare_op_code_reference_or_named_reference(current_opcode)
        elif current_opcode == PRPOpCode.Char or current_opcode == PRPOpCode.NamedChar:
            current_opcode_vm_instruction = self.prepare_op_code_char_or_named_char(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.Int8 or current_opcode == PRPOpCode.NamedInt8:
            current_opcode_vm_instruction = self.prepare_op_code_int8_or_named_int8(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.Bool or current_opcode == PRPOpCode.NamedBool:
            current_opcode_vm_instruction = self.prepare_op_code_bool_or_named_bool(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.Int16 or current_opcode == PRPOpCode.NamedInt16:
            current_opcode_vm_instruction = self.prepare_op_code_int16_or_named_int16(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.Int32 or current_opcode == PRPOpCode.NamedInt32:
            current_opcode_vm_instruction = self.prepare_op_code_int32_or_named_int32(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.Float32 or current_opcode == PRPOpCode.NamedFloat32:
            current_opcode_vm_instruction = self.prepare_op_code_float32_or_named_float32(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.Float64 or current_opcode == PRPOpCode.NamedFloat64:
            current_opcode_vm_instruction = self.prepare_op_code_float64_or_named_float64(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.String or current_opcode == PRPOpCode.NamedString:
            current_opcode_vm_instruction = self.prepare_op_code_string_or_named_string(current_opcode, vm_ctx, vm_flags, vm_token_table)
        elif current_opcode == PRPOpCode.RawData or current_opcode == PRPOpCode.NamedRawData:
            current_opcode_vm_instruction = self.prepare_op_code_raw_data_or_named_raw_data(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.Bitfield or current_opcode == PRPOpCode.NameBitfield:
            current_opcode_vm_instruction = self.prepare_op_code_bitfield_or_named_bitfield(current_opcode, vm_ctx)
        elif current_opcode == PRPOpCode.SkipMark:
            current_opcode_vm_instruction = self.prepare_op_code_skip_mark(current_opcode)
        elif current_opcode == PRPOpCode.StringOrArray_E or current_opcode == PRPOpCode.StringOrArray_8E:
            current_opcode_vm_instruction = self.prepare_op_code_string_array_e_or_8e(current_opcode, vm_ctx, vm_flags, vm_token_table)
        elif current_opcode == PRPOpCode.StringArray:
            current_opcode_vm_instruction = self.prepare_op_code_string_array(current_opcode, vm_ctx, vm_flags, vm_token_table)

        # --- SAVE INSTRUCTION ---
        if current_opcode_vm_instruction is not None:
            self._vm_instructions.append(current_opcode_vm_instruction)

    def prepare_op_code_array_or_named_array(self,
                                             vm_opcode: PRPOpCode,
                                             vm_ctx: PRPByteCodeContext,
                                             vm_flags: int,
                                             vm_token_table: [str]) -> Optional[PRPInstruction]:
        vm_ctx.set_flag(PRPByteCodeContext.CF_READ_ARRAY)
        capacity: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
        vm_ctx += 4
        return PRPInstruction(vm_opcode, {'length': capacity})

    def prepare_op_code_begin_object_or_named_object(self, vm_opcode: PRPOpCode) -> Optional[PRPInstruction]:
        return PRPInstruction(vm_opcode)

    def prepare_op_code_container_or_named_container(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        vm_ctx.set_flag(PRPByteCodeContext.CF_READ_CONTAINER)
        capacity: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
        vm_ctx += 4
        return PRPInstruction(vm_opcode, {'length': capacity})

    def prepare_op_code_end_array(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        vm_ctx.unset_flag(PRPByteCodeContext.CF_READ_ARRAY)
        return PRPInstruction(vm_opcode)

    def prepare_op_code_end_object(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        vm_ctx.unset_flag(PRPByteCodeContext.CF_READ_OBJECT)
        return PRPInstruction(vm_opcode)

    def prepare_op_code_end_stream(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        vm_ctx.set_flag(PRPByteCodeContext.CF_END_OF_STREAM)
        return PRPInstruction(vm_opcode)

    def prepare_op_code_reference_or_named_reference(self, vm_opcode: PRPOpCode) -> Optional[PRPInstruction]:
        raise NotImplementedError(f"This op-code ({vm_opcode}) is not implemented yet")

    def prepare_op_code_char_or_named_char(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        value: str = self._vm_bytecode[vm_ctx.index: vm_ctx.index + 1].decode("ascii")
        vm_ctx += 1
        return PRPInstruction(vm_opcode, value)

    def prepare_op_code_bool_or_named_bool(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        value: bool = bool.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 1], "little")
        vm_ctx += 1
        return PRPInstruction(vm_opcode, value)

    def prepare_op_code_int8_or_named_int8(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        value: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 1], "little")
        vm_ctx += 1
        return PRPInstruction(vm_opcode, value)

    def prepare_op_code_int16_or_named_int16(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        value: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 2], "little")
        vm_ctx += 2
        return PRPInstruction(vm_opcode, value)

    def prepare_op_code_int32_or_named_int32(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        value: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
        vm_ctx += 4
        return PRPInstruction(vm_opcode, value)

    def prepare_op_code_float32_or_named_float32(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        value: float
        raw = self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4]
        (value) = struct.unpack('<f', raw)
        vm_ctx += 4
        return PRPInstruction(vm_opcode, value)

    def prepare_op_code_float64_or_named_float64(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        value: float
        raw = self._vm_bytecode[vm_ctx.index: vm_ctx.index + 8]
        (value) = struct.unpack('<d', raw)
        vm_ctx += 8
        return PRPInstruction(vm_opcode, value)

    def prepare_op_code_string_or_named_string(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext, vm_flags: int, vm_token_table: [str]) -> Optional[PRPInstruction]:
        result: str = self.exchange_string(vm_ctx, vm_flags, vm_token_table)
        return PRPInstruction(vm_opcode, {'length': len(result), 'data': result})

    def prepare_op_code_raw_data_or_named_raw_data(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        capacity: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
        buffer: [] = []
        vm_ctx += 4
        if capacity > 0:
            buffer = self._vm_bytecode[vm_ctx.index: vm_ctx.index + capacity]
            vm_ctx += capacity

        return PRPInstruction(vm_opcode, {'length': capacity, 'data': buffer})

    def prepare_op_code_bitfield_or_named_bitfield(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext) -> Optional[PRPInstruction]:
        value: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
        vm_ctx += 4
        return PRPInstruction(vm_opcode, value)

    def prepare_op_code_skip_mark(self, vm_opcode: PRPOpCode) -> Optional[PRPInstruction]:
        return PRPInstruction(vm_opcode)

    def prepare_op_code_string_array_e_or_8e(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext, vm_flags: int, vm_token_table: [str]) -> Optional[PRPInstruction]:
        if (vm_flags >> 2) & 1:
            result: str = self.exchange_string(vm_ctx, vm_flags, vm_token_table)
            return PRPInstruction(vm_opcode, {'length': len(result), 'data': result})
        else:
            value: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
            vm_ctx += 4
            return PRPInstruction(vm_opcode, value)

    def prepare_op_code_string_array(self, vm_opcode: PRPOpCode, vm_ctx: PRPByteCodeContext, vm_flags: int, vm_token_table: [str]) -> Optional[PRPInstruction]:
        if (vm_flags >> 2) & 1:
            if (vm_flags >> 3) & 1:
                capacity: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
                vm_ctx += 4
                result: [str] = []

                for si in range(0, capacity):
                    result.append(self.exchange_string(vm_ctx, vm_flags, vm_token_table))

                return PRPInstruction(vm_opcode, result)
            else:
                raise NotImplementedError("This combination of options not implemented yet!")
        else:
            value: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
            vm_ctx += 4
            return PRPInstruction(vm_opcode, value)

    def exchange_string(self, vm_ctx: PRPByteCodeContext, vm_flags: int, vm_token_table: [str]) -> str:
        if (vm_flags >> 3) & 1:
            token_index: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
            vm_ctx += 4
            if token_index < 0 or token_index >= len(vm_token_table):
                raise IndexError(f"Token index '{token_index}' is out of bounds (op-instruction: {vm_ctx.index - 4})")

            return vm_token_table[token_index]
        else:
            length: int = int.from_bytes(self._vm_bytecode[vm_ctx.index: vm_ctx.index + 4], "little")
            vm_ctx += 4
            if length <= 0:
                raise PRPBadInstructionError(f"Got bad instruction at {vm_ctx.index - 4}")

            raw_bytes: [] = self._vm_bytecode[vm_ctx.index: vm_ctx.index + length]
            vm_ctx += length
            return ''.join(raw_bytes)
