module MAC_simple (
    input wire clk,
    input wire rst,
    input wire Clear_and_Mult,
    input wire [7:0] Data_A,
    input wire [7:0] Data_B,
    output reg [15:0] Output_2,  // 累加结果
    output reg Output_1          // 溢出标志
);

    // 内部信号 - 两级流水线
    reg [7:0] reg_A, reg_B;          // 第一级：输入寄存器
    reg reg_Clear_and_Mult;          // 第一级：控制信号寄存器
    reg reg_valid;                   // 第一级：有效信号
    
    reg [7:0] pipe_A, pipe_B;        // 第二级：流水线寄存器
    reg pipe_Clear_and_Mult;         // 第二级：流水线控制信号
    reg pipe_valid;                  // 第二级：流水线有效信号
    
    wire [15:0] mult_result;         // 乘法结果
    reg [16:0] accumulator;          // 17位累加器 (包含溢出位)
    wire [16:0] add_result;          // 加法结果
    
    // 检测输入变化 - 当输入发生变化时认为是新的有效操作
    reg [7:0] last_A, last_B;
    reg last_Clear_and_Mult;
    wire input_changed;
    
    assign input_changed = (Data_A != last_A) || (Data_B != last_B) || (Clear_and_Mult != last_Clear_and_Mult);
    
    // 乘法器 - 使用第二级流水线的值
    TC_Mul #(.BIT_WIDTH(8)) multiplier (
        .in0(pipe_A),
        .in1(pipe_B),
        .out0(mult_result[7:0]),     // 低8位
        .out1(mult_result[15:8])     // 高8位
    );
    
    // 加法器 - 累加器 + 当前乘法结果
    assign add_result = accumulator + {1'b0, mult_result};
    
    // 时序逻辑 - 带有效信号控制的流水线
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            // 复位所有寄存器
            reg_A <= 8'b0;
            reg_B <= 8'b0;
            reg_Clear_and_Mult <= 1'b0;
            reg_valid <= 1'b0;
            pipe_A <= 8'b0;
            pipe_B <= 8'b0;
            pipe_Clear_and_Mult <= 1'b0;
            pipe_valid <= 1'b0;
            accumulator <= 17'b0;
            Output_2 <= 16'b0;
            Output_1 <= 1'b0;
            last_A <= 8'b0;
            last_B <= 8'b0;
            last_Clear_and_Mult <= 1'b0;
        end else begin
            // 更新历史值
            last_A <= Data_A;
            last_B <= Data_B;
            last_Clear_and_Mult <= Clear_and_Mult;
            
            // 第一级：输入寄存（只有输入变化时才有效）
            reg_A <= Data_A;
            reg_B <= Data_B;
            reg_Clear_and_Mult <= Clear_and_Mult;
            reg_valid <= input_changed;
            
            // 第二级：流水线推进
            pipe_A <= reg_A;
            pipe_B <= reg_B;
            pipe_Clear_and_Mult <= reg_Clear_and_Mult;
            pipe_valid <= reg_valid;
            
            // 第三级：只有当流水线有效时才进行计算
            if (pipe_valid) begin
                if (pipe_Clear_and_Mult) begin
                    // 清零模式：累加器设为当前乘法结果
                    accumulator <= {1'b0, mult_result};
                    Output_2 <= mult_result;
                    Output_1 <= 1'b0;  // 单次乘法不会溢出16位
                end else begin
                    // 累加模式：累加器 += 当前乘法结果
                    accumulator <= add_result;
                    Output_2 <= add_result[15:0];
                    Output_1 <= add_result[16];  // 溢出标志
                end
            end
            // 如果pipe_valid为0，则不更新累加器和输出
        end
    end

endmodule 