`timescale 1ns / 1ps

module tb_modular_mac;

    // 时钟和复位
    reg clk;
    reg rst;
    
    // MAC输入
    reg Clear_and_Mult;
    reg [7:0] Data_A;
    reg [7:0] Data_B;
    
    // MAC输出
    wire [15:0] Output_2;
    wire Output_1;

    // Instantiate DUT
    MAC_simple dut (
        .clk(clk),
        .rst(rst),
        .Clear_and_Mult(Clear_and_Mult),
        .Data_A(Data_A),
        .Data_B(Data_B),
        .Output_2(Output_2),
        .Output_1(Output_1)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns周期，100MHz
    end

    // 测试序列
    initial begin
        // 初始化
        rst = 1;
        Clear_and_Mult = 0;
        Data_A = 0;
        Data_B = 0;
        
        // 复位
        #20 rst = 0;
        
        // 等待几个时钟周期
        #50;
        
        // 测试1: 基本乘法 10×5
        Data_A = 10;
        Data_B = 5;
        Clear_and_Mult = 1;
        #50; // 等待流水线
        $display("Test 1: 10×5 = %d (Expected: 50)", Output_2);
        
        // 测试2: 累加 +3×4
        Data_A = 3;
        Data_B = 4;
        Clear_and_Mult = 0;
        #50;
        $display("Test 2: 50 + 3×4 = %d (Expected: 62)", Output_2);
        
        // 测试3: 清零模式 7×8
        Data_A = 7;
        Data_B = 8;
        Clear_and_Mult = 1;
        #50;
        $display("Test 3: 7×8 = %d (Expected: 56)", Output_2);
        
        // 测试4: 大数值测试
        Data_A = 200;
        Data_B = 200;
        Clear_and_Mult = 1;
        #50;
        $display("Test 4: 200×200 = %d, Overflow = %d", Output_2, Output_1);
        
        // 测试5: 溢出累加
        Data_A = 100;
        Data_B = 100;
        Clear_and_Mult = 0;
        #50;
        $display("Test 5: Previous + 100×100 = %d, Overflow = %d", Output_2, Output_1);
        
        #100;
        $finish;
    end

    // 波形文件生成
    initial begin
        $dumpfile("tb_modular_mac.vcd");
        $dumpvars(0, tb_modular_mac);
    end

endmodule 