module nibble_interface (
    input wire clk,
    input wire rst,
    input wire enable,
    
    // 4-bit nibble inputs
    input wire [3:0] data_a_nibble_in,
    input wire [3:0] data_b_nibble_in,
    input wire clear_and_mult_in,
    
    // 4-bit nibble outputs
    output wire [3:0] result_low_nibble_out,
    output wire [3:0] result_high_nibble_out,
    output wire overflow_out,
    output wire data_ready,
    
    // MAC interface
    output wire [7:0] mac_data_a,
    output wire [7:0] mac_data_b,
    output wire mac_clear_and_mult,
    input wire [15:0] mac_result,
    input wire mac_overflow
);

    // State machine for 2-cycle nibble protocol
    reg cycle_state;  // 0 = first cycle (lower nibble), 1 = second cycle (upper nibble)
    reg [3:0] data_a_lower, data_b_lower;
    reg clear_mult_stored;
    reg [7:0] assembled_data_a, assembled_data_b;
    reg assembled_clear_mult;
    reg data_valid;
    
    // Output registers for result nibbles
    reg [7:0] result_low_reg, result_high_reg;
    reg overflow_reg;
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            cycle_state <= 1'b0;
            data_a_lower <= 4'b0;
            data_b_lower <= 4'b0;
            clear_mult_stored <= 1'b0;
            assembled_data_a <= 8'b0;
            assembled_data_b <= 8'b0;
            assembled_clear_mult <= 1'b0;
            data_valid <= 1'b0;
            result_low_reg <= 8'b0;
            result_high_reg <= 8'b0;
            overflow_reg <= 1'b0;
        end else if (enable) begin
            if (cycle_state == 1'b0) begin
                // First cycle: store lower nibbles
                data_a_lower <= data_a_nibble_in;
                data_b_lower <= data_b_nibble_in;
                clear_mult_stored <= clear_and_mult_in;
                data_valid <= 1'b0;
                cycle_state <= 1'b1;
            end else begin
                // Second cycle: combine with upper nibbles and output to MAC
                assembled_data_a <= {data_a_nibble_in, data_a_lower};
                assembled_data_b <= {data_b_nibble_in, data_b_lower};
                assembled_clear_mult <= clear_mult_stored;
                data_valid <= 1'b1;
                cycle_state <= 1'b0;
            end
        end else begin
            data_valid <= 1'b0;
        end
        
        // Always capture MAC results
        if (mac_result != 16'b0 || mac_overflow) begin
            result_low_reg <= mac_result[7:0];
            result_high_reg <= mac_result[15:8];
            overflow_reg <= mac_overflow;
        end
    end
    
    // Connect to MAC
    assign mac_data_a = assembled_data_a;
    assign mac_data_b = assembled_data_b;
    assign mac_clear_and_mult = assembled_clear_mult && data_valid;
    
    // Output nibble selection based on cycle
    assign result_low_nibble_out = cycle_state ? result_low_reg[7:4] : result_low_reg[3:0];
    assign result_high_nibble_out = cycle_state ? result_high_reg[7:4] : result_high_reg[3:0];
    assign overflow_out = overflow_reg;
    assign data_ready = (cycle_state == 1'b0) && !enable;  // Ready for new data after second cycle

endmodule 