<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project implements an 8×8→16-bit Multiply-Accumulate (MAC) peripheral with overflow detection, designed for digital signal processing applications.

### Architecture Overview

The MAC peripheral consists of three main components:

1. **8×8 Multiplier (TC_Mul.v)**: Performs unsigned 8-bit × 8-bit multiplication, producing a 16-bit result
2. **17-bit Accumulator**: Stores and accumulates multiplication results with overflow detection
3. **3-Stage Pipeline**: Ensures stable operation with 4-cycle latency

### Operation Modes

- **Clear Mode** (`Clear_and_Mult = 1`): Replaces accumulator value with new multiplication result
- **Accumulate Mode** (`Clear_and_Mult = 0`): Adds new multiplication result to existing accumulator value

### Pipeline Stages

1. **Stage 1**: Input capture and validation
2. **Stage 2**: 8×8 multiplication using TC_Mul component
3. **Stage 3**: Accumulation and overflow detection

### TinyTapeout Interface

**Input Pins:**

- `ui_in[7:0]`: Data_A (8-bit multiplicand)
- `uio_in[6:0]`: Data_B (7-bit multiplier, MSB=0)
- `uio_in[7]`: Clear_and_Mult control signal

**Output Pins:**

- `uo_out[7:0]`: Result bits [7:0] (lower 8 bits)
- `uio_out[6:0]`: Result bits [14:8] (upper 7 bits)
- `uio_out[7]`: Overflow flag

### Key Features

- **50MHz Operation**: Optimized for TinyTapeout's 50MHz clock
- **Overflow Detection**: 17-bit internal accumulator detects 16-bit overflow
- **Low Latency**: 4-cycle pipeline provides deterministic timing
- **Compact Design**: Fits in single 1×1 TinyTapeout tile

## How to test

### Basic Operation Test

1. **Reset the design**: Assert reset for several clock cycles
2. **Set inputs**:
   - `ui_in[7:0] = 0x05` (Data_A = 5)
   - `uio_in[6:0] = 0x03` (Data_B = 3)
   - `uio_in[7] = 1` (Clear mode)
3. **Wait 4 cycles**: Allow pipeline to complete
4. **Read result**:
   - Expected: `uo_out = 0x0F`, `uio_out[6:0] = 0x00` (5×3 = 15)

### Accumulation Test

1. **Perform initial multiplication**: 10×10 = 100 (Clear mode)
2. **Add second multiplication**: +5×5 = 25 (Accumulate mode)
3. **Verify result**: Total should be 125

### Overflow Test

1. **Set large values**: 255×255 = 65025 (Clear mode)
2. **Add more**: +200×200 = 40000 (Accumulate mode)
3. **Check overflow**: `uio_out[7]` should be 1, indicating overflow

### Test Sequence Example

```
Clock 0-3:   Reset active
Clock 4:     Set A=10, B=10, Clear=1
Clock 8:     Result = 100 (10×10)
Clock 9:     Set A=5, B=5, Clear=0
Clock 13:    Result = 125 (100+25)
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
