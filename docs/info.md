## How it works

Tiny1 is a 1-bit CPU. A host (for example the RP2040 on the Tiny Tapeout demo board) acts as the program counter and memory: every clock with GO high it presents one instruction byte on `ui_in` and one data bit on `uio[0]` (HX), and the chip executes it.

State: result bit RR, carry CY, 15 one-bit registers R0..R14, an 8-bit counter CNT, an 8-bit threshold THR and a 16-bit LFSR (taps 16,15,13,4, resets to 0xACE1).

Instruction byte: `ui_in[7:4]` = opcode, `ui_in[3:0]` = operand. In the table, `x` means register R(operand) for operands 0..14 and the host bit HX for operand 15.

| Op | Name | Effect |
|----|------|--------|
| 0 | NOP | nothing |
| 1 | LD | RR = x |
| 2 | LDN | RR = ~x |
| 3 | AND | RR = RR & x |
| 4 | OR | RR = RR \| x |
| 5 | XOR | RR = RR ^ x |
| 6 | XNOR | RR = ~(RR ^ x) |
| 7 | ADD | RR = RR ^ x ^ CY, CY = carry out |
| 8 | SUB | same as ADD with ~x (set CY = 1 first; CY = 1 afterwards means no borrow) |
| 9 | ST | operand < 15: R(operand) = RR. Operand 15: DO = RR and WR pulses for one clock |
| A | CC | operand[1:0]: 0 CY=0, 1 CY=1, 2 CY=RR, 3 RR=CY |
| B | NEUR | if RR == x then CNT = CNT + 1 (XNOR neuron: counts matching bits) |
| C | TH | operand[1:0]: 0 RR = (CNT >= THR), 1 CNT = 0, 2 THR = {RR, THR[7:1]} (serial load, LSB first), 3 CNT = CNT + RR |
| D | FN | RR = operand[{RR,HX}]: the operand is a truth table, so all 16 two-input logic functions are available (9 XNOR, 7 NAND, 1 NOR, 6 XOR, 8 AND, 14 OR) |
| E | ANDN | RR = RR & ~x |
| F | RND | operand[1:0]: 0 step LFSR and RR = new bit, 1 shift RR into the LFSR (seed MSB first) |

Numbers of any width are processed one bit at a time, least significant bit first. Example, 8-bit add: `CC 0`, then for each bit `LD 15` (HX = a[i]), `ADD 15` (HX = b[i]), `ST 15` (read DO when WR pulses).

Outputs: `uo_out` is CNT. `uio[2]` RR, `uio[3]` CY, `uio[4]` DO, `uio[5]` WR, `uio[6]` GE (CNT >= THR). Inputs: `uio[0]` HX, `uio[1]` GO (0 = hold).

## How to test

Hold `rst_n` low, then release it. For each instruction set `ui_in` and HX, set GO high for one clock, then read the outputs. A Python model and test vectors are in the project repository.

## External hardware

A microcontroller (such as the RP2040 on the demo board) that supplies instructions and data bits and stores results.
