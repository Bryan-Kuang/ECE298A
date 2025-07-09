`timescale 1ns / 1ps

module tb_mac_nibble;
    reg clk;
    reg rst_n;
    
    reg [7:0] ui_in;
    wire [7:0] uo_out;
    reg [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;
    reg ena;

    // TinyTapeout top module with nibble interface
    tt_um_BryanKuang_mac_peripheral dut (
        .ui_in(ui_in),
        .uo_out(uo_out),
        .uio_in(uio_in),
        .uio_out(uio_out),
        .uio_oe(uio_oe),
        .ena(ena),
        .clk(clk),
        .rst_n(rst_n)
    );

    // Clock generation
    always #5 clk = ~clk;

    initial begin
        // Initialize signals
        clk = 0;
        rst_n = 1;
        ena = 1;
        ui_in = 0;
        uio_in = 0;

        // Reset
        rst_n = 0;
        repeat(2) @(posedge clk);
        rst_n = 1;
        repeat(2) @(posedge clk);

        $display("=== Testing Nibble Interface ===");

        // Test 1: Basic multiplication 5 * 6 = 30
        $display("Test 1: 5 * 6 = 30");
        // First cycle: send lower nibbles
        ui_in[3:0] = 4'd5;  // data_a lower
        ui_in[7:4] = 4'd6;  // data_b lower
        uio_in[0] = 1'b1;   // clear_mult
        uio_in[1] = 1'b1;   // enable
        @(posedge clk);
        
        // Second cycle: send upper nibbles
        ui_in[3:0] = 4'd0;  // data_a upper
        ui_in[7:4] = 4'd0;  // data_b upper
        uio_in[0] = 1'b1;   // clear_mult
        uio_in[1] = 1'b1;   // enable
        @(posedge clk);
        
        // Disable and wait for MAC pipeline
        uio_in[1] = 1'b0;
        repeat(6) @(posedge clk);
        
        // Test 2: Accumulation 30 + (3 * 4) = 42
        $display("Test 2: 30 + (3 * 4) = 42");
        // First cycle: send lower nibbles
        ui_in[3:0] = 4'd3;  // data_a lower
        ui_in[7:4] = 4'd4;  // data_b lower
        uio_in[0] = 1'b0;   // accumulate mode
        uio_in[1] = 1'b1;   // enable
        @(posedge clk);
        
        // Second cycle: send upper nibbles
        ui_in[3:0] = 4'd0;  // data_a upper
        ui_in[7:4] = 4'd0;  // data_b upper
        uio_in[0] = 1'b0;   // accumulate mode
        uio_in[1] = 1'b1;   // enable
        @(posedge clk);
        
        // Disable and wait for MAC pipeline
        uio_in[1] = 1'b0;
        repeat(6) @(posedge clk);
        
        // Test 3: Large values 255 * 127 = 32385
        $display("Test 3: 255 * 127 = 32385");
        // First cycle: send lower nibbles
        ui_in[3:0] = 4'hF;  // 255 lower (15)
        ui_in[7:4] = 4'hF;  // 127 lower (15)
        uio_in[0] = 1'b1;   // clear mode
        uio_in[1] = 1'b1;   // enable
        @(posedge clk);
        
        // Second cycle: send upper nibbles
        ui_in[3:0] = 4'hF;  // 255 upper (15)
        ui_in[7:4] = 4'h7;  // 127 upper (7)
        uio_in[0] = 1'b1;   // clear mode
        uio_in[1] = 1'b1;   // enable
        @(posedge clk);
        
        // Disable and wait for MAC pipeline
        uio_in[1] = 1'b0;
        repeat(6) @(posedge clk);

        $display("=== Nibble Interface Test Complete ===");
        // Don't call $finish - let cocotb handle test completion
    end

    // Generate VCD for waveform viewing
    initial begin
        $dumpfile("mac_nibble_test.vcd");
        $dumpvars(0, tb_mac_nibble);
    end

endmodule 