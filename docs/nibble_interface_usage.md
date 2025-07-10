# 2-Cycle 8-bit Serial Interface Usage Guide

## Overview

The MAC peripheral now uses a **2-cycle 8-bit serial interface** that enables complete 16-bit result input/output through TinyTapeout's 8-bit I/O ports.

## Interface Design

### **Input Protocol (2 cycles)**

**Cycle 1: Data A + Control Signal**

- `ui_in[7:0]` = 8-bit Data A
- `uio_in[0]` = clear_and_mult control signal (0=accumulate mode, 1=clear mode)
- `uio_in[1]` = enable = 1 (enable interface)

**Cycle 2: Data B**

- `ui_in[7:0]` = 8-bit Data B
- `uio_in[1]` = enable = 1 (enable interface)
- `uio_in[0]` = don't care (control signal only valid in cycle 1)

### **Output Protocol (2 cycles)**

**Cycle 1: Result High 8 bits + overflow**

- `uo_out[7:0]` = Result high 8 bits (bits 15:8)
- `uio_out[0]` = overflow flag
- `uio_out[1]` = data_ready signal

**Cycle 2: Result Low 8 bits**

- `uo_out[7:0]` = Result low 8 bits (bits 7:0)
- `uio_out[0]` = overflow flag (maintained)
- `uio_out[1]` = data_ready signal

## Usage Examples

### Basic Multiplication Operation

```c
// Calculate 5 * 6 = 30
// Input protocol
cycle1: ui_in = 0x05, uio_in = 0x03  // Data A=5, clear=1, enable=1
cycle2: ui_in = 0x06, uio_in = 0x02  // Data B=6, enable=1
cycle3: uio_in = 0x00                // Disable interface

// Wait for MAC pipeline processing (~6 clock cycles)

// Output protocol - Read 30 = 0x001E
cycle_n:   uo_out = 0x00  // High 8 bits
cycle_n+1: uo_out = 0x1E  // Low 8 bits
// Reconstruct result: (0x00 << 8) | 0x1E = 0x001E = 30
```

### Accumulation Operation

```c
// Step 1: 10 * 10 = 100 (clear mode)
cycle1: ui_in = 0x0A, uio_in = 0x03  // Data A=10, clear=1, enable=1
cycle2: ui_in = 0x0A, uio_in = 0x02  // Data B=10, enable=1

// Step 2: +5 * 5 = +25 -> 125 (accumulate mode)
cycle1: ui_in = 0x05, uio_in = 0x02  // Data A=5, clear=0, enable=1
cycle2: ui_in = 0x05, uio_in = 0x02  // Data B=5, enable=1

// Result: 125 = 0x007D
// Output: 0x00 (high), 0x7D (low)
```

### Overflow Detection

```c
// Large multiplication: 255 * 255 = 65025
cycle1: ui_in = 0xFF, uio_in = 0x03  // Data A=255, clear=1, enable=1
cycle2: ui_in = 0xFF, uio_in = 0x02  // Data B=255, enable=1

// Result: 65025 = 0xFE01
// Output: 0xFE (high), 0x01 (low), overflow=0

// Continue accumulating to trigger overflow: +200 * 200 = +40000
cycle1: ui_in = 0xC8, uio_in = 0x02  // Data A=200, clear=0, enable=1
cycle2: ui_in = 0xC8, uio_in = 0x02  // Data B=200, enable=1

// Total: 65025 + 40000 = 105025 > 65535 (16-bit maximum)
// Output: overflow=1
```

## Timing Requirements

1. **Input Timing**: Each enable cycle must be held for at least 1 clock cycle
2. **MAC Pipeline Delay**: ~4-6 clock cycles from input completion to result availability
3. **Output Cycling**: Result automatically alternates between high/low 8 bits every clock cycle

## Interface Mapping

| Signal      | Pin               | Direction | Description                                       |
| ----------- | ----------------- | --------- | ------------------------------------------------- |
| ui_in[7:0]  | Dedicated Input   | Input     | 8-bit data input (Cycle 1=Data A, Cycle 2=Data B) |
| uo_out[7:0] | Dedicated Output  | Output    | 8-bit data output (alternates high/low 8 bits)    |
| uio_in[0]   | Bidirectional I/O | Input     | clear_and_mult control (valid only in cycle 1)    |
| uio_in[1]   | Bidirectional I/O | Input     | enable signal                                     |
| uio_out[0]  | Bidirectional I/O | Output    | overflow flag                                     |
| uio_out[1]  | Bidirectional I/O | Output    | data_ready signal                                 |

## Pipeline Architecture

The new 2-cycle interface maintains full compatibility with the existing MAC pipeline:

1. **Input Register Stage**: Store and assemble 8-bit input data
2. **Pipeline Register Stage**: Data transfer and synchronization
3. **Multiplier Stage**: 8×8→16-bit multiplication
4. **Accumulator Stage**: 17-bit accumulation and overflow detection

## Advantages

- ✅ **Complete 16-bit Access**: Full 16-bit result accessible through 2 cycles
- ✅ **Maintains Compatibility**: Fully compatible with existing MAC pipeline
- ✅ **Simplified Interface**: Uses standard 8-bit I/O, no complex nibble protocol
- ✅ **Automatic Cycling**: Output automatically alternates between high/low bytes
- ✅ **Overflow Detection**: Maintains complete overflow detection functionality
- ✅ **Pipeline Efficiency**: Preserves original 4-cycle pipeline performance

## Test Coverage

The interface has been thoroughly tested with the following test cases:

1. **Basic Multiplication**: 5 × 6 = 30 ✅
2. **Result Readback**: 15 × 17 = 255 ✅
3. **Accumulation**: 10 × 10 + 5 × 5 = 125 ✅
4. **Overflow Detection**: 255 × 255 + 200 × 200 (triggers overflow) ✅
5. **Timing**: Back-to-back operations ✅
6. **Output Protocol**: 2-cycle output cycling verification ✅

This new design implements the true 2-cycle input/output protocol you requested while maintaining all MAC core functionality and performance characteristics.
