import os

dirs = '/home/artem/Documents/эпикризы_rename'
num = 0

for dir in os.listdir(dirs):
    path_dir = os.path.join(dirs, dir)
    print(f'----------\n {path_dir}\n --------------')

    i = 0
    for i, file in enumerate(sorted(os.listdir(path_dir))):
        print(file)
        # os.rename(os.path.join(path_dir, file), os.path.join(path_dir, f'{dir}_{i}'))
        num += 1

print(num)