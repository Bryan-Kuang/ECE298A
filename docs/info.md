<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project implements an 8×8→16-bit Multiply-Accumulate (MAC) peripheral with overflow detection, designed for digital signal processing applications using a 4-bit nibble serial interface.

### Architecture Overview

The MAC peripheral consists of three main components:

1. **8×8 Multiplier (TC_Mul.v)**: Performs unsigned 8-bit × 8-bit multiplication, producing a 16-bit result
2. **17-bit Accumulator**: Stores and accumulates multiplication results with overflow detection
3. **3-Stage Pipeline**: Ensures stable operation with 4-cycle latency
4. **4-bit Nibble Serial Interface**: Enables data transmission using 4 independent 4-bit ports

### Serial Interface Design

The design uses **4 independent single-direction 4-bit serial ports**:

**Input Ports (2 × 4-bit):**

- `ui_in[3:0]`: Data_A nibble port
- `ui_in[7:4]`: Data_B nibble port

**Output Ports (2 × 4-bit):**

- `uo_out[3:0]`: Result low byte nibble port
- `uo_out[7:4]`: Result high byte nibble port

### Operation Modes

- **Clear Mode** (`Clear_and_Mult = 1`): Replaces accumulator value with new multiplication result
- **Accumulate Mode** (`Clear_and_Mult = 0`): Adds new multiplication result to existing accumulator value

### Pipeline Stages

1. **Stage 1**: Input capture and validation
2. **Stage 2**: 8×8 multiplication using TC_Mul component
3. **Stage 3**: Accumulation and overflow detection

### TinyTapeout Interface

**Input Pins:**

- `ui_in[3:0]`: Data_A nibble (4-bit)
- `ui_in[7:4]`: Data_B nibble (4-bit)
- `uio_in[0]`: Clear_and_Mult control signal
- `uio_in[1]`: Enable signal for nibble interface

**Output Pins:**

- `uo_out[3:0]`: Result low byte nibble (4-bit)
- `uo_out[7:4]`: Result high byte nibble (4-bit)
- `uio_out[0]`: Overflow flag
- `uio_out[1]`: Data ready flag

### Data Transmission Protocol

The interface uses a 2-cycle protocol for each operation:

**Input (2 cycles to send 8-bit × 8-bit data):**

1. **Cycle 1**: Send lower nibbles of Data_A and Data_B
2. **Cycle 2**: Send upper nibbles of Data_A and Data_B

**Output (2 cycles to read 16-bit result):**

1. **Cycle 1**: Read lower nibbles of result low and high bytes
2. **Cycle 2**: Read upper nibbles of result low and high bytes

### Key Features

- **50MHz Operation**: Optimized for TinyTapeout's 50MHz clock
- **Overflow Detection**: 17-bit internal accumulator detects 16-bit overflow
- **Low Latency**: 4-cycle pipeline provides deterministic timing
- **Compact Design**: Fits in single 1×1 TinyTapeout tile
- **4-bit Serial Interface**: Efficient use of limited I/O pins

## How to test

### Basic Operation Test

1. **Reset the design**: Assert reset for several clock cycles
2. **Set inputs** (2-cycle protocol):
   - **Cycle 1**: `ui_in[3:0] = 0x5` (Data_A lower), `ui_in[7:4] = 0x3` (Data_B lower), `uio_in[1] = 1` (Enable), `uio_in[0] = 1` (Clear mode)
   - **Cycle 2**: `ui_in[3:0] = 0x0` (Data_A upper), `ui_in[7:4] = 0x0` (Data_B upper), `uio_in[1] = 1` (Enable), `uio_in[0] = 1` (Clear mode)
3. **Wait 4 cycles**: Allow pipeline to complete
4. **Read result** (2-cycle protocol):
   - **Cycle 1**: `uo_out[3:0] = 0xF` (result low byte lower nibble), `uo_out[7:4] = 0x0` (result high byte lower nibble)
   - **Cycle 2**: `uo_out[3:0] = 0x0` (result low byte upper nibble), `uo_out[7:4] = 0x0` (result high byte upper nibble)
   - Expected: 5×3 = 15 (0x000F)

### Accumulation Test

1. **Perform initial multiplication**: 10×10 = 100 (Clear mode)
2. **Add second multiplication**: +5×5 = 25 (Accumulate mode)
3. **Verify result**: Total should be 125

### Overflow Test

1. **Set large values**: 255×255 = 65025 (Clear mode)
2. **Add more**: +200×200 = 40000 (Accumulate mode)
3. **Check overflow**: `uio_out[0]` should be 1, indicating overflow

### Test Sequence Example

```
Clock 0-3:   Reset active
Clock 4-5:   Send A=10, B=10, Clear=1 (2 cycles)
Clock 10:    Result = 100 (10×10) available after pipeline
Clock 11-12: Send A=5, B=5, Clear=0 (2 cycles)
Clock 17:    Result = 125 (100+25) available after pipeline
```

## External hardware

No external hardware is required. This is a purely digital design that operates with:

- **Clock**: 50MHz system clock from TinyTapeout
- **Reset**: Active-low reset signal
- **Digital I/O**: Standard TinyTapeout pin interface

The design can be tested using:

- Logic analyzer to monitor input/output signals
- Oscilloscope to verify timing relationships
- TinyTapeout demo board for interactive testing
