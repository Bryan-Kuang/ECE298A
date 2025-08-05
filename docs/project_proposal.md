# MAC Peripheral Enhancement Proposal

## Overview

This project implements an 8×8→16‑bit Multiply–Accumulate (MAC) peripheral using the TinyTapeout platform. The core integrates a configurable multiplier, 17‑bit accumulator and a 2‑cycle 8‑bit serial interface that exposes the full 16‑bit result over TinyTapeout's limited I/O pins.

## Objectives

- Provide a compact MAC tile with overflow detection and optional signed arithmetic.

- Offer a simple 2‑cycle input/output protocol for easy host integration.

- Maintain full 50 MHz operation with deterministic 4‑cycle latency.

## Architecture

1. **Input Stage** – Captures two 8‑bit operands and control signals. A change detector triggers loading when data is stable.

1. **Pipeline Stage** – Registers inputs for timing closure and passes signed/unsigned mode to the multiplier.

1. **Multiplier** – Configurable 8×8 block producing a 16‑bit product.

1. **Accumulator** – 17‑bit adder with clear/accumulate modes and overflow flag.

1. **Serial Interface** – Handles 2‑cycle input and output sequencing, presenting the low and high bytes on alternate cycles.

## Block Diagram

![](https://files.manuscdn.com/user_upload_by_module/markdown/310419663031347111/zXbeUKkcmInOrsEt.png)

## Pin Usage

| Pin           | Direction | Function                                                               |
| ------------- | --------- | ---------------------------------------------------------------------- |
| `ui_in[7:0]`  | Input     | Data A (cycle 1) / Data B (cycle 2)                                    |
| `uio_in[0]`   | Input     | `clear_and_mult` (0 = accumulate, 1 = clear and output current result) |
| `uio_in[1]`   | Input     | Interface enable                                                       |
| `uio_in[2]`   | Input     | `signed_mode` (0 = unsigned, 1 = signed)                               |
| `uo_out[7:0]` | Output    | 16‑bit result, cycling low/high bytes every clock                      |
| `uio_out[0]`  | Output    | Overflow flag                                                          |
| `uio_out[1]`  | Output    | Data ready flag                                                        |

## Verification Plan

- **Basic Multiply**: Verify single multiplication using the 2‑cycle protocol.

- **Basic Interface Functionality**: Verify 2-cycle 8-bit serial interface protocol with basic multiplication operations.

- **Result Readback**: Verify complete 16-bit result transmission over 2 cycles using the serial interface.

- **Accumulation Mode**: Verify MAC accumulation functionality with clear and accumulate mode switching.

- **Overflow Detection**: Verify 17-bit accumulator overflow detection for both unsigned and signed operations.

- **Timing and Pipeline**: Verify pipeline timing and back-to-back operation handling.

- **Signed Multiplication**: Verify signed arithmetic operations including positive, negative, and mixed operand multiplication.

- **Signed Accumulation**: Verify signed accumulation with proper sign extension and arithmetic.

- **Signed Overflow Detection**: Verify signed overflow detection mechanism for 16-bit signed arithmetic.

- **Mode Switching**: Verify seamless switching between unsigned and signed arithmetic modes.

- **Clear Functionality**: Verify clear_and_mult control signal properly resets accumulator and outputs only current product.

- **Signed Clear Functionality**: Verify clear functionality works correctly in signed arithmetic mode.

- **Output Protocol**: Verify 16-bit result cycling between high and low 8-bit outputs over 2 cycles.

- **Signal Path Debug**: Verify signed_mode signal propagation through the entire pipeline from input to multiplier.

## CocoTB Test Result

## `4600.00ns INFO cocotb.regression test_clear_functionality_signed_mode passed`

### Test Summary Table

| Test Name                                            | Status | Sim Time (ns) | Real Time (s) | Ratio (ns/s) |
| ---------------------------------------------------- | ------ | ------------- | ------------- | ------------ |
| test_mac.test_2cycle_serial_interface_basic          | PASS   | 180.00        | 0.00          | 79055.38     |
| test_mac.test_2cycle_serial_result_readback          | PASS   | 190.00        | 0.00          | 260260.54    |
| test_mac.test_2cycle_serial_accumulation             | PASS   | 310.00        | 0.00          | 240694.97    |
| test_mac.test_2cycle_serial_overflow                 | PASS   | 310.00        | 0.00          | 265353.93    |
| test_mac.test_2cycle_serial_timing                   | PASS   | 310.00        | 0.00          | 196588.18    |
| test_mac.test_2cycle_output_protocol                 | PASS   | 290.00        | 0.00          | 256451.22    |
| test_mac.test_signed_basic_multiplication            | PASS   | 430.00        | 0.00          | 272316.28    |
| test_mac.test_signed_accumulation                    | PASS   | 430.00        | 0.00          | 281628.78    |
| test_mac.test_signed_overflow                        | PASS   | 430.00        | 0.00          | 261573.71    |
| test_mac.test_mixed_unsigned_signed_modes            | PASS   | 430.00        | 0.00          | 286641.88    |
| test_mac.test_debug_signed_mode                      | PASS   | 190.00        | 0.00          | 192445.73    |
| test_mac.test_clear_functionality_after_accumulation | PASS   | 670.00        | 0.00          | 273443.97    |
| test_mac.test_clear_functionality_signed_mode        | PASS   | 430.00        | 0.00          | 258092.55    |

---

**TESTS=13** &nbsp;&nbsp;&nbsp; **PASS=13** &nbsp;&nbsp;&nbsp; **FAIL=0** &nbsp;&nbsp;&nbsp; **SKIP=0**  
**Total Sim Time:** 4600.00 ns &nbsp;&nbsp;&nbsp; **Real Time:** 0.11 s &nbsp;&nbsp;&nbsp; **Ratio:** 42433.43 ns/s

---

# Project Commit Timeline

This timeline traces development from Bryan's first contribution onward. Some later tasks were picked up by Lingfeng as the project grew.Bryan initially built the core modules and overall architecture. Lingfeng later led debugging, documentation, and interface updates.

## Timeline

cec7bda (2025-05-13, Bryan) - Update info.yaml  
3022e21 (2025-05-13, Bryan) - Update project.v  
cc3fbbf (2025-05-13, Bryan) - Update info.yaml  
3ddf116 (2025-05-13, Lingfeng) - Update info.yaml  
53e3e03 (2025-05-13, Bryan) - Update info.yaml  
129ce41 (2025-05-13, Lingfeng) - Update project.v  
952016a (2025-05-19, Lingfeng) - feat(counter): add 8-bit counter module and integrate into project  
96405cc (2025-06-04, Bryan) - feat: add proposal into docs  
e8747eb (2025-06-06, Bryan) - refactor: remove outdated proposal and add new project proposal; update test cases for counter functionality  
3d8186b (2025-06-06, Lingfeng) - Add debug logging for load functionality test  
39e5e1c (2025-06-06, Bryan) - fix(test): improve timing for load effect in counter test  
5f7c8a5 (2025-06-06, Bryan) - Fix signal propagation timing in cocotb tests  
4d985bf (2025-06-06, Lingfeng) - Improve timing control using RisingEdge and longer signal stabilization  
655595b (2025-06-06, Bryan) - refactor(test): enhance counter test with improved structure and additional logging  
f4fdb6d (2025-06-11, Bryan) - fix: proposal update  
74388f1 (2025-06-11, Lingfeng) - fix: proposal update  
ecf90d3 (2025-06-11, Bryan) - fix: update project proposal document  
916ced1 (2025-06-11, Lingfeng) - fix: update project proposal document  
32872f0 (2025-06-11, Bryan) - fix: update project proposal document  
a43846f (2025-06-23, Bryan) - refactor: remove unused files and add simplified MAC module  
7a2e032 (2025-06-23, Lingfeng) - feat: bring back the tt*um*... doc  
2e3da50 (2025-06-23, Bryan) - feat: add configuration file for tt_um_ARandomNam_mac_peripheral
4e259b9 (2025-06-24, Bryan) - feat: enhance documentation and configuration for MAC peripheral  
d5158ef (2025-06-24, Lingfeng) - feat: update config.json with detailed comments and new parameters  
dcc679d (2025-06-24, Bryan) - feat: update testbench and Makefile for TinyTapeout integration  
f17d2fd (2025-06-24, Bryan) - feat: refactor MAC_simple module and introduce new components  
3c444f3 (2025-06-24, Lingfeng) - Fix TinyTapeout module naming and configuration  
6fd8dc9 (2025-06-24, Bryan) - Complete project file consistency check and fix  
a828d82 (2025-07-08, Bryan) - fix: comment changed to make it clearer  
40137d1 (2025-07-09, Lingfeng) - feat: add spi components for future feature expansion  
f5be0d9 (2025-07-09, Bryan) - fix: fixed the info docs error  
b846692 (2025-07-09, Lingfeng) - fix: update info.yaml for consistency and clarity  
a0ca84a (2025-07-09, Bryan) - fix: improve nibble_interface and suppress unused signal warnings  
edf5a06 (2025-07-10, Bryan) - refactor: implemented 4 bit serial input however the component does not give expected value yet  
f5bb0d9 (2025-07-10, Bryan) - refactor: the current mac can perform cycle input/output mac operation as expected but missing some extra features  
d5706ab (2025-07-10, Bryan) - fix: removed the unused signal  
2c49177 (2025-07-10, Lingfeng) - refactor: enhance nibble_interface for combined input/output handling  
71d56b3 (2025-07-10, Bryan) - feat: add test cases and update Makefile for tb_mac_simple  
2f99ba4 (2025-07-10, Bryan) - feat: add configurable multiplier and update interfaces for signed operations  
bbda052 (2025-07-10, Bryan) - fix: added missing source files path

## Timing Report

---

### Path 1

**Startpoint:** `rst_n` _(input port clocked by `clk`)_  
**Endpoint:** `accumulator/_546_` _(removal check against rising-edge clock `clk`)_  
**Path Group:** `asynchronous`  
**Path Type:** `min`

#### Delay Trace

| Delay (ns) | Time (ns) | Description                                              |
| ---------- | --------- | -------------------------------------------------------- |
| 0.00       | 0.00      | clock `clk` (rise edge)                                  |
| 0.00       | 0.00      | clock network delay (ideal)                              |
| 2.00       | 2.00 ↑    | input external delay                                     |
| 0.00       | 2.00 ↑    | `rst_n` (in)                                             |
| 2.05       | 4.05 ↓    | `_3_/Y` (`sky130_fd_sc_hd__clkinv_1`)                    |
| 0.33       | 4.37 ↑    | `accumulator/_407_/Y` (`sky130_fd_sc_hd__clkinv_1`)      |
| 0.00       | 4.37 ↑    | `accumulator/_546_/RESET_B` (`sky130_fd_sc_hd__dfrtp_1`) |
|            | **4.37**  | **Data Arrival Time**                                    |

#### Required Time Trace

| Delay (ns) | Time (ns) | Description                                          |
| ---------- | --------- | ---------------------------------------------------- |
| 0.00       | 0.00      | clock `clk` (rise edge)                              |
| 0.00       | 0.00      | clock network delay (ideal)                          |
| 0.00       | 0.00      | clock reconvergence pessimism                        |
|            | 0.00 ↑    | `accumulator/_546_/CLK` (`sky130_fd_sc_hd__dfrtp_1`) |
| 0.39       | 0.39      | library removal time                                 |
|            | **0.39**  | **Data Required Time**                               |

#### Slack Calculation

|                    | Value (ns) |
| ------------------ | ---------- |
| Data Required Time | 0.39       |
| Data Arrival Time  | 4.37       |
| **Slack (MET)**    | **3.98**   |

---

### Path 2

**Startpoint:** `input_regs/_60_` _(rising edge-triggered flip-flop clocked by `clk`)_  
**Endpoint:** `pipe_regs/_58_` _(rising edge-triggered flip-flop clocked by `clk`)_  
**Path Group:** `clk`  
**Path Type:** `min`

#### Delay Trace

| Delay (ns) | Time (ns) | Description                                        |
| ---------- | --------- | -------------------------------------------------- |
| 0.00       | 0.00      | clock `clk` (rise edge)                            |
| 0.00       | 0.00      | clock network delay (ideal)                        |
| 0.00       | 0.00 ↑    | `input_regs/_60_/CLK` (`sky130_fd_sc_hd__dfrtp_1`) |
| 0.29       | 0.29 ↑    | `input_regs/_60_/Q` (`sky130_fd_sc_hd__dfrtp_1`)   |
| 0.00       | 0.29 ↑    | `pipe_regs/_58_/D` (`sky130_fd_sc_hd__dfrtp_1`)    |
|            | **0.29**  | **Data Arrival Time**                              |

#### Required Time Trace

| Delay (ns) | Time (ns) | Description                                       |
| ---------- | --------- | ------------------------------------------------- |
| 0.00       | 0.00      | clock `clk` (rise edge)                           |
| 0.00       | 0.00      | clock network delay (ideal)                       |
| 0.00       | 0.00      | clock reconvergence pessimism                     |
|            | 0.00 ↑    | `pipe_regs/_58_/CLK` (`sky130_fd_sc_hd__dfrtp_1`) |
| -0.04      | -0.04     | library hold time                                 |
|            | **-0.04** | **Data Required Time**                            |

#### Slack Calculation

|                    | Value (ns) |
| ------------------ | ---------- |
| Data Required Time | -0.04      |
| Data Arrival Time  | -0.29      |
| **Slack (MET)**    | **0.33**   |

---
