module accumulator_17bit (
    input wire clk,
    input wire rst,
    input wire [15:0] mult_result,
    input wire clear_mode,
    input wire valid,
    
    output reg [16:0] accumulator_value,
    output reg [15:0] result_out,
    output reg overflow_out
);

    wire [16:0] add_result;
    assign add_result = accumulator_value + {1'b0, mult_result};
    
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            accumulator_value <= 17'b0;
            result_out <= 16'b0;
            overflow_out <= 1'b0;
        end else if (valid) begin
            if (clear_mode) begin
                // Clear mode: set accumulator to current multiplication result
                accumulator_value <= {1'b0, mult_result};
                result_out <= mult_result;
                overflow_out <= 1'b0;  // Single multiplication won't overflow 16 bits
            end else begin
                // Accumulate mode: accumulator += current multiplication result
                accumulator_value <= add_result;
                result_out <= add_result[15:0];
                overflow_out <= add_result[16];  // Overflow flag
            end
        end
        // If valid is 0, keep current values unchanged
    end

endmodule 