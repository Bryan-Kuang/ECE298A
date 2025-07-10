import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

async def reset_dut(dut):
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

async def send_nibble_data(dut, data_a, data_b, clear_mult):
    """Send 8-bit data over 2 cycles using 4-bit serial ports"""
    # First cycle: send lower nibbles via independent 4-bit input ports
    dut.ui_in.value = (data_b & 0xF) << 4 | (data_a & 0xF)
    dut.uio_in.value = (clear_mult & 1) | 0x02  # Enable bit set
    await RisingEdge(dut.clk)
    
    # Second cycle: send upper nibbles via independent 4-bit input ports
    dut.ui_in.value = ((data_b >> 4) & 0xF) << 4 | ((data_a >> 4) & 0xF)
    dut.uio_in.value = (clear_mult & 1) | 0x02  # Enable bit set
    await RisingEdge(dut.clk)
    
    # Disable after sending
    dut.uio_in.value = 0
    await RisingEdge(dut.clk)

async def wait_mac_pipeline(dut, cycles=6):
    """Wait for MAC pipeline to complete"""
    for _ in range(cycles):
        await RisingEdge(dut.clk)

def read_nibble_result_2cycle(dut):
    """Read complete 16-bit result from 4-bit output ports over 2 cycles"""
    # Cycle 1: Read lower nibbles from both output ports
    result_low_lower = int(dut.uo_out.value) & 0xF          # Output Port 1 (low byte lower nibble)
    result_high_lower = (int(dut.uo_out.value) >> 4) & 0xF  # Output Port 2 (high byte lower nibble)
    overflow = int(dut.uio_out.value) & 1
    data_ready = (int(dut.uio_out.value) >> 1) & 1
    
    # Advance to cycle 2 (cycle_state changes)
    # In real hardware, the cycle_state would advance, here we simulate by reading again
    # Note: This is a limitation of the test - in real hardware the cycle_state would advance automatically
    
    # For testing purposes, we'll read what the current cycle provides
    # The interface should cycle through nibbles based on internal cycle_state
    return result_low_lower, result_high_lower, overflow, data_ready

def read_nibble_result(dut):
    """Read result from 4-bit output ports (current cycle only)"""
    # Get current nibble outputs from independent 4-bit output ports
    result_low_nibble = int(dut.uo_out.value) & 0xF          # Output Port 1
    result_high_nibble = (int(dut.uo_out.value) >> 4) & 0xF  # Output Port 2
    overflow = int(dut.uio_out.value) & 1
    data_ready = (int(dut.uio_out.value) >> 1) & 1
    
    return result_low_nibble, result_high_nibble, overflow, data_ready

