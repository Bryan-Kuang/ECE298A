# 4-bit Serial Interface Usage Guide

## Overview

The 8-bit MAC peripheral features a **4-bit serial interface** using **4 independent single-direction 4-bit ports** that allows complete 8-bit data transmission and 16-bit result readback using a 2-cycle protocol. This design efficiently uses TinyTapeout's limited I/O pins while maintaining full MAC capabilities.

## Interface Design

### Port Assignment

| Port Group    | Direction | Function                     | Description                            |
| ------------- | --------- | ---------------------------- | -------------------------------------- |
| `ui_in[3:0]`  | Input     | Data_A Nibble Port           | 4-bit input port for Data_A            |
| `ui_in[7:4]`  | Input     | Data_B Nibble Port           | 4-bit input port for Data_B            |
| `uo_out[3:0]` | Output    | Result Low Byte Nibble Port  | 4-bit output port for result[7:0]      |
| `uo_out[7:4]` | Output    | Result High Byte Nibble Port | 4-bit output port for result[15:8]     |
| `uio_in[0]`   | Input     | Clear_and_Mult               | Control signal (0=accumulate, 1=clear) |
| `uio_in[1]`   | Input     | Enable                       | Interface enable signal                |
| `uio_out[0]`  | Output    | Overflow                     | Overflow flag output                   |
| `uio_out[1]`  | Output    | Data_Ready                   | Ready for new data flag                |

### Data Transmission Protocol

The interface uses a **2-cycle protocol** for each operation:

**Input Protocol (2 cycles to send 8-bit × 8-bit data):**

1. **Cycle 1**: Send lower nibbles of Data_A and Data_B
2. **Cycle 2**: Send upper nibbles of Data_A and Data_B

**Output Protocol (2 cycles to read 16-bit result):**

1. **Cycle 1**: Read lower nibbles of result low and high bytes
2. **Cycle 2**: Read upper nibbles of result low and high bytes

### Timing Diagram

```
Clock:         ___┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐_┌─┐___
Enable:        ____┌───┐_____________________┌───┐___
Data_A[3:0]:   ──┤ 5 ├─────────────────────┤ 3 ├───  (Input Port 1)
Data_B[3:0]:   ──┤ 6 ├─────────────────────┤ 4 ├───  (Input Port 2)
Clear_Mult:    ──┤ 1 ├─────────────────────┤ 0 ├───
Result_Low[3:0]:──┤15 ├─────────────────────┤ 4 ├───  (Output Port 1)
Result_High[3:0]:─┤ 0 ├─────────────────────┤ 1 ├───  (Output Port 2)
                  │   │                     │   │
               Cycle 1                   Cycle 1
           Send: A=0x05, B=0x06      Send: A=0x03, B=0x04
           Read: Result=0x001E       Read: Result=0x000C
           (5*6=30, low nibbles)     (3*4=12, low nibbles)
```

## Usage Examples

### Example 1: Basic Multiplication (5 × 6 = 30)

```verilog
// Cycle 1: Send lower nibbles
ui_in[3:0] = 4'd5;    // Data_A lower nibble (Input Port 1)
ui_in[7:4] = 4'd6;    // Data_B lower nibble (Input Port 2)
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

// Read result over 2 cycles
// Cycle 1: Lower nibbles
result_low_nibble = uo_out[3:0];   // Low byte lower nibble (Output Port 1)
result_high_nibble = uo_out[7:4];  // High byte lower nibble (Output Port 2)
@(posedge clk);

// Cycle 2: Upper nibbles
result_low_upper = uo_out[3:0];    // Low byte upper nibble
result_high_upper = uo_out[7:4];   // High byte upper nibble
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

Results are output via **4-bit Output Ports** and need to be assembled over 2 cycles:

```verilog
// Read result from 4-bit output ports over 2 cycles
// Cycle 1: Lower nibbles
result_low[3:0] = uo_out[3:0];     // Low byte lower nibble (Output Port 1)
result_high[3:0] = uo_out[7:4];    // High byte lower nibble (Output Port 2)
overflow = uio_out[0];

// Cycle 2: Upper nibbles
result_low[7:4] = uo_out[3:0];     // Low byte upper nibble (Output Port 1)
result_high[7:4] = uo_out[7:4];    // High byte upper nibble (Output Port 2)

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

1. **I/O Efficiency**: Uses only 4 dedicated 4-bit ports for complete data transfer
2. **Clear Interface**: 4 independent single-direction ports with well-defined functions
3. **Expandability**: Efficient use of TinyTapeout's limited I/O pins
4. **Compatibility**: Maintains full MAC functionality with complete 16-bit result access
5. **Flexibility**: Allows future expansion with additional control signals

## Limitations

1. **Throughput**: 2× slower data input compared to parallel interface
2. **Complexity**: Requires 2-cycle protocol management
3. **Latency**: Additional cycle for data assembly

## Testing

See `test/test_mac_nibble.py` for comprehensive test examples and `test/tb_mac_nibble.v` for Verilog simulation examples.
