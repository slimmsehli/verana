module dut (
    input  logic clk,
    input  logic rst_n,
    input  logic req,
    output logic ready
);
    // Intentional bug for demo:
    // ready is not reset and can become X in sim.
    always_ff @(posedge clk) begin
        if (req) begin
            ready <= 1'b1;
        end
        // no else branch to deassert and no reset assignment
    end
endmodule

