/*
 * Copyright (c) 2024 Bryan Kuang
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_BryanKuang_mac_peripheral (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Nibble interface pin mapping
  wire [3:0] data_a_nibble = ui_in[3:0];             // Data_A nibble input
  wire [3:0] data_b_nibble = ui_in[7:4];             // Data_B nibble input
  wire clear_and_mult = uio_in[0];                   // Clear and multiply control
  wire enable_nibble = uio_in[1];                    // Enable nibble interface
  
  // Nibble interface outputs
  wire [3:0] result_low_nibble;
  wire [3:0] result_high_nibble;
  wire overflow_nibble;
  wire data_ready;
  
  // MAC interface signals
  wire [7:0] mac_data_a, mac_data_b;
  wire mac_clear_and_mult;
  wire [15:0] mac_result;
  wire mac_overflow;
  
  // Internal MAC signals
  wire input_changed;
  wire [7:0] reg_A, reg_B;
  wire reg_Clear_and_Mult;
  wire reg_valid;
  wire [7:0] pipe_A, pipe_B;
  wire pipe_Clear_and_Mult;
  wire pipe_valid;
  wire [15:0] mult_result;
  wire [16:0] accumulator_value;
  
  // Nibble interface module
  nibble_interface nibble_if (
    .clk(clk),
    .rst(~rst_n),
    .enable(enable_nibble),
    .data_a_nibble_in(data_a_nibble),
    .data_b_nibble_in(data_b_nibble),
    .clear_and_mult_in(clear_and_mult),
    .result_low_nibble_out(result_low_nibble),
    .result_high_nibble_out(result_high_nibble),
    .overflow_out(overflow_nibble),
    .data_ready(data_ready),
    .mac_data_a(mac_data_a),
    .mac_data_b(mac_data_b),
    .mac_clear_and_mult(mac_clear_and_mult),
    .mac_result(mac_result),
    .mac_overflow(mac_overflow)
  );
  
  // Input change detection
  change_detector change_det (
    .clk(clk),
    .rst(~rst_n),
    .data_a(mac_data_a),
    .data_b(mac_data_b),
    .clear_mult(mac_clear_and_mult),
    .input_changed(input_changed)
  );
  
  // Stage 1: Input registers
  input_registers input_regs (
    .clk(clk),
    .rst(~rst_n),
    .data_a_in(mac_data_a),
    .data_b_in(mac_data_b),
    .clear_mult_in(mac_clear_and_mult),
    .valid_in(input_changed),
    .data_a_out(reg_A),
    .data_b_out(reg_B),
    .clear_mult_out(reg_Clear_and_Mult),
    .valid_out(reg_valid)
  );
  
  // Stage 2: Pipeline registers
  pipeline_registers pipe_regs (
    .clk(clk),
    .rst(~rst_n),
    .data_a_in(reg_A),
    .data_b_in(reg_B),
    .clear_mult_in(reg_Clear_and_Mult),
    .valid_in(reg_valid),
    .data_a_out(pipe_A),
    .data_b_out(pipe_B),
    .clear_mult_out(pipe_Clear_and_Mult),
    .valid_out(pipe_valid)
  );
  
  // 8x8 Multiplier
  TC_Mul #(.BIT_WIDTH(8)) multiplier (
    .in0(pipe_A),
    .in1(pipe_B),
    .out0(mult_result[7:0]),
    .out1(mult_result[15:8])
  );
  
  // 17-bit accumulator
  accumulator_17bit accumulator (
    .clk(clk),
    .rst(~rst_n),
    .mult_result(mult_result),
    .clear_mode(pipe_Clear_and_Mult),
    .valid(pipe_valid),
    .accumulator_value(accumulator_value),
    .result_out(mac_result),
    .overflow_out(mac_overflow)
  );
  
  // Output mapping
  assign uo_out[3:0] = result_low_nibble;            // Result low nibble
  assign uo_out[7:4] = result_high_nibble;           // Result high nibble
  assign uio_oe[7:0] = 8'b11111100;                  // uio[7:2] as outputs, uio[1:0] as inputs
  assign uio_out[0] = overflow_nibble;               // Overflow flag
  assign uio_out[1] = data_ready;                    // Data ready flag
  assign uio_out[7:2] = 6'b0;                        // Unused outputs

  // Suppress unused signal warnings
  wire _unused = &{ena, uio_in[7:2], accumulator_value, 1'b0};

endmodule 