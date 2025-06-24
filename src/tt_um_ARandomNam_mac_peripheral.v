/*
 * Copyright (c) 2024 Bryan Kuang
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ARandomNam_mac_peripheral (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // All output pins must be assigned. If not used, assign to 0.
  
  // MAC inputs mapping:
  // ui_in[7:0] = Data_A[7:0] (8-bit input A)
  // uio_in[6:0] = Data_B[6:0] (7-bit input B, bit 7 unused for simplicity) 
  // uio_in[7] = Clear_and_Mult control signal
  
  wire [7:0] data_a = ui_in[7:0];
  wire [7:0] data_b = {1'b0, uio_in[6:0]}; // Use only 7 bits for B, MSB = 0
  wire clear_and_mult = uio_in[7]; // Use bit 7 of uio_in as control
  
  wire [15:0] mac_output;
  wire overflow;
  
  // MAC module instantiation
  MAC_simple mac_inst (
    .clk(clk),
    .rst(~rst_n),  // Convert active-low reset to active-high
    .Data_A(data_a),
    .Data_B(data_b),
    .Clear_and_Mult(clear_and_mult),
    .Output_2(mac_output),
    .Output_1(overflow)
  );
  
  // Output mapping:
  // uo_out[7:0] = MAC output lower 8 bits
  // uio_out[7:0] = MAC output upper 8 bits (with overflow in bit 7)
  assign uo_out[7:0] = mac_output[7:0];   // Lower 8 bits of MAC result
  
  // Configure bidirectional pins as outputs for upper result bits
  assign uio_oe[7:0] = 8'b11111111;       // All uio pins as outputs
  assign uio_out[7:0] = {overflow, mac_output[14:8]}; // Overflow flag + upper 7 bits

  // Suppress unused signal warnings
  wire _unused = &{ena, mac_output[15], 1'b0};

endmodule 