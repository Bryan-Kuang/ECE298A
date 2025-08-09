import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles

# Fixed random test configuration
TEST_ITER = 1000
TEST_SEED = 1234567

async def reset_dut(dut):
    """Reset the DUT"""
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

async def send_data_2cycle(dut, data_a, data_b, clear_mult):
    """Send data using new 2-cycle 8-bit serial protocol"""
    # Cycle 1: Send Data A + control signal
    dut.ui_in.value = data_a & 0xFF               # 8-bit Data A
    dut.uio_in.value = (clear_mult & 0x1) | 0x2   # bit[0] = clear_mult, bit[1] = enable
    await RisingEdge(dut.clk)
    
    # Cycle 2: Send Data B
    dut.ui_in.value = data_b & 0xFF               # 8-bit Data B  
    dut.uio_in.value = 0x2                        # bit[1] = enable (clear_mult not valid in cycle 2)
    await RisingEdge(dut.clk)
    
    # Disable interface after input
    dut.uio_in.value = 0x0                        # Disable enable
    await RisingEdge(dut.clk)

async def wait_mac_pipeline(dut, cycles=6):
    """Wait for MAC pipeline to process"""
    await ClockCycles(dut.clk, cycles)

def read_result_2cycle(dut):
    """Read result using new 2-cycle 8-bit serial protocol"""
    # Current cycle outputs (either low 8 bits or high 8 bits depending on internal state)
    data_output = int(dut.uo_out.value) & 0xFF
    overflow = int(dut.uio_out.value) & 1
    data_ready = (int(dut.uio_out.value) >> 1) & 1
    
    return data_output, overflow, data_ready

async def read_full_result_2cycle(dut):
    """Read complete 16-bit result over 2 cycles"""
    # Wait a few cycles to ensure we're in a stable output state
    await ClockCycles(dut.clk, 2)
    
    # Read two consecutive cycles to get both high and low bytes
    first_read, overflow, ready = read_result_2cycle(dut)
    
    await RisingEdge(dut.clk)
    second_read, overflow2, ready2 = read_result_2cycle(dut)
    
    # From our debug test, we confirmed the pattern is: high_byte, low_byte
    # For 255*255 = 0xFE01: we see 0xFE (high), 0x01 (low)
    # For 16*16 = 0x0100: we see 0x01 (high), 0x00 (low)  
    # So first_read is always high byte, second_read is always low byte
    high_8bits = first_read
    low_8bits = second_read
    
    # Combine into 16-bit result
    result_16bit = (high_8bits << 8) | low_8bits
    return result_16bit, overflow, ready

