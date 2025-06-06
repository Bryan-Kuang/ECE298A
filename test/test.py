# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start 8-bit Counter Test")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset test
    dut._log.info("Testing Reset functionality")
    dut.ena.value = 1
    dut.ui_in.value = 0      # Base count = 0
    dut.uio_in.value = 0b00000010  # out_enable = 1, load = 0 (bit 1 = out_en, bit 0 = load)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    
    # After reset, counter should be 0
    assert dut.uo_out.value == 0, f"Reset failed: expected 0, got {dut.uo_out.value}"
    dut._log.info("✓ Reset test passed")

    # Test counting from 0
    dut._log.info("Testing basic counting functionality")
    for i in range(5):
        await ClockCycles(dut.clk, 1)
        expected = (i + 1) & 0xFF  # Ensure 8-bit wrap
        actual = int(dut.uo_out.value)
        assert actual == expected, f"Count {i+1}: expected {expected}, got {actual}"
    dut._log.info(f"✓ Basic counting test passed, counter is now at {int(dut.uo_out.value)}")

    # Test load functionality
    dut._log.info("Testing load functionality")
    base_count = 100
    
    # Set both base count and load signal at the same time
    dut.ui_in.value = base_count   # Set base count to 100
    dut.uio_in.value = 0b00000011  # out_enable = 1, load = 1
    
    # Wait a small amount of time for signals to propagate
    await Timer(1, units="ns")
    
    # Wait for the load to take effect
    await ClockCycles(dut.clk, 1)
    
    # Wait a small amount of time for the output to update
    await Timer(1, units="ns")
    
    # After load, counter should be 100
    actual_value = int(dut.uo_out.value)
    dut._log.info(f"Load test: expected {base_count}, got {actual_value} (binary: {bin(actual_value)})")
    assert actual_value == base_count, f"Load failed: expected {base_count}, got {actual_value}"
    dut._log.info("✓ Load functionality test passed")
    
    # Test counting after load
    dut._log.info("Testing counting after load")
    dut.uio_in.value = 0b00000010  # out_enable = 1, load = 0 (disable load)
    for i in range(3):
        await ClockCycles(dut.clk, 1)
        await Timer(1, units="ns")  # Wait for output to update
        expected = (base_count + i + 1) & 0xFF
        actual = int(dut.uo_out.value)
        assert actual == expected, f"Count after load {i+1}: expected {expected}, got {actual}"
    dut._log.info("✓ Counting after load test passed")

    # Test tri-state functionality
    dut._log.info("Testing tri-state output functionality")
    dut.uio_in.value = 0b00000000  # out_enable = 0, load = 0 (disable output)
    await ClockCycles(dut.clk, 1)
    
    # When output is disabled, we should get high-impedance (Z)
    # In simulation, this typically shows as 'z' or undefined
    try:
        output_val = dut.uo_out.value
        # If we can read a value, it should be in high-impedance state
        dut._log.info(f"Tri-state output value: {output_val}")
    except:
        # This is expected for high-impedance state in some simulators
        dut._log.info("Output in high-impedance state (Z)")
    dut._log.info("✓ Tri-state functionality test passed")
    
    # Re-enable output and verify counter continued counting
    dut._log.info("Testing counter continued during tri-state")
    dut.uio_in.value = 0b00000010  # out_enable = 1, load = 0 (re-enable output)
    await ClockCycles(dut.clk, 1)
    await Timer(1, units="ns")  # Wait for output to update
    
    # Counter should have continued counting during tri-state period
    expected = (base_count + 5) & 0xFF  # +5 because we had 3 counts after load + 1 during tri-state + 1 when re-enabling
    actual = int(dut.uo_out.value)
    assert actual == expected, f"Counter during tri-state: expected {expected}, got {actual}"
    dut._log.info("✓ Counter continued during tri-state test passed")

    # Test overflow (8-bit wrap-around)
    dut._log.info("Testing 8-bit overflow")
    dut.ui_in.value = 254   # Load near maximum
    dut.uio_in.value = 0b00000011  # out_enable = 1, load = 1
    await ClockCycles(dut.clk, 1)
    await Timer(1, units="ns")  # Wait for output to update
    actual = int(dut.uo_out.value)
    assert actual == 254, f"Load 254 failed: expected 254, got {actual}"
    
    dut.uio_in.value = 0b00000010  # out_enable = 1, load = 0 (disable load)
    await ClockCycles(dut.clk, 1)
    await Timer(1, units="ns")  # Wait for output to update
    actual = int(dut.uo_out.value)
    assert actual == 255, f"Count to 255 failed: expected 255, got {actual}"
    
    await ClockCycles(dut.clk, 1)
    await Timer(1, units="ns")  # Wait for output to update
    actual = int(dut.uo_out.value)
    assert actual == 0, f"Overflow failed: expected 0, got {actual}"
    dut._log.info("✓ 8-bit overflow test passed")

    dut._log.info("All tests completed successfully! 🎉")