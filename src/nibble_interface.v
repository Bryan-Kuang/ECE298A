module nibble_interface (
    input wire clk,
    input wire rst,
    input wire enable,
    
    // 8-bit data inputs (full byte, not nibbles)
    input wire [7:0] data_in,           // 8-bit data input (Data A in cycle 1, Data B in cycle 2)
    input wire clear_and_mult_in,       // MAC control signal (valid in cycle 1)
    
    // 8-bit data outputs (full byte, not nibbles)  
    output wire [7:0] data_out,         // 8-bit data output (low 8 bits in cycle 1, high 8 bits in cycle 2)
    output wire overflow_out,           // Overflow flag (valid in cycle 1)
    output wire data_ready,             // Ready signal
    
    // MAC interface
    output wire [7:0] mac_data_a,
    output wire [7:0] mac_data_b,
    output wire mac_clear_and_mult,
    input wire [15:0] mac_result,
    input wire mac_overflow
);

    // Input state machine for 2-cycle input protocol
    reg input_cycle_state;              // 0 = cycle 1 (Data A + control), 1 = cycle 2 (Data B)
    reg [7:0] stored_data_a;            // Store Data A from cycle 1
    reg stored_clear_mult;              // Store control signal from cycle 1
    reg [7:0] assembled_data_a;         // Complete Data A for MAC
    reg [7:0] assembled_data_b;         // Complete Data B for MAC
    reg assembled_clear_mult;           // Complete control signal for MAC
    
    // Output state machine for 2-cycle output protocol  
    reg output_cycle_state;             // 0 = cycle 1 (low 8 bits + overflow), 1 = cycle 2 (high 8 bits)
    reg [15:0] result_reg;              // Stored MAC result
    reg overflow_reg;                   // Stored overflow flag
    reg result_available;               // Flag indicating result is ready for output
    
    // Input protocol: 2-cycle input handling
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            input_cycle_state <= 1'b0;
            stored_data_a <= 8'b0;
            stored_clear_mult <= 1'b0;
            assembled_data_a <= 8'b0;
            assembled_data_b <= 8'b0;
            assembled_clear_mult <= 1'b0;
        end else begin
            if (enable) begin
                if (input_cycle_state == 1'b0) begin
                    // Cycle 1: Store Data A and control signal
                    stored_data_a <= data_in;
                    stored_clear_mult <= clear_and_mult_in;
                    input_cycle_state <= 1'b1;
                    // Mark that new input started, previous result becomes invalid
                    result_available <= 1'b0;
                end else begin
                    // Cycle 2: Combine with Data B and send to MAC
                    assembled_data_a <= stored_data_a;
                    assembled_data_b <= data_in;           // data_in is Data B in cycle 2
                    assembled_clear_mult <= stored_clear_mult;
                    input_cycle_state <= 1'b0;
                end
            end
        end
    end
    
    // Output protocol: Capture and cycle through result
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            output_cycle_state <= 1'b0;
            result_reg <= 16'b0;
            overflow_reg <= 1'b0;
            result_available <= 1'b0;
        end else begin
            // Always capture the latest MAC result
            result_reg <= mac_result;
            overflow_reg <= mac_overflow;
            
            // Manage output cycling when not actively inputting
            if (!enable) begin
                if (!result_available) begin
                    result_available <= 1'b1;
                    output_cycle_state <= 1'b0;    // Start from cycle 1 (low 8 bits)
                end else begin
                    // Advance output cycle to show different parts of result
                    output_cycle_state <= ~output_cycle_state;
                end
            end else begin
                // Reset availability when new input starts
                if (input_cycle_state == 1'b0) begin
                    result_available <= 1'b0;
                end
            end
        end
    end
    
    // Connect to MAC
    assign mac_data_a = assembled_data_a;
    assign mac_data_b = assembled_data_b;
    assign mac_clear_and_mult = assembled_clear_mult;
    
    // 2-cycle 8-bit output protocol
    // Cycle 1: Output low 8 bits (7:0) + overflow
    // Cycle 2: Output high 8 bits (15:8)
    assign data_out = output_cycle_state ? result_reg[15:8] : result_reg[7:0];
    assign overflow_out = overflow_reg;     // Overflow flag available in both cycles
    assign data_ready = (input_cycle_state == 1'b0) && !enable;    // Ready for new input after cycle 2

endmodule 