@cocotb.test()
async def test_basic_unsigned(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    import random
    random.seed(TEST_SEED)
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        await send_data_2cycle(dut, a, b, 1)  # clear mode, unsigned
        await wait_mac_pipeline(dut)
        result_16bit, overflow, ready = await read_full_result_2cycle(dut)
        expected = (a * b) & 0xFFFF
        assert result_16bit == expected, f"[basic_unsigned] iter={i} a={a} b={b} exp={expected} got={result_16bit}"
        assert overflow == 0, f"[basic_unsigned] iter={i} overflow unexpected: {overflow}"

@cocotb.test() 
async def test_readback(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    import random
    random.seed(TEST_SEED)
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        await send_data_2cycle(dut, a, b, 1)
        await wait_mac_pipeline(dut)
        # Read two cycles to reconstruct 16-bit
        result_16bit, overflow, ready = await read_full_result_2cycle(dut)
        expected = (a * b) & 0xFFFF
        assert result_16bit == expected, f"[readback] iter={i} a={a} b={b} exp={expected} got={result_16bit}"
        assert overflow == 0, f"[readback] iter={i} overflow unexpected: {overflow}"

@cocotb.test()
async def test_accumulate_unsigned(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    import random
    random.seed(TEST_SEED)
    acc = 0
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        clear = 1 if (random.random() < 0.15 or i == 0) else 0
        await send_data_2cycle(dut, a, b, clear)
        await wait_mac_pipeline(dut)
        result_16bit, overflow, _ = await read_full_result_2cycle(dut)
        prod = (a * b) & 0xFFFF
        if clear:
            acc = prod
        else:
            acc = (acc + prod) & 0xFFFF
        assert result_16bit == acc, f"[accumulate_unsigned] iter={i} exp={acc} got={result_16bit}"

@cocotb.test()
async def test_overflow_unsigned(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    import random
    random.seed(TEST_SEED)
    acc = 0
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        clear = 1 if (random.random() < 0.2 or i == 0) else 0
        await send_data_2cycle(dut, a, b, clear)
        await wait_mac_pipeline(dut)
        result_16bit, overflow, _ = await read_full_result_2cycle(dut)
        prod = (a * b) & 0xFFFF
        if clear:
            acc = prod
        else:
            acc = (acc + prod) & 0x1FFFF  # 17-bit internal
        exp_ov = 1 if (acc >> 16) & 1 else 0
        exp_res = acc & 0xFFFF
        assert result_16bit == exp_res, f"[overflow_unsigned] iter={i} exp={exp_res} got={result_16bit}"
        assert overflow == exp_ov, f"[overflow_unsigned] iter={i} ov_exp={exp_ov} ov_got={overflow}"

@cocotb.test()
async def test_back_to_back(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    import random
    random.seed(TEST_SEED)
    acc = 0
    for i in range(TEST_ITER):
        a1 = random.randrange(0, 256)
        b1 = random.randrange(0, 256)
        await send_data_2cycle(dut, a1, b1, 1)
        await wait_mac_pipeline(dut)
        r1, ov1, _ = await read_full_result_2cycle(dut)
        acc = (a1 * b1) & 0xFFFF
        assert r1 == acc and ov1 == 0

        a2 = random.randrange(0, 256)
        b2 = random.randrange(0, 256)
        await send_data_2cycle(dut, a2, b2, 0)
        await wait_mac_pipeline(dut)
        r2, ov2, _ = await read_full_result_2cycle(dut)
        acc = (acc + (a2 * b2)) & 0x1FFFF
        exp2 = acc & 0xFFFF
        expov2 = 1 if (acc >> 16) & 1 else 0
        assert r2 == exp2 and ov2 == expov2

@cocotb.test()
async def test_output_bytes(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    import random
    random.seed(TEST_SEED)
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        await send_data_2cycle(dut, a, b, 1)
        await wait_mac_pipeline(dut)
        first, ov1, _ = read_result_2cycle(dut)
        await RisingEdge(dut.clk)
        second, ov2, _ = read_result_2cycle(dut)
        full, ov, _ = await read_full_result_2cycle(dut)
        low = full & 0xFF
        high = (full >> 8) & 0xFF
        assert sorted([first, second]) == sorted([low, high]), (
            f"[output_bytes] iter={i} bytes mismatch: ({first:02X},{second:02X}) vs expected any order of ({low:02X},{high:02X})")
        assert ov1 == ov2 == 0

async def send_data_2cycle_signed(dut, data_a, data_b, clear_mult, signed_mode):
    """Send data using new 2-cycle 8-bit serial protocol with signed mode control"""
    # Cycle 1: Send Data A + control signals
    dut.ui_in.value = data_a & 0xFF               # 8-bit Data A
    control_bits = (clear_mult & 0x1) | 0x2 | ((signed_mode & 0x1) << 2)  # bit[0] = clear_mult, bit[1] = enable, bit[2] = signed_mode
    dut.uio_in.value = control_bits
    await RisingEdge(dut.clk)
    
    # Cycle 2: Send Data B (signed_mode persists)
    dut.ui_in.value = data_b & 0xFF               # 8-bit Data B  
    dut.uio_in.value = 0x2 | ((signed_mode & 0x1) << 2)  # bit[1] = enable, bit[2] = signed_mode
    await RisingEdge(dut.clk)
    
    # Disable interface after input
    dut.uio_in.value = 0x0                        # Disable enable
    await RisingEdge(dut.clk)

def to_signed_8bit(value):
    """Convert unsigned 8-bit value to signed interpretation"""
    if value > 127:
        return value - 256
    return value

def to_signed_16bit(value):
    """Convert unsigned 16-bit value to signed interpretation"""
    if value > 32767:
        return value - 65536
    return value

# --------- Randomized testing helpers ---------
def _bit(val: int, pos: int) -> int:
    return (val >> pos) & 1

def _mask17(val: int) -> int:
    return val & 0x1FFFF  # keep 17 bits

def _sign_extend_17_from16(x16: int) -> int:
    # Extend 16-bit two's complement value to 17 bits by copying bit15 into bit16
    sign = 1 if (x16 & 0x8000) else 0
    return (sign << 16) | (x16 & 0xFFFF)

def mac_step_model(acc17: int, a: int, b: int, clear: int, signed_mode: int):
    """One MAC step software model aligned to RTL accumulator_17bit behavior.

    Returns (new_acc17, result16, overflow_flag)
    - acc17: 17-bit register value (integer 0..0x1FFFF)
    - a, b: 8-bit unsigned operands (0..255)
    - clear: 1 to load current product, 0 to accumulate
    - signed_mode: 1 for signed arithmetic, 0 for unsigned
    """
    if signed_mode:
        sa = to_signed_8bit(a)
        sb = to_signed_8bit(b)
        prod = sa * sb  # Python int (could be negative)
        prod16 = prod & 0xFFFF  # lower 16 bits like hardware
        if clear:
            new_acc17 = _mask17(prod16)
            result16 = prod16 & 0xFFFF
            overflow = 0
        else:
            signed_acc17 = _sign_extend_17_from16(acc17 & 0xFFFF)
            signed_mult17 = _sign_extend_17_from16(prod16)
            add17 = _mask17(signed_acc17 + signed_mult17)
            overflow = int((_bit(signed_acc17, 15) == _bit(signed_mult17, 15)) and (_bit(add17, 15) != _bit(signed_acc17, 15)))
            new_acc17 = add17
            result16 = add17 & 0xFFFF
        return new_acc17, result16, overflow
    else:
        prod = (a & 0xFF) * (b & 0xFF)
        prod16 = prod & 0xFFFF
        if clear:
            new_acc17 = _mask17(prod16)
            result16 = prod16
            overflow = 0
        else:
            add17 = (acc17 + prod16)
            overflow = int(_bit(add17, 16) == 1)
            new_acc17 = _mask17(add17)
            result16 = new_acc17 & 0xFFFF
        return new_acc17, result16, overflow

@cocotb.test()
async def test_random_unsigned_mac_1000(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.ena.value = 1
    await reset_dut(dut)

    import random
    random.seed(TEST_SEED)
    print(f"[RAND] test_random_unsigned_mac_1000 SEED={TEST_SEED} ITER={TEST_ITER}")

    acc17 = 0
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        clear = 1 if (random.random() < 0.15 or i == 0) else 0  # 15% clear, ensure first op clears
        signed_mode = 0

        await send_data_2cycle_signed(dut, a, b, clear, signed_mode)
        await wait_mac_pipeline(dut)
        rtl_result, rtl_overflow, _ = await read_full_result_2cycle(dut)

        acc17, mdl_result, mdl_overflow = mac_step_model(acc17, a, b, clear, signed_mode)

        assert rtl_result == mdl_result, (
            f"[UNSIGNED] iter={i} a={a} b={b} clear={clear} expected={mdl_result} got={rtl_result}")
        assert rtl_overflow == mdl_overflow, (
            f"[UNSIGNED] iter={i} a={a} b={b} clear={clear} overflow_expected={mdl_overflow} overflow_got={rtl_overflow}")

@cocotb.test()
async def test_random_signed_mac_1000(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.ena.value = 1
    await reset_dut(dut)

    import random
    random.seed(TEST_SEED)
    print(f"[RAND] test_random_signed_mac_1000 SEED={TEST_SEED} ITER={TEST_ITER}")

    acc17 = 0
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        clear = 1 if (random.random() < 0.15 or i == 0) else 0
        signed_mode = 1

        await send_data_2cycle_signed(dut, a, b, clear, signed_mode)
        await wait_mac_pipeline(dut)
        rtl_result, rtl_overflow, _ = await read_full_result_2cycle(dut)

        acc17, mdl_result, mdl_overflow = mac_step_model(acc17, a, b, clear, signed_mode)

        assert rtl_result == mdl_result, (
            f"[SIGNED] iter={i} a={to_signed_8bit(a)} b={to_signed_8bit(b)} clear={clear} "
            f"expected={to_signed_16bit(mdl_result)} (0x{mdl_result:04X}) got={to_signed_16bit(rtl_result)} (0x{rtl_result:04X})")
        assert rtl_overflow == mdl_overflow, (
            f"[SIGNED] iter={i} a={to_signed_8bit(a)} b={to_signed_8bit(b)} clear={clear} "
            f"overflow_expected={mdl_overflow} overflow_got={rtl_overflow}")

@cocotb.test()
async def test_signed_basic(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Signed Mode Basic Multiplication ===")
    
    # Test 1: Positive * Positive: 5 * 6 = 30
    print("Test 1: 5 * 6 = 30 (signed mode)")
    await send_data_2cycle_signed(dut, 5, 6, 1, 1)  # Clear mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Result: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    assert result_16bit == 30, f"5*6 signed: expected 30, got {result_16bit}"
    assert overflow == 0, f"Unexpected overflow: {overflow}"
    
    # Test 2: Positive * Negative: 10 * (-5) = -50
    # -5 in 8-bit two's complement is 251 (0xFB)
    print("Test 2: 10 * (-5) = -50 (signed mode)")
    await send_data_2cycle_signed(dut, 10, 251, 1, 1)  # Clear mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    signed_result = to_signed_16bit(result_16bit)
    print(f"Result: {signed_result} (unsigned: {result_16bit}, 0x{result_16bit:04X}), overflow={overflow}")
    
    assert signed_result == -50, f"10*(-5) signed: expected -50, got {signed_result}"
    assert overflow == 0, f"Unexpected overflow: {overflow}"
    
    # Test 3: Negative * Negative: (-8) * (-7) = 56
    # -8 in 8-bit two's complement is 248 (0xF8)
    # -7 in 8-bit two's complement is 249 (0xF9)
    print("Test 3: (-8) * (-7) = 56 (signed mode)")
    await send_data_2cycle_signed(dut, 248, 249, 1, 1)  # Clear mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Result: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    assert result_16bit == 56, f"(-8)*(-7) signed: expected 56, got {result_16bit}"
    assert overflow == 0, f"Unexpected overflow: {overflow}"
    
    print("✅ Signed mode basic multiplication test passed")

@cocotb.test()
async def test_accumulate_signed(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Signed Mode Accumulation ===")
    
    # Start with 10 * 10 = 100
    print("Clear: 10 * 10 = 100 (signed mode)")
    await send_data_2cycle_signed(dut, 10, 10, 1, 1)  # Clear mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"After clear: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    assert result_16bit == 100, f"Clear operation: expected 100, got {result_16bit}"
    assert overflow == 0, f"Unexpected overflow in clear: {overflow}"
    
    # Accumulate: +(-5) * 6 = -30 -> 100 - 30 = 70
    # -5 in 8-bit two's complement is 251 (0xFB)
    print("Accumulate: (-5) * 6 = -30 -> 100 - 30 = 70 (signed mode)")
    await send_data_2cycle_signed(dut, 251, 6, 0, 1)  # Accumulate mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"After accumulate: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    assert result_16bit == 70, f"Accumulate operation: expected 70, got {result_16bit}"
    assert overflow == 0, f"Unexpected overflow in accumulate: {overflow}"
    
    # Accumulate more: +(-4) * (-5) = +20 -> 70 + 20 = 90
    # -4 in 8-bit two's complement is 252 (0xFC)
    print("Accumulate: (-4) * (-5) = +20 -> 70 + 20 = 90 (signed mode)")
    await send_data_2cycle_signed(dut, 252, 251, 0, 1)  # Accumulate mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Final result: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    assert result_16bit == 90, f"Final accumulate operation: expected 90, got {result_16bit}"
    assert overflow == 0, f"Unexpected overflow in final accumulate: {overflow}"
    
    print("✅ Signed mode accumulation test passed")

@cocotb.test()
async def test_overflow_signed(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Signed Mode Overflow Detection ===")
    
    # Test large positive values: 127 * 127 = 16129 (no overflow)
    print("Test: 127 * 127 = 16129 (max positive, signed mode)")
    await send_data_2cycle_signed(dut, 127, 127, 1, 1)  # Clear mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Max positive result: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    assert result_16bit == 16129, f"127*127 signed: expected 16129, got {result_16bit}"
    assert overflow == 0, f"Unexpected overflow: {overflow}"
    
    # Test accumulation that causes positive overflow
    # Add 127 * 127 again: 16129 + 16129 = 32258 (still within 16-bit signed range)
    print("Accumulate: +127 * 127 = +16129 -> 32258 (still within range)")
    await send_data_2cycle_signed(dut, 127, 127, 0, 1)  # Accumulate mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Double max result: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    assert result_16bit == 32258, f"Double accumulation: expected 32258, got {result_16bit}"
    assert overflow == 0, f"Unexpected overflow: {overflow}"
    
    # Now cause actual overflow by adding more
    # Add another large value to push beyond 32767
    print("Force overflow: +100 * 100 = +10000 -> should cause signed overflow")
    await send_data_2cycle_signed(dut, 100, 100, 0, 1)  # Accumulate mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    signed_result = to_signed_16bit(result_16bit)
    print(f"Overflow test: signed={signed_result}, unsigned={result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    # 32258 + 10000 = 42258 > 32767, should overflow in signed mode
    assert overflow == 1, f"Signed overflow flag should be set, but got {overflow}"
    
    print("✅ Signed mode overflow test passed")

@cocotb.test()
async def test_mode_compare(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Mixed Unsigned/Signed Mode Operations ===")
    
    # Test same inputs in unsigned vs signed mode
    # Using 200 * 200 which behaves differently in unsigned vs signed
    # In unsigned: 200 * 200 = 40000
    # In signed: (-56) * (-56) = 3136 (since 200 = -56 in signed 8-bit)
    
    print("Test: 200 * 200 in unsigned mode")
    await send_data_2cycle_signed(dut, 200, 200, 1, 0)  # Clear mode, unsigned
    await wait_mac_pipeline(dut)
    
    result_16bit_unsigned, overflow_unsigned, ready = await read_full_result_2cycle(dut)
    print(f"Unsigned result: {result_16bit_unsigned} (0x{result_16bit_unsigned:04X}), overflow={overflow_unsigned}")
    
    assert result_16bit_unsigned == 40000, f"200*200 unsigned: expected 40000, got {result_16bit_unsigned}"
    
    # Reset between tests to ensure clean state
    await reset_dut(dut)
    await ClockCycles(dut.clk, 5)
    
    # Same inputs in signed mode
    print("Test: 200 * 200 in signed mode ((-56) * (-56) = 3136)")
    await send_data_2cycle_signed(dut, 200, 200, 1, 1)  # Clear mode, signed
    await wait_mac_pipeline(dut)
    
    result_16bit_signed, overflow_signed, ready = await read_full_result_2cycle(dut)
    print(f"Signed result: {result_16bit_signed} (0x{result_16bit_signed:04X}), overflow={overflow_signed}")
    
    # 200 in 8-bit signed is -56, so (-56) * (-56) = 3136
    assert result_16bit_signed == 3136, f"200*200 signed: expected 3136, got {result_16bit_signed}"
    
    print("✅ Mixed mode test passed")

@cocotb.test()
async def test_debug_signed(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Debug Signed Mode Signal Path ===")
    
    # Simple test: 10 * (-5) = -50 in signed mode
    # -5 in 8-bit two's complement is 251 (0xFB)
    print("Testing: 10 * (-5) = -50 in signed mode")
    print(f"Before operation: uio_in[2] = {int(dut.uio_in.value) & 4}")
    
    await send_data_2cycle_signed(dut, 10, 251, 1, 1)  # Clear mode, signed
    
    # Check intermediate signals in pipeline via hierarchical access
    print(f"After input: dut.signed_mode = {dut.dut.signed_mode.value}")
    print(f"After input: nibble_if signed_mode = {dut.dut.serial_if.mac_signed_mode.value}")
    print(f"After input: reg_signed_mode = {dut.dut.reg_signed_mode.value}")  
    print(f"After input: pipe_signed_mode = {dut.dut.pipe_signed_mode.value}")
    
    await wait_mac_pipeline(dut, 2)
    
    print(f"After pipeline: pipe_signed_mode = {dut.dut.pipe_signed_mode.value}")
    print(f"Multiplier inputs: in0={dut.dut.pipe_A.value}, in1={dut.dut.pipe_B.value}, signed_mode={dut.dut.multiplier.signed_mode.value}")
    print(f"Multiplier result: {dut.dut.mult_result.value} (0x{int(dut.dut.mult_result.value):04X})")
    
    await wait_mac_pipeline(dut, 4)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    signed_result = to_signed_16bit(result_16bit)
    print(f"Final result: signed={signed_result}, unsigned={result_16bit} (0x{result_16bit:04X})")
    
    # Calculate what we expect
    # In signed mode: 10 * (-5) = -50 = 0xFFCE in 16-bit two's complement
    expected_unsigned = (-50) & 0xFFFF  # Convert -50 to unsigned 16-bit representation
    print(f"Expected: signed=-50, unsigned={expected_unsigned} (0x{expected_unsigned:04X})")
    
    print("✅ Debug test completed")

    print("✅ Mixed mode test passed")

@cocotb.test()
async def test_clear_then_accumulate(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Clear Functionality After Accumulation ===")
    
    # Step 1: Initial accumulation operations
    print("Step 1: Initial accumulation operations")
    
    # First accumulation: 10 * 10 = 100 (clear mode start)
    print("First: 10 * 10 = 100 (clear_and_mult=1)")
    await send_data_2cycle_signed(dut, 10, 10, 1, 0)  # clear=1, unsigned
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Accumulator state: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    assert result_16bit == 100, f"First operation: expected 100, got {result_16bit}"
    
    # Second accumulation: 100 + (8 * 9) = 172 (accumulate mode)
    print("Second: 8 * 9 = 72 -> 100 + 72 = 172 (clear_and_mult=0)")
    await send_data_2cycle_signed(dut, 8, 9, 0, 0)  # clear=0, unsigned
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Accumulator state: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    assert result_16bit == 172, f"Second operation: expected 172, got {result_16bit}"
    
    # Third accumulation: 172 + (7 * 6) = 214 (accumulate mode)
    print("Third: 7 * 6 = 42 -> 172 + 42 = 214 (clear_and_mult=0)")
    await send_data_2cycle_signed(dut, 7, 6, 0, 0)  # clear=0, unsigned
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Accumulator state: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    assert result_16bit == 214, f"Third operation: expected 214, got {result_16bit}"
    
    # Step 2: Now test clear functionality
    print("\nStep 2: Testing clear functionality")
    print(f"Accumulator value before clear: {result_16bit}")
    
    # Use clear mode: should clear previous 214, only keep new multiplication result
    print("Clear operation: 5 * 4 = 20 (clear_and_mult=1, should ignore previous 214)")
    await send_data_2cycle_signed(dut, 5, 4, 1, 0)  # clear=1, unsigned
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Result after clear: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    # Key verification: result should be 20, not 214+20=234
    assert result_16bit == 20, f"Clear operation failed: expected 20, got {result_16bit} (if 234 means no clear)"
    
    # Step 3: Verify normal accumulation after clear
    print("\nStep 3: Verify normal accumulation after clear")
    
    # Accumulate on cleared base
    print("Accumulate after clear: 20 + (3 * 2) = 26 (clear_and_mult=0)")
    await send_data_2cycle_signed(dut, 3, 2, 0, 0)  # clear=0, unsigned
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Final result: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    assert result_16bit == 26, f"Accumulate after clear: expected 26, got {result_16bit}"
    
    print("✅ Clear functionality test passed!")

@cocotb.test()
async def test_clear_signed(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    dut.ena.value = 1
    await reset_dut(dut)
    
    print("=== Testing Clear Functionality in Signed Mode ===")
    
    # Step 1: Accumulation in signed mode
    print("Step 1: Signed mode accumulation")
    
    # First: 10 * 10 = 100 (clear start)
    print("First: 10 * 10 = 100 (signed, clear_and_mult=1)")
    await send_data_2cycle_signed(dut, 10, 10, 1, 1)  # clear=1, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Accumulator state: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    assert result_16bit == 100, f"First operation: expected 100, got {result_16bit}"
    
    # Second accumulation: 100 + [(-5) * 6] = 70
    print("Second: (-5) * 6 = -30 -> 100 - 30 = 70 (signed, clear_and_mult=0)")
    await send_data_2cycle_signed(dut, 251, 6, 0, 1)  # -5=251, clear=0, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Accumulator state: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    assert result_16bit == 70, f"Second operation: expected 70, got {result_16bit}"
    
    # Step 2: Clear in signed mode
    print("\nStep 2: Signed mode clear test")
    print(f"Accumulator value before clear: {result_16bit}")
    
    # Use clear mode, should clear previous 70
    print("Clear operation: (-3) * (-4) = 12 (signed, clear_and_mult=1)")
    await send_data_2cycle_signed(dut, 253, 252, 1, 1)  # -3=253, -4=252, clear=1, signed
    await wait_mac_pipeline(dut)
    
    result_16bit, overflow, ready = await read_full_result_2cycle(dut)
    print(f"Result after clear: {result_16bit} (0x{result_16bit:04X}), overflow={overflow}")
    
    # Verification: result should be 12, not 70+12=82
    assert result_16bit == 12, f"Signed clear failed: expected 12, got {result_16bit}"
    
    print("✅ Signed mode clear functionality test passed!")

    print("✅ Debug test completed") 

# ================= Additional randomized tests per new plan =================

@cocotb.test()
async def test_protocol_basic_random_unsigned(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.ena.value = 1
    await reset_dut(dut)

    import random
    random.seed(TEST_SEED)
    print(f"[RAND] test_protocol_basic_random_unsigned SEED={TEST_SEED} ITER={TEST_ITER}")

    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        await send_data_2cycle_signed(dut, a, b, 1, 0)  # clear=1, unsigned
        await wait_mac_pipeline(dut)
        rtl_result, rtl_overflow, _ = await read_full_result_2cycle(dut)

        expected = (a * b) & 0xFFFF
        assert rtl_result == expected, f"[BASIC UNSIGNED] iter={i} a={a} b={b} exp={expected} got={rtl_result}"
        assert rtl_overflow == 0, f"[BASIC UNSIGNED] iter={i} overflow unexpected: {rtl_overflow}"

@cocotb.test()
async def test_mode_switch_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.ena.value = 1
    await reset_dut(dut)

    import random
    random.seed(TEST_SEED)
    print(f"[RAND] test_mode_switch_random SEED={TEST_SEED} ITER={TEST_ITER}")

    acc17 = 0
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        signed_mode = 1 if random.random() < 0.5 else 0
        clear = 1 if (random.random() < 0.15 or i == 0) else 0

        await send_data_2cycle_signed(dut, a, b, clear, signed_mode)
        await wait_mac_pipeline(dut)
        rtl_result, rtl_overflow, _ = await read_full_result_2cycle(dut)

        acc17, mdl_result, mdl_overflow = mac_step_model(acc17, a, b, clear, signed_mode)

        assert rtl_result == mdl_result, (
            f"[MODE] iter={i} mode={'S' if signed_mode else 'U'} a={to_signed_8bit(a) if signed_mode else a} "
            f"b={to_signed_8bit(b) if signed_mode else b} clear={clear} expected={to_signed_16bit(mdl_result) if signed_mode else mdl_result} got={to_signed_16bit(rtl_result) if signed_mode else rtl_result}")
        assert rtl_overflow == mdl_overflow, (
            f"[MODE] iter={i} mode={'S' if signed_mode else 'U'} overflow_expected={mdl_overflow} overflow_got={rtl_overflow}")

@cocotb.test()
async def test_output_protocol_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.ena.value = 1
    await reset_dut(dut)

    import random
    random.seed(TEST_SEED)
    print(f"[RAND] test_output_protocol_random SEED={TEST_SEED} ITER={TEST_ITER}")

    acc17 = 0
    for i in range(TEST_ITER):
        a = random.randrange(0, 256)
        b = random.randrange(0, 256)
        signed_mode = 1 if random.random() < 0.5 else 0
        clear = 1 if (random.random() < 0.15 or i == 0) else 0

        await send_data_2cycle_signed(dut, a, b, clear, signed_mode)
        await wait_mac_pipeline(dut)

        # Read two consecutive cycles without assuming order
        first, ov1, _ = read_result_2cycle(dut)
        await RisingEdge(dut.clk)
        second, ov2, _ = read_result_2cycle(dut)

        acc17, mdl_result, mdl_overflow = mac_step_model(acc17, a, b, clear, signed_mode)
        low = mdl_result & 0xFF
        high = (mdl_result >> 8) & 0xFF

        assert sorted([first, second]) == sorted([low, high]), (
            f"[OUT] iter={i} bytes mismatch: got ({first:02X},{second:02X}) expected any order of ({low:02X},{high:02X})")
        # Overflow should be consistent on both cycles
        assert ov1 == mdl_overflow and ov2 == mdl_overflow, (
            f"[OUT] iter={i} overflow mismatch: ({ov1},{ov2}) expected {mdl_overflow}")

@cocotb.test()
async def test_burst_back_to_back_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.ena.value = 1
    await reset_dut(dut)

    import random
    random.seed(TEST_SEED)
    print(f"[RAND] test_burst_back_to_back_random SEED={TEST_SEED} ITER={TEST_ITER}")

    acc17 = 0
    for i in range(TEST_ITER):
        burst_len = 1 + (random.randrange(0, 5))  # 1..5
        for j in range(burst_len):
            a = random.randrange(0, 256)
            b = random.randrange(0, 256)
            signed_mode = 1 if random.random() < 0.5 else 0
            clear = 1 if (j == 0 or random.random() < 0.1) else 0

            await send_data_2cycle_signed(dut, a, b, clear, signed_mode)
            await wait_mac_pipeline(dut)
            rtl_result, rtl_overflow, _ = await read_full_result_2cycle(dut)

            acc17, mdl_result, mdl_overflow = mac_step_model(acc17, a, b, clear, signed_mode)
            assert rtl_result == mdl_result, f"[BURST] iter={i} step={j} exp={mdl_result} got={rtl_result}"
            assert rtl_overflow == mdl_overflow, f"[BURST] iter={i} step={j} ov_exp={mdl_overflow} ov_got={rtl_overflow}"

@cocotb.test()
async def test_overflow_boundary_random(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.ena.value = 1
    await reset_dut(dut)

    import random
    random.seed(TEST_SEED)
    print(f"[RAND] test_overflow_boundary_random SEED={TEST_SEED} ITER={TEST_ITER}")

    acc17 = 0
    edge_vals = [0, 1, 2, 254, 255, 127, 128]
    for i in range(TEST_ITER):
        # Bias sampling towards edges 50% of the time
        def samp():
            return random.choice(edge_vals) if (random.random() < 0.5) else random.randrange(0, 256)

        a = samp()
        b = samp()
        signed_mode = 1 if random.random() < 0.5 else 0
        clear = 1 if (random.random() < 0.2 or i == 0) else 0

        await send_data_2cycle_signed(dut, a, b, clear, signed_mode)
        await wait_mac_pipeline(dut)
        rtl_result, rtl_overflow, _ = await read_full_result_2cycle(dut)

        acc17, mdl_result, mdl_overflow = mac_step_model(acc17, a, b, clear, signed_mode)
        assert rtl_result == mdl_result, f"[EDGE] iter={i} mode={'S' if signed_mode else 'U'} a={a} b={b} exp={mdl_result} got={rtl_result}"
        assert rtl_overflow == mdl_overflow, f"[EDGE] iter={i} ov_exp={mdl_overflow} ov_got={rtl_overflow}"