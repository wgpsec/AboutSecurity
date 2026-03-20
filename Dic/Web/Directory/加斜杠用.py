# -*- coding: UTF-8 -*-

with open('input.txt', 'r') as f:
    lines = f.readlines()

    with open('output.txt', 'w') as out_file:
        for line in lines:
            line = line.strip()
            if not line.startswith('/'):
                line = '/' + line
            print(line)
            out_file.write(line.strip() + '\n')
