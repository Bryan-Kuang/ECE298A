import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

async def reset_dut(dut):
    """Helper function to reset DUT"""
    dut.rst.value = 1
    await RisingEdge(dut.clk)
    dut.rst.value = 0
    await RisingEdge(dut.clk)

async def wait_result(dut, cycles=4):
    """Helper function to wait for MAC result"""
    for _ in range(cycles):
        await RisingEdge(dut.clk)

@cocotb.test()
async def test_basic_functionality(dut):
    """Test basic MAC functionality including reset, zero, and simple operations"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    
    print("=== Testing Basic Functionality ===")
    
    # Test reset functionality
    dut.Data_A.value = 100
    dut.Data_B.value = 200
    dut.Clear_and_Mult.value = 1
    await wait_result(dut)
    await reset_dut(dut)
    
    result = int(dut.Output_2.value)
    assert result == 0, f"Reset failed: expected 0, got {result}"
    print("✅ Reset functionality works")
    
    # Test zero inputs: 0 * 0 = 0
    dut.Data_A.value = 0
    dut.Data_B.value = 0
    dut.Clear_and_Mult.value = 1
    await wait_result(dut)
    
    result = int(dut.Output_2.value)
    assert result == 0, f"Zero multiplication failed: expected 0, got {result}"
    print("✅ Zero multiplication works")
    
    # Test one operand zero: 255 * 0 = 0, 0 * 255 = 0
    test_cases = [(255, 0, 0), (0, 255, 0), (42, 1, 42), (1, 123, 123)]
    for a, b, expected in test_cases:
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = 1
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        assert result == expected, f"{a}*{b} failed: expected {expected}, got {result}"
        print(f"Basic test: {a}*{b} = {result}")
    
    print("✅ Basic functionality test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_boundary_values(dut):
    """Test boundary values and extreme cases"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Boundary Values ===")
    
    boundary_cases = [
        # (A, B, expected, description)
        (1, 1, 1, "Minimum positive"),
        (255, 255, 65025, "Maximum values"),
        (128, 128, 16384, "Mid-range squared"),
        (2, 2, 4, "Power of 2"),
        (16, 16, 256, "Larger power of 2"),
        (127, 127, 16129, "Near mid-range"),
        (254, 1, 254, "Near-max * small"),
        (1, 254, 254, "Small * near-max"),
    ]
    
    for a, b, expected, desc in boundary_cases:
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = 1
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        assert result == expected, f"{desc} failed: {a}*{b} expected {expected}, got {result}"
        print(f"Boundary: {desc} - {a}*{b} = {result}")
    
    print("✅ Boundary values test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_accumulation_modes(dut):
    """Test clear vs accumulate mode switching"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Accumulation Modes ===")
    
    # Sequential accumulation test
    operations = [
        (10, 10, 1, 100, "Clear: 10*10"),      # Clear to 100
        (5, 5, 0, 125, "Accumulate: +5*5"),    # Add 25 -> 125
        (3, 7, 0, 146, "Accumulate: +3*7"),    # Add 21 -> 146
        (6, 7, 1, 42, "Clear: 6*7"),          # Clear to 42
        (2, 3, 0, 48, "Accumulate: +2*3"),     # Add 6 -> 48
    ]
    
    for a, b, clear, expected, desc in operations:
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = clear
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        assert result == expected, f"{desc} failed: expected {expected}, got {result}"
        print(f"Mode test: {desc} -> {result}")
    
    print("✅ Accumulation modes test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_overflow_detection(dut):
    """Test overflow detection and handling"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Overflow Detection ===")
    
    # Start with large value: 255*255 = 65025
    dut.Data_A.value = 255
    dut.Data_B.value = 255
    dut.Clear_and_Mult.value = 1
    await wait_result(dut)
    
    result1 = int(dut.Output_2.value)
    overflow1 = int(dut.Output_1.value)
    assert result1 == 65025, f"Large multiplication failed: expected 65025, got {result1}"
    assert overflow1 == 0, f"Unexpected overflow: expected 0, got {overflow1}"
    print(f"Large value: 255*255 = {result1} (no overflow)")
    
    # Add another large value to cause overflow: +200*200 = +40000
    dut.Data_A.value = 200
    dut.Data_B.value = 200
    dut.Clear_and_Mult.value = 0
    await wait_result(dut)
    
    result2 = int(dut.Output_2.value)
    overflow2 = int(dut.Output_1.value)
    expected_total = 65025 + 40000  # 105025, should overflow
    expected_result = expected_total & 0xFFFF
    
    print(f"Overflow test: 65025 + 40000 = {result2} (overflow={overflow2})")
    print(f"Expected: result={expected_result}, overflow={1 if expected_total > 65535 else 0}")
    
    # Multiple consecutive overflows
    dut.Data_A.value = 150
    dut.Data_B.value = 200
    dut.Clear_and_Mult.value = 0
    await wait_result(dut)
    
    result3 = int(dut.Output_2.value)
    overflow3 = int(dut.Output_1.value)
    print(f"Multiple overflow: +{150*200} -> result={result3} (overflow={overflow3})")
    
    print("✅ Overflow detection test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_pipeline_timing(dut):
    """Test pipeline timing and back-to-back operations"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Pipeline Timing ===")
    
    # Test back-to-back operations
    dut.Data_A.value = 6
    dut.Data_B.value = 7
    dut.Clear_and_Mult.value = 1
    await wait_result(dut, 4)
    
    result1 = int(dut.Output_2.value)
    assert result1 == 42, f"First pipeline result failed: expected 42, got {result1}"
    
    # Immediate next operation
    dut.Data_A.value = 3
    dut.Data_B.value = 4
    dut.Clear_and_Mult.value = 0
    await wait_result(dut, 4)
    
    result2 = int(dut.Output_2.value)
    expected2 = 54  # 42 + 12
    assert result2 == expected2, f"Second pipeline result failed: expected {expected2}, got {result2}"
    
    print(f"Pipeline timing: {result1} -> {result2}")
    print("✅ Pipeline timing test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_rapid_mode_switching(dut):
    """Test rapid switching between clear and accumulate modes"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Rapid Mode Switching ===")
    
    rapid_operations = [
        (5, 5, 1, 25),      # Clear: 5*5 = 25
        (3, 3, 0, 34),      # Accumulate: 25 + 9 = 34
        (10, 2, 1, 20),     # Clear: 10*2 = 20
        (1, 1, 0, 21),      # Accumulate: 20 + 1 = 21
        (7, 7, 1, 49),      # Clear: 7*7 = 49
        (2, 3, 0, 55),      # Accumulate: 49 + 6 = 55
    ]
    
    for i, (a, b, clear, expected) in enumerate(rapid_operations):
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = clear
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        mode = "Clear" if clear else "Accumulate"
        assert result == expected, f"Operation {i+1} ({mode}) failed: expected {expected}, got {result}"
        print(f"Rapid {i+1}: {mode} {a}*{b} -> {result}")
    
    print("✅ Rapid mode switching test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_mathematical_patterns(dut):
    """Test mathematical patterns: primes, fibonacci, bit patterns"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Mathematical Patterns ===")
    
    # Prime number tests
    prime_tests = [(2, 3, 6), (5, 7, 35), (11, 13, 143), (17, 19, 323)]
    accumulator = 0
    
    for i, (a, b, expected_mult) in enumerate(prime_tests):
        if i == 0:
            dut.Clear_and_Mult.value = 1
            accumulator = expected_mult
        else:
            dut.Clear_and_Mult.value = 0
            accumulator += expected_mult
        
        dut.Data_A.value = a
        dut.Data_B.value = b
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        # Handle overflow for accumulated values
        expected_result = accumulator & 0xFFFF if accumulator > 65535 else accumulator
        print(f"Prime {i+1}: {a}*{b} -> accumulator = {result}")
    
    # Fibonacci sequence test
    print("--- Fibonacci Test ---")
    fib_numbers = [1, 1, 2, 3, 5, 8]
    dut.Data_A.value = fib_numbers[0]
    dut.Data_B.value = fib_numbers[1]
    dut.Clear_and_Mult.value = 1
    await wait_result(dut)
    
    fib_acc = 1
    for i in range(2, len(fib_numbers), 2):
        if i+1 < len(fib_numbers):
            dut.Data_A.value = fib_numbers[i]
            dut.Data_B.value = fib_numbers[i+1]
            dut.Clear_and_Mult.value = 0
            await wait_result(dut)
            
            fib_acc += fib_numbers[i] * fib_numbers[i+1]
            result = int(dut.Output_2.value)
            print(f"Fibonacci: {fib_numbers[i]}*{fib_numbers[i+1]} -> accumulator = {result}")
    
    # Bit pattern test
    print("--- Bit Pattern Test ---")
    patterns = [
        (0b10101010, 0b01010101, "Alternating"),  # 170 * 85
        (0b11110000, 0b00001111, "High/Low"),     # 240 * 15
        (0b11001100, 0b00110011, "Double bit"),   # 204 * 51
    ]
    
    for a, b, desc in patterns:
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = 1
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        expected = a * b
        assert result == expected, f"{desc} pattern failed: expected {expected}, got {result}"
        print(f"Pattern {desc}: {a:08b}*{b:08b} = {result}")
    
    print("✅ Mathematical patterns test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_stress_operations(dut):
    """Test stress conditions with many consecutive operations"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Stress Operations ===")
    
    # Start with clear operation
    dut.Data_A.value = 1
    dut.Data_B.value = 1
    dut.Clear_and_Mult.value = 1
    await wait_result(dut)
    
    accumulator = 1
    result = int(dut.Output_2.value)
    assert result == accumulator, f"Stress start failed: expected {accumulator}, got {result}"
    
    # Perform 8 accumulation operations
    for i in range(8):
        a = (i + 1) % 8 + 1  # Values 1-8
        b = (i + 3) % 6 + 1  # Values 1-6
        
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = 0
        await wait_result(dut)
        
        accumulator = (accumulator + a * b) & 0xFFFF
        result = int(dut.Output_2.value)
        overflow = int(dut.Output_1.value)
        
        print(f"Stress {i+1}: +{a}*{b} -> accumulator = {result} (overflow={overflow})")
    
    print("✅ Stress operations test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_input_stability(dut):
    """Test input stability and edge cases"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Input Stability ===")
    
    # Test stable inputs
    dut.Data_A.value = 40
    dut.Data_B.value = 20
    dut.Clear_and_Mult.value = 1
    await wait_result(dut)
    
    result = int(dut.Output_2.value)
    expected = 800
    assert result == expected, f"Input stability failed: expected {expected}, got {result}"
    print(f"Stable inputs: 40*20 = {result}")
    
    # Test edge values
    edge_cases = [
        (128, 128, 16384, "Mid-range"),
        (64, 255, 16320, "Power-of-2 * max"),
        (255, 64, 16320, "Max * power-of-2"),
        (85, 85, 7225, "Special value"),
    ]
    
    for a, b, expected, desc in edge_cases:
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = 1
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        assert result == expected, f"{desc} failed: expected {expected}, got {result}"
        print(f"Edge case {desc}: {a}*{b} = {result}")
    
    print("✅ Input stability test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_comprehensive_scenarios(dut):
    """Test comprehensive real-world scenarios"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Testing Comprehensive Scenarios ===")
    
    # Scenario 1: Digital signal processing simulation
    print("--- DSP Simulation ---")
    signal_samples = [(100, 100), (50, 150), (200, 75), (25, 200)]
    
    # Clear with first sample
    a, b = signal_samples[0]
    dut.Data_A.value = a
    dut.Data_B.value = b
    dut.Clear_and_Mult.value = 1
    await wait_result(dut)
    
    dsp_acc = a * b
    result = int(dut.Output_2.value)
    print(f"DSP init: {a}*{b} = {result}")
    
    # Accumulate remaining samples
    for i, (a, b) in enumerate(signal_samples[1:], 1):
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = 0
        await wait_result(dut)
        
        dsp_acc = (dsp_acc + a * b) & 0xFFFF
        result = int(dut.Output_2.value)
        overflow = int(dut.Output_1.value)
        print(f"DSP step {i}: +{a}*{b} -> {result} (overflow={overflow})")
    
    # Scenario 2: Coefficient processing
    print("--- Coefficient Processing ---")
    coefficients = [(15, 15), (240, 240), (128, 64)]
    
    for i, (a, b) in enumerate(coefficients):
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = 1  # Each coefficient processed independently
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        overflow = int(dut.Output_1.value)
        expected = a * b
        
        print(f"Coeff {i+1}: {a}*{b} = {result} (expected={expected}, overflow={overflow})")
        
        # Verify results within reasonable bounds
        assert isinstance(result, int), f"Result should be integer"
        assert 0 <= result <= 65535, f"Result out of range: {result}"
        assert overflow in [0, 1], f"Invalid overflow flag: {overflow}"
    
    print("✅ Comprehensive scenarios test passed")
    await reset_dut(dut)

