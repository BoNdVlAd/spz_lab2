from BlockDevice import *
from FileSystem import *

BLOCK_SIZE = 512
MAX_FILE_DESCRIPTORS = 100
MAX_FILENAME_LENGTH = 255
MAX_OPEN_FILES = 100

def main():
    device = BlockDevice(10 * 1024 * 1024)

    print("Ініціалізація файлової системи")
    fs = FileSystem(device, MAX_FILE_DESCRIPTORS)
    fs.mkfs(MAX_FILE_DESCRIPTORS)

    print('-------------------------------------------------------------------------------------------------')

    print("Створення файлу example_file.txt, запис тексту, читання з файлу, закриття файлу:")
    fs.create("example_file.txt")
    fd = fs.open("example_file.txt")
    fs.write(fd, b"Hello, World!")
    fs.seek(fd, 0)
    print(fs.read(fd, 13))
    fs.close(fd)

    print('-------------------------------------------------------------------------------------------------')

    print('Відкриття файлу example_file.txt та читання інформації з нього:')
    fd = fs.open("example_file.txt")
    data = fs.read(fd, 13)
    fs.close(fd)
    print(data)

    print('-------------------------------------------------------------------------------------------------')

    print('Створення файлу file1.txt, створення посилання file2.txt на цей файл, вивід файлів в коревневому каталозі:')
    fs.create("file1.txt")
    fs.link("file1.txt", "file2.txt")
    print("Файли в кореневому каталозі:", fs.ls())

    print('-------------------------------------------------------------------------------------------------')

    print("Відкриття файлу file1.txt, запис тексту у файл, закриття файлу, вивід stat file.2.txt, читання file2.txt")
    fd = fs.open("file1.txt")
    fs.write(fd, b"Hello, my name is Vlad")
    fs.close(fd)

    print("File stat:", fs.stat("file2.txt").__dict__)
    print("Читання file2.txt за жорстким посиланням:")
    fd = fs.open("file1.txt")
    print(fs.read(fd, 22))
    fs.close(fd)

    print('-------------------------------------------------------------------------------------------------')

    print("Відкриття file2.txt, зменшення рощміру файлу до 8, вивід stat file2.txt, читання file1.txt:")
    fd = fs.open('file2.txt')
    fs.truncate("file2.txt", 8)
    print("File stat після зменшення розміру файлу(22 -> 8):", fs.stat("file2.txt").__dict__)
    fs.seek(fd, 0)
    print('file2.txt: ', fs.read(fd, 8))
    fs.close(fd)
    fd = fs.open('file1.txt')
    print('file1.txt: ', fs.read(fd, 22))

    print('-------------------------------------------------------------------------------------------------')

    print("Від'єднання посилання file2.txt:")
    fs.unlink("file2.txt")
    print("Файли у кореневому каталозі після від'єднання file2.txt:", fs.ls())

if __name__ == "__main__":
    main()


