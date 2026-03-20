# -*- coding: UTF-8 -*-
import readline
from pypinyin import pinyin, lazy_pinyin, Style

with open('input.txt', 'r') as f:
    lines = f.readlines()

    with open('output.txt', 'w') as out_file:
        for line in lines:
            line = line.strip()
            line_array1=pinyin(line, style=Style.NORMAL, strict=False)
            line_str1 = ""

            for tempvar in line_array1:
                temp_str1 = "".join(tempvar)
                line_str1 = line_str1 + temp_str1

            print(line_str1)
            out_file.write(line_str1.strip() + '\n')
