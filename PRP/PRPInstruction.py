from PRP import PRPOpCode
from typing import Any
import struct


class PRPInstruction:
    def __init__(self, op_code: PRPOpCode, data: object = None):
        self._op_code = op_code
        self._op_data = data

    def _get_op_data(self) -> Any:
        return self._op_data

    def _set_op_data(self, new_op_data: object):
        self._op_data = new_op_data

    @property
    def op_code(self) -> PRPOpCode:
        return self._op_code

    op_data = property(_get_op_data, _set_op_data)

    @staticmethod
    def from_json(json_property):
        prp_op_code: PRPOpCode = PRPOpCode[json_property['op_code'].split('.')[1]]
        prp_op_data = json_property['op_data']

        if prp_op_data is None:
            prp_op_data = object()

        if prp_op_code == PRPOpCode.RawData or prp_op_code == PRPOpCode.NamedRawData:
            prp_res_data = {
                'length': len(prp_op_data),
                'data': bytes()
            }

            for prp_op_byte in prp_op_data:
                prp_res_data['data'] += prp_op_byte.to_bytes(1, "little")

            prp_op_data = prp_res_data

        return PRPInstruction(prp_op_code, prp_op_data)

    def __dict__(self):
        res_data = self.op_data
        if self.op_code == PRPOpCode.RawData or self.op_code == PRPOpCode.NamedRawData:
            res_data = [x for x in self.op_data['data']]

        return {
            'op_code': str(self.op_code),
            'op_data': res_data
        }

    def to_bytes(self, flags: int, token_table: [str]) -> bytes:
        res: bytes = bytes()
        res += struct.pack('<c', self.op_code.value.to_bytes(1, "little"))

        opc: PRPOpCode = self.op_code
        data = self.op_data

        if opc in [PRPOpCode.Array, PRPOpCode.NamedArray, PRPOpCode.Container, PRPOpCode.NamedContainer]:
            res += struct.pack('<i', data['length'])
        elif opc == PRPOpCode.Reference or opc == PRPOpCode.NamedReference:
            raise NotImplementedError(f"This op-code ({opc}) is not implemented yet")
        elif opc in [PRPOpCode.BeginObject, PRPOpCode.BeginNamedObject, PRPOpCode.EndObject, PRPOpCode.SkipMark, PRPOpCode.EndOfStream, PRPOpCode.EndArray]:
            pass  # Just do nothing here
        elif opc in [PRPOpCode.Char, PRPOpCode.NamedChar, PRPOpCode.Bool, PRPOpCode.NamedBool, PRPOpCode.Int8, PRPOpCode.NamedInt8]:
            res += struct.pack('<c', data.to_bytes(1, "little"))
        elif opc == PRPOpCode.Int16 or opc == PRPOpCode.NamedInt16:
            res += struct.pack('<h', data)
        elif opc in [PRPOpCode.Int32, PRPOpCode.NamedInt32, PRPOpCode.Bitfield, PRPOpCode.NameBitfield]:
            res += struct.pack('<I', data)  # Int should be unsigned to allow save 0xFFFFFFFF
        elif opc == PRPOpCode.Float32 or opc == PRPOpCode.NamedFloat32:
            res += struct.pack('<f', data[0])
        elif opc == PRPOpCode.Float64 or opc == PRPOpCode.NamedFloat64:
            res += struct.pack('<d', data[0])
        elif opc == PRPOpCode.String or opc == PRPOpCode.NamedString:
            if (flags >> 3) & 1:
                res += struct.pack('<i', token_table.index(data['data']))
            else:
                res += struct.pack('<i', len(data['data']))
                res += data['data'].encode("ascii")
                res += b"\x00"
        elif opc == PRPOpCode.RawData or opc == PRPOpCode.NamedRawData:
            res += struct.pack('<i', data['length'])
            res += data['data']
        elif opc == PRPOpCode.StringArray:
            if (flags >> 2) & 1:
                if (flags >> 3) & 1:
                    res += struct.pack('<i', len(data))
                    for entry in data:
                        if (flags >> 3) & 1:
                            res += struct.pack('<i', token_table.index(entry))
                        else:
                            res += struct.pack('<i', len(entry))
                            res += entry.encode("ascii")
                            res += b"\x00"
                else:
                    raise NotImplementedError("This combination of options not implemented yet [c1]!")
            else:
                res += struct.pack('<i', data)
        elif opc == PRPOpCode.StringOrArray_E or opc == PRPOpCode.StringOrArray_8E:
            if (flags >> 2) & 1:
                if (flags >> 3) & 1:
                    res += struct.pack('<i', token_table.index(data['data']))
                else:
                    res += struct.pack('<i', data['length'])
                    res += data['data'].encode("ascii")
            else:
                res += struct.pack('<i', data)

        return res