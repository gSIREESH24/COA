addi x1,x0,10
addi x2,x0,20

add x3,x1,x2
sub x4,x2,x1

addi x5,x0,10

sw x3,0(x5)
lw x6,0(x5)

bne x6,x4,8

addi x7,x0,1
addi x7,x0,2