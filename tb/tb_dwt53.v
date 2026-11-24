`timescale 1ns/1ps
module tb_dwt53;
    parameter integer ARCH=0,H=8,W=12,TILE=2,FRAMES=6;
    localparam N=H*W;
    reg clk=0; always #5 clk=~clk;
    reg rst=1, in_valid=0, out_ready=0;
    reg [7:0] in_pixel=0;
    wire in_ready,out_valid,out_last;
    wire signed [31:0] out_coeff;
    wire [31:0] out_index;
    reg [7:0] pixels [0:N*FRAMES-1];
    reg signed [31:0] golden [0:N*FRAMES-1];
    integer f,k,t,cycles;
    reg [1023:0] pixel_file,golden_file;
    dwt53_frame #(.H(H),.W(W),.ARCH(ARCH),.TILE(TILE)) dut(
        .clk(clk),.rst(rst),.in_valid(in_valid),.in_pixel(in_pixel),.in_ready(in_ready),
        .out_valid(out_valid),.out_ready(out_ready),.out_coeff(out_coeff),
        .out_index(out_index),.out_last(out_last));
    initial begin
        if(H<2 || W<2 || H%2 || W%2 || ARCH<0 || ARCH>5 ||
           TILE<1 || (ARCH==4 && ((H/2)%TILE || (W/2)%TILE)))
            $fatal(1,"Invalid parameters");
        if(!$value$plusargs("pixels=%s",pixel_file)) pixel_file="build/pixels.hex";
        if(!$value$plusargs("golden=%s",golden_file)) golden_file="build/golden.hex";
        $readmemh(pixel_file,pixels); $readmemh(golden_file,golden);
        repeat(3) @(negedge clk);
        rst=0;
        for(f=0;f<FRAMES;f=f+1) begin
            for(k=0;k<N;k=k+1) begin
                if(k%7==0) begin in_valid=0; @(negedge clk); end
                in_pixel=pixels[f*N+k]; in_valid=1;
                // Sample handshake on positive edge.
                @(posedge clk);
                while(!in_ready) @(posedge clk);
                @(negedge clk);
            end
            in_valid=0; cycles=0;
            while(!out_valid) begin @(negedge clk); cycles=cycles+1; end
            $display("arch=%0d frame=%0d compute_cycles=%0d",ARCH,f,cycles);
            k=0; t=0;
            while(k<N) begin
                out_ready=(t%5!=2);
                @(posedge clk);
                if(out_valid && out_ready) begin
                    if(out_index!==k || out_coeff!==golden[f*N+k] ||
                       out_last!==(k==N-1))
                        $fatal(1,"arch=%0d frame=%0d idx=%0d got=%0d expected=%0d",
                            ARCH,f,k,out_coeff,golden[f*N+k]);
                    k=k+1;
                end
                @(negedge clk); t=t+1;
            end
            out_ready=0;
        end
        $display("PASS architecture %0d: %0d coefficients",ARCH,N*FRAMES);
        $finish;
    end
    initial begin
        repeat(1000*N*FRAMES) @(posedge clk);
        $fatal(1,"timeout");
    end
endmodule
