/*
 * Copyright (c) 2024 Bryan Kuang
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module counter_8bit (
    input  wire        clk,       // Clock input
    input  wire        rst_n,     // Active-low reset
    input  wire        load,      // Load enable signal
    input  wire        out_en,    // Output enable for tri-state
    input  wire [7:0]  base_count, // Base count to load
    output wire [7:0]  count_out  // Counter output (tri-state)
);

    // Internal counter register
    reg [7:0] count_reg;
    
    // Synchronous counter logic with load functionality
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset counter to 0
            count_reg <= 8'h00;
        end else if (load) begin
            // Load the base count value
            count_reg <= base_count;
        end else begin
            // Increment the counter
            count_reg <= count_reg + 1'b1;
        end
    end
    
    // Tri-state output control
    // When out_en is high, output the counter value
    // When out_en is low, output high-impedance (Z)
    assign count_out = out_en ? count_reg : 8'bz;

endmodule