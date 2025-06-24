module MAC_simple (
    input wire clk,
    input wire rst,
    input wire Clear_and_Mult,
    input wire [7:0] Data_A,
    input wire [7:0] Data_B,
    output wire [15:0] Output_2,  // Accumulation result
    output wire Output_1          // Overflow flag
);

    // Internal interconnect signals
    wire input_changed;
    
    // First stage pipeline signals
    wire [7:0] reg_A, reg_B;
    wire reg_Clear_and_Mult;
    wire reg_valid;
    
    // Second stage pipeline signals
    wire [7:0] pipe_A, pipe_B;
    wire pipe_Clear_and_Mult;
    wire pipe_valid;
    
    // Multiplier output
    wire [15:0] mult_result;
    
    // Accumulator signals
    wire [16:0] accumulator_value;
    
    // Input change detection module
    change_detector change_det (
        .clk(clk),
        .rst(rst),
        .data_a(Data_A),
        .data_b(Data_B),
        .clear_mult(Clear_and_Mult),
        .input_changed(input_changed)
    );
    
    // Stage 1: Input registers
    input_registers input_regs (
        .clk(clk),
        .rst(rst),
        .data_a_in(Data_A),
        .data_b_in(Data_B),
        .clear_mult_in(Clear_and_Mult),
        .valid_in(input_changed),
        .data_a_out(reg_A),
        .data_b_out(reg_B),
        .clear_mult_out(reg_Clear_and_Mult),
        .valid_out(reg_valid)
    );
    
    // Stage 2: Pipeline registers
    pipeline_registers pipe_regs (
        .clk(clk),
        .rst(rst),
        .data_a_in(reg_A),
        .data_b_in(reg_B),
        .clear_mult_in(reg_Clear_and_Mult),
        .valid_in(reg_valid),
        .data_a_out(pipe_A),
        .data_b_out(pipe_B),
        .clear_mult_out(pipe_Clear_and_Mult),
        .valid_out(pipe_valid)
    );
    
    // Multiplier module
    TC_Mul #(.BIT_WIDTH(8)) multiplier (
        .in0(pipe_A),
        .in1(pipe_B),
        .out0(mult_result[7:0]),     // Lower 8 bits
        .out1(mult_result[15:8])     // Upper 8 bits
    );
    
    // Accumulator module
    accumulator_17bit accumulator (
        .clk(clk),
        .rst(rst),
        .mult_result(mult_result),
        .clear_mode(pipe_Clear_and_Mult),
        .valid(pipe_valid),
        .accumulator_value(accumulator_value),
        .result_out(Output_2),
        .overflow_out(Output_1)
    );

endmodule 