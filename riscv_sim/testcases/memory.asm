addi x1,x0,4
addi x2,x0,300
addi x3,x0,12

sw x2,0(x1)
sw x3,4(x1)

lw x4,0(x1)
lw x5,4(x1)

add x6,x4,x5