.data
array:  .word 5, 4, 3, 2, 1    # The 5 elements to sort
size:   .word 5                # N = 5

.text
main:
    # --- Initialization ---
    addi  x10, x0, 1024      # x10 = Base address (where .data starts)
    addi  x11, x0, 5         # x11 = Number of elements (N)
    
    addi  x5, x0, 0          # i = 0
    addi  x7, x11, -1        # limit = N - 1

outer_loop:
    # if i >= limit, sort is complete
    bge   x5, x7, exit       
    addi  x6, x0, 0          # j = 0

inner_loop:
    # limit for inner loop: (N - 1) - i
    sub   x20, x7, x5        
    bge   x6, x20, next_i    # if j >= (N-1-i), go to next_i

    # --- Load elements ---
    slli  x21, x6, 2         # x21 = j * 4 (offset)
    add   x22, x10, x21      # x22 = &arr[j]
    lw    x23, 0(x22)        # x23 = arr[j]
    lw    x24, 4(x22)        # x24 = arr[j+1]

    # --- Compare and Swap ---
    # if arr[j] <= arr[j+1], skip the swap
    ble   x23, x24, no_swap  
    
    sw    x24, 0(x22)        # arr[j] = x24
    sw    x23, 4(x22)        # arr[j+1] = x23

no_swap:
    addi  x6, x6, 1          # j++
    
    # Unconditional jump to inner_loop
    # Using jal to x0 (discard link) for jump
    jal   x0, inner_loop

next_i:
    addi  x5, x5, 1          # i++
    
    # Unconditional jump to outer_loop
    jal   x0, outer_loop

exit:
    # Infinite loop to signal end of program
    jal   x0, exit