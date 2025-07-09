# Nibble Interface Usage Guide

## Overview

The 8-bit MAC peripheral now features a nibble-based serial interface that allows 8-bit data transmission using only 4-bit pins over 2 clock cycles. This design frees up I/O pins for additional functionality while maintaining full MAC capabilities.

## Interface Protocol

### Pin Assignment

| Pin Group     | Function           | Description                            |
| ------------- | ------------------ | -------------------------------------- |
| `ui_in[3:0]`  | Data_A Nibble      | 4-bit nibble for input A               |
| `ui_in[7:4]`  | Data_B Nibble      | 4-bit nibble for input B               |
| `uio_in[0]`   | Clear_and_Mult     | Control signal (0=accumulate, 1=clear) |
| `uio_in[1]`   | Enable             | Nibble interface enable                |
| `uo_out[3:0]` | Result_Low Nibble  | Lower nibble of result low byte        |
| `uo_out[7:4]` | Result_High Nibble | Lower nibble of result high byte       |
| `uio_out[0]`  | Overflow           | Overflow flag output                   |
| `uio_out[1]`  | Data_Ready         | Ready for new data flag                |

### Data Transmission Protocol

The interface uses a 2-cycle protocol for each 8-bit value:

1. **Cycle 1**: Transmit lower 4 bits (nibble) of Data_A and Data_B
2. **Cycle 2**: Transmit upper 4 bits (nibble) of Data_A and Data_B

### Timing Diagram

```
Clock:     ___┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐___
Enable:    ____┌───┐_____________________┌───┐___
Data_A[3:0]: ──┤ 5 ├─────────────────────┤ 3 ├───
Data_A[7:4]: ──┤ 0 ├─────────────────────┤ 0 ├───
Data_B[3:0]: ──┤ 6 ├─────────────────────┤ 4 ├───
Data_B[7:4]: ──┤ 0 ├─────────────────────┤ 0 ├───
Clear_Mult:  ──┤ 1 ├─────────────────────┤ 0 ├───
                │   │                     │   │
             Cycle 1                   Cycle 1
           (5*6=30)                   (3*4=12)
           Clear Mode              Accumulate Mode
```

## Usage Examples

### Example 1: Basic Multiplication (5 × 6 = 30)

```verilog
// Cycle 1: Send lower nibbles
ui_in[3:0] = 4'd5;    // Data_A lower nibble
ui_in[7:4] = 4'd6;    // Data_B lower nibble
uio_in[0] = 1'b1;     // Clear mode
uio_in[1] = 1'b1;     // Enable
@(posedge clk);

// Cycle 2: Send upper nibbles
ui_in[3:0] = 4'd0;    // Data_A upper nibble (5 = 0x05)
ui_in[7:4] = 4'd0;    // Data_B upper nibble (6 = 0x06)
uio_in[0] = 1'b1;     // Clear mode
uio_in[1] = 1'b1;     // Enable
@(posedge clk);

// Disable and wait for MAC pipeline (4-6 cycles)
uio_in[1] = 1'b0;
repeat(6) @(posedge clk);

// Result will be available on uo_out nibbles
```

### Example 2: Accumulation (Previous + 3 × 4)

```verilog
// Cycle 1: Send lower nibbles
ui_in[3:0] = 4'd3;    // Data_A lower nibble
ui_in[7:4] = 4'd4;    // Data_B lower nibble
uio_in[0] = 1'b0;     // Accumulate mode
uio_in[1] = 1'b1;     // Enable
@(posedge clk);

// Cycle 2: Send upper nibbles
ui_in[3:0] = 4'd0;    // Data_A upper nibble
ui_in[7:4] = 4'd0;    // Data_B upper nibble
uio_in[0] = 1'b0;     // Accumulate mode
uio_in[1] = 1'b1;     // Enable
@(posedge clk);

// Disable and wait
uio_in[1] = 1'b0;
repeat(6) @(posedge clk);
```

### Example 3: Large Values (255 × 127)

```verilog
// Cycle 1: Send lower nibbles
ui_in[3:0] = 4'hF;    // 255 lower (0xFF & 0xF = 0xF)
ui_in[7:4] = 4'hF;    // 127 lower (0x7F & 0xF = 0xF)
uio_in[0] = 1'b1;     // Clear mode
uio_in[1] = 1'b1;     // Enable
@(posedge clk);

// Cycle 2: Send upper nibbles
ui_in[3:0] = 4'hF;    // 255 upper (0xFF >> 4 = 0xF)
ui_in[7:4] = 4'h7;    // 127 upper (0x7F >> 4 = 0x7)
uio_in[0] = 1'b1;     // Clear mode
uio_in[1] = 1'b1;     // Enable
@(posedge clk);

// Disable and wait
uio_in[1] = 1'b0;
repeat(6) @(posedge clk);
```

## Reading Results

Results are output as nibbles that need to be assembled:

```verilog
// Read result nibbles over 2 cycles
// Cycle 1: Lower nibbles
result_low[3:0] = uo_out[3:0];     // Result low byte, lower nibble
result_high[3:0] = uo_out[7:4];    // Result high byte, lower nibble
overflow = uio_out[0];

// Cycle 2: Upper nibbles
result_low[7:4] = uo_out[3:0];     // Result low byte, upper nibble
result_high[7:4] = uo_out[7:4];    // Result high byte, upper nibble

// Assemble 16-bit result
final_result = {result_high, result_low};
```

## Control Signals

### Enable Signal (`uio_in[1]`)

- Must be high during both cycles of data transmission
- Set low between operations
- Controls the nibble interface state machine

### Clear_and_Mult Signal (`uio_in[0]`)

- `1`: Clear accumulator and set to multiplication result
- `0`: Add multiplication result to current accumulator value

### Data_Ready Signal (`uio_out[1]`)

- Indicates when the interface is ready for new data
- High when not in the middle of a 2-cycle transmission

### Overflow Signal (`uio_out[0]`)

- Set when accumulator result exceeds 16 bits
- Persistent until next clear operation

## Pipeline Timing

The MAC has a 4-cycle pipeline delay:

1. Input registers
2. Pipeline registers
3. Multiplication
4. Accumulation

After sending data via nibble interface, wait 4-6 clock cycles before reading results.

## Benefits

1. **I/O Efficiency**: Reduces required pins from 16 to 8 for data
2. **Expandability**: Frees up 8 I/O pins for additional features
3. **Compatibility**: Maintains full MAC functionality
4. **Flexibility**: Allows future expansion with signed arithmetic, DMA, etc.

## Limitations

1. **Throughput**: 2× slower data input compared to parallel interface
2. **Complexity**: Requires 2-cycle protocol management
3. **Latency**: Additional cycle for data assembly

## Testing

See `test/test_mac_nibble.py` for comprehensive test examples and `test/tb_mac_nibble.v` for Verilog simulation examples.
