`timescale 1ns / 1ps

module tb_mac_simple;
    // Clock and reset signals
    reg clk;
    reg rst;
    
    // MAC input signals
    reg Clear_and_Mult;
    reg [7:0] Data_A;
    reg [7:0] Data_B;
    
    // MAC output signals
    wire Output_1;
    wire [15:0] Output_2;

    // Instantiate simplified MAC module
    MAC_simple dut (
        .clk(clk),
        .rst(rst),
        .Clear_and_Mult(Clear_and_Mult),
        .Data_A(Data_A),
        .Data_B(Data_B),
        .Output_1(Output_1),
        .Output_2(Output_2)
    );

    // Initialize signals (but don't run any tests)
    initial begin
        clk = 0;
        rst = 0;
        Clear_and_Mult = 0;
        Data_A = 0;
        Data_B = 0;
    end

    // Generate VCD file for waveform viewing
    initial begin
        $dumpfile("mac_simple_test.vcd");
        $dumpvars(0, tb_mac_simple);
    end

endmodule 