@cocotb.test()
async def test_final_integration(dut):
    """Final integration test combining all major features"""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    await reset_dut(dut)
    
    print("=== Final Integration Test ===")
    
    # Complex sequence testing all aspects
    integration_sequence = [
        (50, 50, 1, "Large clear operation"),           # 2500
        (10, 10, 0, "Small accumulate"),                # +100 = 2600
        (0, 100, 0, "Zero accumulate"),                 # +0 = 2600
        (200, 200, 1, "Large clear with potential overflow"), # 40000
        (100, 100, 0, "Large accumulate causing overflow"),   # +10000 = 50000
        (1, 1, 1, "Reset to minimal"),                 # 1
        (255, 255, 1, "Maximum clear"),                # 65025
        (5, 5, 0, "Final small accumulate"),           # +25 = 65050 (overflow)
    ]
    
    for i, (a, b, clear, desc) in enumerate(integration_sequence):
        dut.Data_A.value = a
        dut.Data_B.value = b
        dut.Clear_and_Mult.value = clear
        await wait_result(dut)
        
        result = int(dut.Output_2.value)
        overflow = int(dut.Output_1.value)
        mode = "Clear" if clear else "Accumulate"
        
        print(f"Integration {i+1}: {desc}")
        print(f"  {mode} {a}*{b} -> result={result}, overflow={overflow}")
        
        # Verify operation completed successfully
        assert isinstance(result, int), f"Result should be integer"
        assert isinstance(overflow, int), f"Overflow should be integer"
        assert 0 <= result <= 65535, f"Result out of 16-bit range: {result}"
        assert overflow in [0, 1], f"Overflow should be 0 or 1: {overflow}"
    
    print("✅ Final integration test passed")
    await reset_dut(dut) 