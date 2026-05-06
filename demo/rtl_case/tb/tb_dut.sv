`timescale 1ns/1ps

module tb_dut;
    logic clk;
    logic rst_n;
    logic req;
    logic ready;

    dut u_dut (
        .clk(clk),
        .rst_n(rst_n),
        .req(req),
        .ready(ready)
    );

    initial begin
        $dumpfile("waves/demo.vcd");
        $dumpvars(0, tb_dut);
    end

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        rst_n = 0;
        req = 0;
        repeat (2) @(posedge clk);
        rst_n = 1;
        repeat (1) @(posedge clk);
        req = 1;
        @(posedge clk);
        req = 0;
        repeat (3) @(posedge clk);
        if (^ready === 1'bx) begin
            $display("FAIL: ready is X");
            $finish_and_return(1);
        end
        $display("PASS");
        $finish;
    end
endmodule

