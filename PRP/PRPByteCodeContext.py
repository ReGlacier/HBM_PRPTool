class PRPByteCodeContext:
    CF_READ_ARRAY: int = 1 << 0
    CF_READ_CONTAINER: int = 1 << 1
    CF_READ_OBJECT: int = 1 << 2
    CF_END_OF_STREAM: int = 1 << 31

    def __init__(self, op_index: int = 0):
        self._op_index = op_index
        self._cf_flags = 0x0

    @property
    def index(self) -> int:
        return self._op_index

    @property
    def flags(self) -> int:
        return self._cf_flags

    @property
    def is_eof(self) -> bool:
        return bool(self._cf_flags & PRPByteCodeContext.CF_END_OF_STREAM)

    @property
    def is_array(self) -> bool:
        return bool(self._cf_flags & PRPByteCodeContext.CF_READ_ARRAY)

    @property
    def is_container(self) -> bool:
        return bool(self._cf_flags & PRPByteCodeContext.CF_READ_CONTAINER)

    @property
    def is_object(self) -> bool:
        return bool(self._cf_flags & PRPByteCodeContext.CF_READ_OBJECT)

    def __iadd__(self, other):
        self._op_index += other
        return self

    def __isub__(self, other):
        self._op_index -= other
        return self

    def set_flag(self, flag: int):
        self._cf_flags |= flag

    def unset_flag(self, flag: int):
        self._cf_flags &= ~flag

    def is_set(self, flag: int) -> bool:
        return bool(self._cf_flags & flag)

    def set_index(self, index: int):
        self._op_index = index
