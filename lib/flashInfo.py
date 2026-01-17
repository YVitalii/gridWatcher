import os

# Отримуємо статистику файлової системи
stat = os.statvfs('/')

block_size = stat[0]
total_blocks = stat[2]
free_blocks = stat[3]

total_size = (block_size * total_blocks) / 1024
free_size = (block_size * free_blocks) / 1024

print(f"[Flash]::Free space: {free_size:.2f} kB ({free_size/total_size*100:.1f}%)")