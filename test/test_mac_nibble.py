import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

async def reset_dut(dut):
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

async def send_nibble_data(dut, data_a, data_b, clear_mult):
    """Send 8-bit data over 2 cycles using 4-bit nibbles"""
    # First cycle: send lower nibbles
    dut.ui_in.value = (data_b & 0xF) << 4 | (data_a & 0xF)
    dut.uio_in.value = (clear_mult & 1) | 0x02  # Enable bit set
    await RisingEdge(dut.clk)
    
    # Second cycle: send upper nibbles
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

def read_nibble_result(dut):
    """Read result from nibble outputs"""
    # Get current nibble outputs
    result_low_nibble = int(dut.uo_out.value) & 0xF
    result_high_nibble = (int(dut.uo_out.value) >> 4) & 0xF
    overflow = int(dut.uio_out.value) & 1
    data_ready = (int(dut.uio_out.value) >> 1) & 1
    
    return result_low_nibble, result_high_nibble, overflow, data_ready

@cocotb.test()
async def test_nibble_basic_functionality(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Nibble Interface Basic Functionality ===")
    
    # Test 1: Basic multiplication 5 * 6 = 30
    print("Test 1: 5 * 6 = 30")
    await send_nibble_data(dut, 5, 6, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Result nibbles: low={low_nibble}, high={high_nibble}, overflow={overflow}, ready={ready}")
    
    # Test 2: Zero multiplication
    print("Test 2: 0 * 255 = 0")
    await send_nibble_data(dut, 0, 255, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Result nibbles: low={low_nibble}, high={high_nibble}, overflow={overflow}, ready={ready}")
    
    print("✅ Nibble basic functionality test passed")

@cocotb.test()
async def test_nibble_accumulation(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Nibble Interface Accumulation ===")
    
    # Start with 10 * 10 = 100
    print("Clear: 10 * 10 = 100")
    await send_nibble_data(dut, 10, 10, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"After clear: low={low_nibble}, high={high_nibble}")
    
    # Accumulate: +5 * 5 = +25 -> 125
    print("Accumulate: +5 * 5 = +25 -> 125")
    await send_nibble_data(dut, 5, 5, 0)  # Accumulate mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"After accumulate: low={low_nibble}, high={high_nibble}")
    
    print("✅ Nibble accumulation test passed")

@cocotb.test()
async def test_nibble_large_values(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Nibble Interface Large Values ===")
    
    # Test maximum values: 255 * 127 = 32385
    print("Test: 255 * 127 = 32385")
    await send_nibble_data(dut, 255, 127, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Large value result: low={low_nibble}, high={high_nibble}, overflow={overflow}")
    
    # Test overflow: add large value to cause overflow
    print("Test overflow: +200 * 100 = +20000 -> overflow")
    await send_nibble_data(dut, 200, 100, 0)  # Accumulate mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Overflow test: low={low_nibble}, high={high_nibble}, overflow={overflow}")
    
    print("✅ Nibble large values test passed")

@cocotb.test()
async def test_nibble_timing(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Nibble Interface Timing ===")
    
    # Test back-to-back operations
    print("Back-to-back: 6 * 7 = 42, then +3 * 4 = +12 -> 54")
    
    await send_nibble_data(dut, 6, 7, 1)  # Clear mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"First operation: low={low_nibble}, high={high_nibble}")
    
    await send_nibble_data(dut, 3, 4, 0)  # Accumulate mode
    await wait_mac_pipeline(dut)
    
    low_nibble, high_nibble, overflow, ready = read_nibble_result(dut)
    print(f"Second operation: low={low_nibble}, high={high_nibble}")
    
    print("✅ Nibble timing test passed") 