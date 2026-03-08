.data
array:  .word 6,11,3,1,2
size:   .word 5

.text
main:

    # --- Initialization ---
    la    x10, array        # x10 = base address of array
    lw    x11, size         # x11 = N

    addi  x5, x0, 0         # i = 0
    addi  x7, x11, -1       # limit = N - 1

outer_loop:

    # if i >= limit -> exit
    bge   x5, x7, exit

    addi  x6, x0, 0         # j = 0

inner_loop:

    # limit for inner loop = (N - 1) - i
    sub   x20, x7, x5
    bge   x6, x20, next_i

    # --- Calculate address of arr[j] ---
    slli  x21, x6, 2        # offset = j * 4
    add   x22, x10, x21     # x22 = &arr[j]

    # --- Load arr[j] and arr[j+1] ---
    lw    x23, 0(x22)
    lw    x24, 4(x22)

    # --- Compare ---
    ble   x23, x24, no_swap

    # --- Swap ---
    sw    x24, 0(x22)
    sw    x23, 4(x22)

no_swap:

    addi  x6, x6, 1         # j++

    # jump inner_loop
    jal   x0, inner_loop


next_i:

    addi  x5, x5, 1         # i++

    # jump outer_loop
    jal   x0, outer_loop


exit:

    # infinite loop (program end)
    jal x0 , exit