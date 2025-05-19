/*
 * Copyright (c) 2024 Bryan Kuang
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ARandomNam_example (
    input  wire [7:0] ui_in,    // Dedicated inputs - used for base count
    output wire [7:0] uo_out,   // Dedicated outputs - counter output
    input  wire [7:0] uio_in,   // IOs: Input path - not used
    output wire [7:0] uio_out,  // IOs: Output path - not used
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // Control signals derived from inputs
  wire load = uio_in[0];        // Load signal from first bit of uio_in
  wire out_enable = uio_in[1];  // Output enable from second bit of uio_in
  
  // Instantiate the 8-bit counter
  counter_8bit counter (
    .clk(clk),
    .rst_n(rst_n),
    .load(load),
    .out_en(out_enable),
    .base_count(ui_in),  // Use ui_in as the base count to load
    .count_out(uo_out)   // Connect counter output to uo_out
  );
  
  // Set all bidirectional pins to inputs (not used)
  assign uio_out = 8'b0;
  assign uio_oe = 8'b0;

  // List unused inputs to prevent warnings
  wire _unused = &{ena, uio_in[7:2], 1'b0};

endmodule
