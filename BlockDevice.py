BLOCK_SIZE = 512

class BlockDevice:
    def __init__(self, size):
        self.size = size
        self.blocks = [bytearray(BLOCK_SIZE) for _ in range(size // BLOCK_SIZE)]
        self.bitmap = [False] * len(self.blocks)

    def read_block(self, block_num):
        return self.blocks[block_num]

    def write_block(self, block_num, data):
        if len(data) > BLOCK_SIZE:
            raise ValueError("Дані перевищують розмір блоку")
        self.blocks[block_num][:] = data
        self.bitmap[block_num] = True

    def allocate_block(self):
        for i, used in enumerate(self.bitmap):
            if not used:
                self.bitmap[i] = True
                return i
        raise RuntimeError("Немає вільних блоків")

    def free_block(self, block_num):
        self.bitmap[block_num] = False
        self.blocks[block_num] = bytearray(BLOCK_SIZE)

