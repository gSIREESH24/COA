.data
array:  .word 1,2,3,4,5
size:   .word 5

.text
main:

    la   x10, array
    lw   x11, size

    addi x5, x0, 0      # i = 0
    addi x12, x0, 0     # sum = 0

loop:

    bge  x5, x11, end

    slli x6, x5, 2
    add  x7, x10, x6

    lw   x8, 0(x7)

    add  x12, x12, x8

    addi x5, x5, 1

    jal  x0, loop

end:
    jal x0, end