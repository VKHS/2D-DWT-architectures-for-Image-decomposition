// Standalone combinational CDF 5/3 pair primitives for datapath inspection.
// Inputs signed, output numerator is eight times the normalized output.
module dwt53_fir_pair(input wire signed [31:0] a,b,c,d,e,
                      output wire signed [31:0] low8,high8);
    assign low8=-a+(b<<<1)+(c<<<2)+(c<<<1)+(d<<<1)-e;
    assign high8=((d<<<1)-c-e)<<<2;
endmodule

module dwt53_lift_pair(input wire signed [31:0] a,b,c,d,e,
                       output wire signed [31:0] low8,high8);
    wire signed [31:0] dm=(b<<<1)-a-c;
    wire signed [31:0] dp=(d<<<1)-c-e;
    assign low8=(c<<<3)+dm+dp;
    assign high8=dp<<<2;
endmodule
