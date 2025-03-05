# Problem: sử dụng python để in ra ký tự * theo hình kim tự tháp, với số dòng là 7  

rows = 7
for i in range(rows):
    print(' ' * (rows - i - 1) + '*' * (2 * i + 1))