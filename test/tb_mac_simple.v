`timescale 1ns / 1ps

module tb_mac_simple;
    // Clock and reset signals
    reg clk;
    reg rst_n;
    
    // TinyTapeout interface signals
    reg [7:0] ui_in;     // Dedicated inputs - Data_A
    wire [7:0] uo_out;   // Dedicated outputs - Result[7:0]
    reg [7:0] uio_in;    // Bidirectional inputs - Data_B[6:0] + Clear_and_Mult
    wire [7:0] uio_out;  // Bidirectional outputs - Result[15:8] + Overflow
    wire [7:0] uio_oe;   // Bidirectional enable
    reg ena;             // Enable signal

    // Instantiate TinyTapeout top module
    tt_um_ARandomNam_mac_peripheral_modular dut (
        .ui_in(ui_in),
        .uo_out(uo_out),
        .uio_in(uio_in),
        .uio_out(uio_out),
        .uio_oe(uio_oe),
        .ena(ena),
        .clk(clk),
        .rst_n(rst_n)
    );

    // Initialize signals (but don't run any tests)
    initial begin
        clk = 0;
        rst_n = 1;
        ena = 1;
        ui_in = 0;
        uio_in = 0;
    end

    // Generate VCD file for waveform viewing
    initial begin
        $dumpfile("mac_simple_test.vcd");
        $dumpvars(0, tb_mac_simple);
    end

endmodule 