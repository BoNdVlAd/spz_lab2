from FileDescriptor import *


MAX_OPEN_FILES = 100
MAX_FILENAME_LENGTH = 255
BLOCK_SIZE = 512

class FileSystem:
    def __init__(self, device, num_descriptors):
        self.device = device
        self.root_dir = {}
        self.file_descriptors = [None] * num_descriptors
        self.open_files = [None] * MAX_OPEN_FILES
        self.seek_positions = [0] * MAX_OPEN_FILES

    def mkfs(self, num_descriptors):
        self.file_descriptors = [None] * num_descriptors
        self.root_dir = {}

    def stat(self, name):
        fd_index = self.root_dir.get(name)
        if fd_index is None:
            raise FileNotFoundError("Файл не знайдено")
        fd = self.file_descriptors[fd_index]
        return fd

    def ls(self):
        return self.root_dir

    def create(self, name):
        if len(name) > MAX_FILENAME_LENGTH:
            raise ValueError("Занадто довге ім'я файлу")
        if name in self.root_dir:
            raise ValueError("Файл вже існує")

        fd_index = self._allocate_file_descriptor('regular')
        self.root_dir[name] = fd_index
        return fd_index

    def open(self, name):
        fd_index = self.root_dir.get(name)
        if fd_index is None:
            raise FileNotFoundError("Файл не знайдено")
        for i in range(MAX_OPEN_FILES):
            if self.open_files[i] is None:
                self.open_files[i] = fd_index
                self.seek_positions[i] = 0
                return i
        raise RuntimeError("Немає вільних дескрипторів файлів")

    def close(self, fd):
        if self.open_files[fd] is None:
            raise ValueError("Дескриптор файлу не відкрито")
        self.open_files[fd] = None
        self.seek_positions[fd] = 0

    def seek(self, fd, offset):
        if self.open_files[fd] is None:
            raise ValueError("Дескриптор файлу не відкрито")
        self.seek_positions[fd] = offset

    def read(self, fd, size):
        if self.open_files[fd] is None:
            raise ValueError("Дескриптор файлу не відкрито")
        fd_index = self.open_files[fd]
        position = self.seek_positions[fd]
        file_descriptor = self.file_descriptors[fd_index]

        data = bytearray()
        remaining = size
        while remaining > 0 and position < file_descriptor.size:
            block_index = position // BLOCK_SIZE
            block_offset = position % BLOCK_SIZE
            block_num = file_descriptor.block_map[block_index]
            block_data = self.device.read_block(block_num)

            chunk = min(BLOCK_SIZE - block_offset, remaining)
            data.extend(block_data[block_offset:block_offset + chunk])
            position += chunk
            remaining -= chunk

        self.seek_positions[fd] = position
        return data.decode()

    def write(self, fd, data):
        if self.open_files[fd] is None:
            raise ValueError("Дескриптор файлу не відкрито")
        fd_index = self.open_files[fd]
        position = self.seek_positions[fd]
        file_descriptor = self.file_descriptors[fd_index]

        remaining = len(data)
        written = 0
        while remaining > 0:
            block_index = position // BLOCK_SIZE
            block_offset = position % BLOCK_SIZE
            if block_index >= len(file_descriptor.block_map):
                block_num = self.device.allocate_block()
                file_descriptor.block_map.append(block_num)
            else:
                block_num = file_descriptor.block_map[block_index]

            block_data = self.device.read_block(block_num)
            chunk = min(BLOCK_SIZE - block_offset, remaining)
            block_data[block_offset:block_offset + chunk] = data[written:written + chunk]
            self.device.write_block(block_num, block_data)

            position += chunk
            written += chunk
            remaining -= chunk

        file_descriptor.size = max(file_descriptor.size, position)
        self.seek_positions[fd] = position

    def link(self, name1, name2):
        fd_index = self.root_dir.get(name1)
        if fd_index is None:
            raise FileNotFoundError("Файл не знайдено")
        if name2 in self.root_dir:
            raise ValueError("Файл вже існує")
        self.root_dir[name2] = fd_index
        self.file_descriptors[fd_index].hard_links += 1

    def unlink(self, name):
        fd_index = self.root_dir.pop(name, None)
        if fd_index is None:
            raise FileNotFoundError("Файл не знайдено")
        fd = self.file_descriptors[fd_index]
        fd.hard_links -= 1
        if fd.hard_links == 0 and not any(fd_index in self.open_files for fd_index in self.open_files):
            for block_num in fd.block_map:
                self.device.free_block(block_num)
            self.file_descriptors[fd_index] = None

    def truncate(self, name, size):
        fd_index = self.root_dir.get(name)
        if fd_index is None:
            raise FileNotFoundError("File not found")
        file_descriptor = self.file_descriptors[fd_index]
        current_size = file_descriptor.size
        if size < current_size:
            while file_descriptor.block_map and size < (len(file_descriptor.block_map) - 1) * BLOCK_SIZE:
                block_num = file_descriptor.block_map.pop()
                self.device.free_block(block_num)

            if file_descriptor.block_map:
                last_block_num = file_descriptor.block_map[-1]
                last_block_data = self.device.read_block(last_block_num)
                truncate_offset = size % BLOCK_SIZE
                if truncate_offset == 0 and size > 0:
                    truncate_offset = BLOCK_SIZE
                for i in range(truncate_offset, BLOCK_SIZE):
                    last_block_data[i] = 0
                self.device.write_block(last_block_num, last_block_data)

        elif size > current_size:
            num_new_blocks = (size + BLOCK_SIZE - 1) // BLOCK_SIZE - (current_size + BLOCK_SIZE - 1) // BLOCK_SIZE
            for _ in range(num_new_blocks):
                block_num = self.device.allocate_block()
                file_descriptor.block_map.append(block_num)
            if current_size % BLOCK_SIZE != 0:
                last_block_num = file_descriptor.block_map[current_size // BLOCK_SIZE]
                last_block_data = self.device.read_block(last_block_num)
                start_offset = current_size % BLOCK_SIZE
                for i in range(start_offset, BLOCK_SIZE):
                    last_block_data[i] = 0
                self.device.write_block(last_block_num, last_block_data)
            if num_new_blocks > 0:
                for i in range(len(file_descriptor.block_map) - num_new_blocks, len(file_descriptor.block_map)):
                    block_num = file_descriptor.block_map[i]
                    self.device.write_block(block_num, bytearray(BLOCK_SIZE))

        file_descriptor.size = size

    def _allocate_file_descriptor(self, file_type):
        for i in range(len(self.file_descriptors)):
            if self.file_descriptors[i] is None:
                self.file_descriptors[i] = FileDescriptor(file_type)
                return i
        raise RuntimeError("Немає вільних дескрипторів файлів")