# Program: Sum from 1 to N
# N = 5

addi x1, x0, 5      # x1 = N = 5
addi x2, x0, 1      # x2 = i = 1
addi x3, x0, 0      # x3 = sum = 0

loop:
add  x3, x3, x2     # sum = sum + i
addi x2, x2, 1      # i = i + 1

sub  x4, x2, x1     # x4 = i - N
bne  x4, x0, loop   # if i != N → continue loop

jal  x5, end        # jump to end (simulate function return)

end:
addi x6, x3, 0      # copy sum to x6 (final result register)