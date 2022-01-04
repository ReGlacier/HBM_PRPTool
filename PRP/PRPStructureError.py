class PRPStructureError(Exception):
    def __init__(self, message, offset):
        super().__init__(message)
        self.offset = offset
