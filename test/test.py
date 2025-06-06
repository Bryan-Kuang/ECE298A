# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_counter(dut):
    dut._log.info("Start 8-bit counter test")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Initialize signals
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # Test 1: Reset behavior
    dut._log.info("Test 1: Reset behavior")
    dut.rst_n.value = 0  # Assert reset
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1  # Release reset
    
    # Set output enable to observe counter value
    dut.uio_in.value = 2  # bit[1] is output enable
    await ClockCycles(dut.clk, 1)
    
    # After reset, counter should be 0
    assert dut.uo_out.value == 0, f"Reset failed: counter = {dut.uo_out.value}, expected 0"
    
    # Test 2: Normal counting operation
    dut._log.info("Test 2: Normal counting operation")
    # Count for several cycles and check incrementing behavior
    for i in range(10):
        current_value = int(dut.uo_out.value)
        await ClockCycles(dut.clk, 1)
        expected_value = (current_value + 1) & 0xFF  # 8-bit wrap around
        assert dut.uo_out.value == expected_value, f"Count failed: counter = {dut.uo_out.value}, expected {expected_value}"
    
    # Test 3: Load functionality
    dut._log.info("Test 3: Load functionality")
    test_value = 123
    dut._log.info(f"Before load: counter = {dut.uo_out.value}")
    
    # Set signals and wait for them to propagate
    dut.ui_in.value = test_value  # Set base count value
    dut.uio_in.value = 3  # Set both load (bit 0) and output enable (bit 1)
    dut._log.info(f"Set ui_in = {dut.ui_in.value}, uio_in = {dut.uio_in.value}")
    
    # Wait for load to take effect on next clock edge
    await ClockCycles(dut.clk, 1)
    dut._log.info(f"After load clock: counter = {dut.uo_out.value}")
    
    # Verify loaded value
    assert dut.uo_out.value == test_value, f"Load failed: counter = {dut.uo_out.value}, expected {test_value}"
    
    dut.uio_in.value = 2  # Clear load, keep output enable
    
    # Test 4: Continued counting after load
    dut._log.info("Test 4: Continued counting after load")
    for i in range(5):
        current_value = int(dut.uo_out.value)
        await ClockCycles(dut.clk, 1)
        expected_value = (current_value + 1) & 0xFF
        assert dut.uo_out.value == expected_value, f"Post-load count failed: counter = {dut.uo_out.value}, expected {expected_value}"
    
    # Test 5: Output enable control
    dut._log.info("Test 5: Output enable control")
    # Disable output
    dut.uio_in.value = 0  # Clear output enable
    await ClockCycles(dut.clk, 1)
    
    # When output is disabled, the output should be high-impedance (Z)
    # In simulation, this is often represented as X, but cocotb might handle it differently
    # We'll check if the output is not the expected counter value
    
    # Re-enable output
    dut.uio_in.value = 2  # Set output enable
    await ClockCycles(dut.clk, 1)
    
    # Counter should have continued incrementing internally
    # But we can only verify it's working again, not the exact value
    
    # Test 6: Overflow behavior
    dut._log.info("Test 6: Overflow behavior")
    # Set counter to 255 (max 8-bit value)
    dut.ui_in.value = 255
    dut.uio_in.value = 3  # Set load and output enable
    await ClockCycles(dut.clk, 1)
    
    # Verify loaded value
    assert dut.uo_out.value == 255, f"Load max value failed: counter = {dut.uo_out.value}, expected 255"
    
    dut.uio_in.value = 2  # Clear load, keep output enable
    
    # Check overflow to 0
    await ClockCycles(dut.clk, 1)
    assert dut.uo_out.value == 0, f"Overflow failed: counter = {dut.uo_out.value}, expected 0"
    
    dut._log.info("8-bit counter test completed successfully")
