class FileDescriptor:
    def __init__(self, file_type, size=0):
        self.file_type = file_type
        self.hard_links = 1
        self.size = size
        self.block_map = []