@cocotb.test()
async def test_4bit_serial_interface_basic(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing 4-bit Serial Interface Basic Functionality ===")
    
    # Test 1: Basic multiplication 5 * 6 = 30 using 4-bit serial ports
    print("Test 1: 5 * 6 = 30 via 4-bit serial ports")
    await send_nibble_data(dut, 5, 6, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Result from 4-bit ports: low_port={low_nibble}, high_port={high_nibble}, overflow={overflow}, ready={ready}")
    
    # Expected: 5*6 = 30 = 0x001E
    # Low byte (0x1E): lower nibble = 0xE, upper nibble = 0x1  
    # High byte (0x00): lower nibble = 0x0, upper nibble = 0x0
    
    expected_low_byte_lower = 0xE
    expected_high_byte_lower = 0x0
    
    assert low_nibble == expected_low_byte_lower, f"Low port nibble mismatch: expected {expected_low_byte_lower}, got {low_nibble}"
    assert high_nibble == expected_high_byte_lower, f"High port nibble mismatch: expected {expected_high_byte_lower}, got {high_nibble}"
    
    print("✅ 4-bit serial interface basic test passed")

@cocotb.test() 
async def test_4bit_serial_result_readback(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing 4-bit Serial Interface Result Readback ===")
    
    # Test with a known result: 15 * 17 = 255 = 0x00FF
    print("Test: 15 * 17 = 255 = 0x00FF")
    await send_nibble_data(dut, 15, 17, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"4-bit serial result: low_port={low_nibble:X}, high_port={high_nibble:X}")
    
    # Expected: 15*17 = 255 = 0x00FF
    # Low byte (0xFF): lower nibble = 0xF, upper nibble = 0xF
    # High byte (0x00): lower nibble = 0x0, upper nibble = 0x0
    # Currently reading lower nibbles (cycle_state = 0)
    expected_low_byte_lower = 0xF
    expected_high_byte_lower = 0x0
    
    assert low_nibble == expected_low_byte_lower, f"Low port lower nibble: expected {expected_low_byte_lower:X}, got {low_nibble:X}"
    assert high_nibble == expected_high_byte_lower, f"High port lower nibble: expected {expected_high_byte_lower:X}, got {high_nibble:X}"
    
    print("✅ 4-bit serial result readback test passed")

@cocotb.test()
async def test_4bit_accumulation(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing 4-bit Serial Interface Accumulation ===")
    
    # Start with 10 * 10 = 100
    print("Clear: 10 * 10 = 100")
    await send_nibble_data(dut, 10, 10, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"After clear: low_port={low_nibble:X}, high_port={high_nibble:X}")
    
    # Expected: 10*10 = 100 = 0x0064
    # Low byte (0x64): lower nibble = 0x4, upper nibble = 0x6
    # High byte (0x00): lower nibble = 0x0, upper nibble = 0x0
    # Reading lower nibbles
    assert low_nibble == 0x4, f"Clear operation low port: expected 0x4, got {low_nibble:X}"
    assert high_nibble == 0x0, f"Clear operation high port: expected 0x0, got {high_nibble:X}"
    
    # Accumulate: +5 * 5 = +25 -> 125
    print("Accumulate: +5 * 5 = +25 -> 125")
    await send_nibble_data(dut, 5, 5, 0)  # Accumulate mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"After accumulate: low_port={low_nibble:X}, high_port={high_nibble:X}")
    
    # Expected: 125 = 0x007D
    # Low byte (0x7D): lower nibble = 0xD, upper nibble = 0x7
    # High byte (0x00): lower nibble = 0x0, upper nibble = 0x0
    # Reading lower nibbles
    assert low_nibble == 0xD, f"Accumulate operation low port: expected 0xD, got {low_nibble:X}"
    assert high_nibble == 0x0, f"Accumulate operation high port: expected 0x0, got {high_nibble:X}"
    
    print("✅ 4-bit serial accumulation test passed")

@cocotb.test()
async def test_4bit_overflow(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing 4-bit Serial Interface Overflow Detection ===")
    
    # Test maximum values: 255 * 255 = 65025 = 0xFE01
    print("Test: 255 * 255 = 65025")
    await send_nibble_data(dut, 255, 255, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Large value result: low_port={low_nibble:X}, high_port={high_nibble:X}, overflow={overflow}")
    
    # Expected: 255*255 = 65025 = 0xFE01
    # Low byte (0x01): lower nibble = 0x1, upper nibble = 0x0
    # High byte (0xFE): lower nibble = 0xE, upper nibble = 0xF
    # Reading lower nibbles (cycle_state = 0)
    assert low_nibble == 0x1, f"Large multiplication low port: expected 0x1, got {low_nibble:X}"
    assert high_nibble == 0xE, f"Large multiplication high port: expected 0xE, got {high_nibble:X}"
    
    # Test overflow: add another large value to cause overflow
    print("Test overflow: +200 * 200 = +40000 -> should overflow")
    await send_nibble_data(dut, 200, 200, 0)  # Accumulate mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Overflow test: low_port={low_nibble:X}, high_port={high_nibble:X}, overflow={overflow}")
    
    # 65025 + 40000 = 105025 > 65535, should overflow
    assert overflow == 1, f"Overflow flag should be set, but got {overflow}"
    
    print("✅ 4-bit serial overflow test passed")

@cocotb.test()
async def test_4bit_timing(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing 4-bit Serial Interface Timing ===")
    
    # Test back-to-back operations
    print("Back-to-back: 6 * 7 = 42, then +3 * 4 = +12 -> 54")
    
    await send_nibble_data(dut, 6, 7, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"First operation: low_port={low_nibble:X}, high_port={high_nibble:X}")
    
    # Expected: 6*7 = 42 = 0x002A
    # Low byte (0x2A): lower nibble = 0xA, upper nibble = 0x2
    # High byte (0x00): lower nibble = 0x0, upper nibble = 0x0
    # Reading lower nibbles
    assert low_nibble == 0xA, f"First operation low port: expected 0xA, got {low_nibble:X}"
    assert high_nibble == 0x0, f"First operation high port: expected 0x0, got {high_nibble:X}"
    
    await send_nibble_data(dut, 3, 4, 0)  # Accumulate mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Second operation: low_port={low_nibble:X}, high_port={high_nibble:X}")
    
    # Expected: 42 + 12 = 54 = 0x0036
    # Low byte (0x36): lower nibble = 0x6, upper nibble = 0x3
    # High byte (0x00): lower nibble = 0x0, upper nibble = 0x0
    # Reading lower nibbles
    assert low_nibble == 0x6, f"Second operation low port: expected 0x6, got {low_nibble:X}"
    assert high_nibble == 0x0, f"Second operation high port: expected 0x0, got {high_nibble:X}"
    
    print("✅ 4-bit serial timing test passed") 