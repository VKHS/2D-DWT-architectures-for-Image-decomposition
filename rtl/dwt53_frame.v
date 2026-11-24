// Author: Abdolvahab Khalili Sadaghiani (VKHS), ORCID 0000-0003-4870-2768. MIT License.
// Single-level CDF 5/3, unsigned 8-bit samples, exact signed Q6 output.
// Verilog-2001 datapath reference. H,W even; ARCH=4 requires H/2,W/2
// divisible by TILE. Frame-buffered reference; not a line-rate AXI core.
module dwt53_frame #(
    parameter integer H=8, W=12, ARCH=0, TILE=2
)(
    input wire clk, rst,
    input wire in_valid,
    input wire [7:0] in_pixel,
    output wire in_ready,
    output wire out_valid,
    input wire out_ready,
    output wire signed [31:0] out_coeff,
    output wire [31:0] out_index,
    output wire out_last
);
    localparam integer N=H*W, HH=H/2, WW=W/2, P=2*TILE+3;
    localparam LOAD=0, SEP=1, DIRECT=2, LINE_FILL=3, LINE_EMIT=4,
               TILE_FILL=5, TILE_EMIT=6, DRAIN=7;
    reg [7:0] frame [0:N-1];
    reg signed [31:0] mid [0:N-1], coeff [0:N-1];
    reg signed [31:0] linebuf [0:5*W-1];
    reg [7:0] patch [0:P*P-1];
    integer state, input_idx, output_idx;
    integer pass_no, outer_idx, inner_idx, phase;
    integer oy, ox, lr, col_idx, tx, ty, px, py;
    integer saved_d, saved_prev;
    wire vertical = (ARCH==5) ? (pass_no==0) : (pass_no==1);
    assign in_ready = (state==LOAD);
    assign out_valid = (state==DRAIN);
    assign out_index = output_idx;
    assign out_last = out_valid && (output_idx==N-1);
    assign out_coeff = out_valid ? coeff[output_idx] : 32'sd0;

    // Periodic indices. Offsets never require more than a few wraps;
    // modulo by constant dimensions also handles H/W=2.
    function integer wrap;
        input integer k,n;
        integer t;
        begin t=k%n; wrap=(t<0)?t+n:t; end
    endfunction
    function integer pix;
        input integer r,c;
        begin pix=frame[wrap(r,H)*W+wrap(c,W)]; end
    endfunction
    function integer axis_sample;
        input integer v, src, o, k;
        integer idx;
        begin
            idx=v ? wrap(k,H)*W+o : o*W+wrap(k,W);
            if(src==0) axis_sample=frame[idx];
            else axis_sample=mid[idx];
        end
    endfunction
    function integer lo8;
        input integer a,b,c,d,e;
        begin lo8=-a+(b<<<1)+(c<<<2)+(c<<<1)+(d<<<1)-e; end
    endfunction
    function integer hi8;
        input integer c,d,e;
        begin hi8=((d<<<1)-c-e)<<<2; end
    endfunction
    function integer pred2;
        input integer e0,o0,e1;
        begin pred2=(o0<<<1)-e0-e1; end
    endfunction
    function integer sample_k;
        input integer k;
        begin sample_k=axis_sample(vertical,pass_no,outer_idx,2*inner_idx+k); end
    endfunction
    function integer weight;
        input integer band,k;
        begin
            if(band==0) begin
                case(k)
                    -2,2: weight=-1;
                    -1,1: weight=2;
                    0: weight=6;
                    default: weight=0;
                endcase
            end else begin
                case(k)
                    0,2: weight=-4;
                    1: weight=8;
                    default: weight=0;
                endcase
            end
        end
    endfunction
    // Independent outer-product 2-D filter. Constant loop bounds.
    // ARCH=2 reads frame directly; ARCH=4 reads a local halo patch.
    function integer direct_band;
        input integer r,c,vb,hb,use_patch;
        integer k,l,z,acc;
        begin
            acc=0;
            for(k=-2;k<=2;k=k+1)
                for(l=-2;l<=2;l=l+1) begin
                    if(use_patch!=0) z=patch[(r+k)*P+c+l];
                    else z=pix(r+k,c+l);
                    acc=acc+weight(vb,k)*weight(hb,l)*z;
                end
            direct_band=acc;
        end
    endfunction
    task emit_direct;
        input integer y,x,pr,pc,local_patch;
        begin
            coeff[y*W+x] <= direct_band(pr,pc,0,0,local_patch);
            coeff[y*W+x+WW] <= direct_band(pr,pc,0,1,local_patch);
            coeff[(y+HH)*W+x] <= direct_band(pr,pc,1,0,local_patch);
            coeff[(y+HH)*W+x+WW] <= direct_band(pr,pc,1,1,local_patch);
        end
    endtask
    task write_pair;
        input integer l,h;
        integer li,hi;
        begin
            if(vertical) begin
                li=inner_idx*W+outer_idx;
                hi=(inner_idx+HH)*W+outer_idx;
            end else begin
                li=outer_idx*W+inner_idx;
                hi=outer_idx*W+inner_idx+WW;
            end
            if(pass_no==0) begin mid[li]<=l; mid[hi]<=h; end
            else begin coeff[li]<=l; coeff[hi]<=h; end
        end
    endtask
    task advance_pair;
        begin
            phase<=0;
            if(inner_idx==(vertical?HH:WW)-1) begin
                inner_idx<=0;
                if(outer_idx==(vertical?W:H)-1) begin
                    outer_idx<=0;
                    if(pass_no==0) pass_no<=1;
                    else begin state<=DRAIN; output_idx<=0; end
                end else outer_idx<=outer_idx+1;
            end else inner_idx<=inner_idx+1;
        end
    endtask
    // One folded predictor, with phase-controlled neighborhood multiplexing.
    wire signed [31:0] folded_offset = (phase==0)?0:-2;
    // Use predictor only inside clocked block; no combinational memory
    // sensitivity-list dependencies.
    always @(posedge clk) begin
        if(rst) begin
            state<=LOAD; input_idx<=0; output_idx<=0;
            pass_no<=0; outer_idx<=0; inner_idx<=0; phase<=0;
            oy<=0; ox<=0; lr<=0; col_idx<=0;
            tx<=0; ty<=0; px<=0; py<=0;
            saved_d<=0; saved_prev<=0;
        end else begin
            case(state)
                LOAD: if(in_valid) begin
                    frame[input_idx]<=in_pixel;
                    if(input_idx==N-1) begin
                        input_idx<=0; output_idx<=0;
                        pass_no<=0; outer_idx<=0; inner_idx<=0; phase<=0;
                        oy<=0; ox<=0; lr<=0; col_idx<=0;
                        tx<=0; ty<=0; px<=0; py<=0;
                        case(ARCH)
                            2: state<=DIRECT;
                            3: state<=LINE_FILL;
                            4: state<=TILE_FILL;
                            default: state<=SEP;
                        endcase
                    end else input_idx<=input_idx+1;
                end
                SEP: begin
                    if(ARCH==5) begin
                        // Two predictor cycles, then one update/write cycle.
                        if(phase<2) begin
                            if(phase==0)
                                saved_d<=pred2(sample_k(folded_offset),
                                    sample_k(folded_offset+1),sample_k(folded_offset+2));
                            else
                                saved_prev<=pred2(sample_k(folded_offset),
                                    sample_k(folded_offset+1),sample_k(folded_offset+2));
                            phase<=phase+1;
                        end else begin
                            write_pair((sample_k(0)<<<3)+saved_d+saved_prev,saved_d<<<2);
                            advance_pair;
                        end
                    end else begin
                        if(ARCH==1)
                            write_pair((sample_k(0)<<<3)+
                                pred2(sample_k(-2),sample_k(-1),sample_k(0))+
                                pred2(sample_k(0),sample_k(1),sample_k(2)),
                                pred2(sample_k(0),sample_k(1),sample_k(2))<<<2);
                        else
                            write_pair(lo8(sample_k(-2),sample_k(-1),sample_k(0),
                                           sample_k(1),sample_k(2)),
                                       hi8(sample_k(0),sample_k(1),sample_k(2)));
                        advance_pair;
                    end
                end
                DIRECT: begin
                    emit_direct(oy,ox,2*oy,2*ox,0);
                    if(ox==WW-1) begin
                        ox<=0;
                        if(oy==HH-1) state<=DRAIN;
                        else oy<=oy+1;
                    end else ox<=ox+1;
                end
                LINE_FILL: begin
                    // Five horizontal rows, including periodic halo.
                    // Refill each output-row group, not a strict raster-only stream.
                    linebuf[lr*W+ox]<=lo8(pix(2*oy+lr-2,2*ox-2),
                        pix(2*oy+lr-2,2*ox-1),pix(2*oy+lr-2,2*ox),
                        pix(2*oy+lr-2,2*ox+1),pix(2*oy+lr-2,2*ox+2));
                    linebuf[lr*W+ox+WW]<=hi8(pix(2*oy+lr-2,2*ox),
                        pix(2*oy+lr-2,2*ox+1),pix(2*oy+lr-2,2*ox+2));
                    if(ox==WW-1) begin
                        ox<=0;
                        if(lr==4) begin lr<=0; col_idx<=0; state<=LINE_EMIT; end
                        else lr<=lr+1;
                    end else ox<=ox+1;
                end
                LINE_EMIT: begin
                    coeff[oy*W+col_idx]<=lo8(linebuf[col_idx],linebuf[W+col_idx],
                        linebuf[2*W+col_idx],linebuf[3*W+col_idx],linebuf[4*W+col_idx]);
                    coeff[(oy+HH)*W+col_idx]<=hi8(linebuf[2*W+col_idx],
                        linebuf[3*W+col_idx],linebuf[4*W+col_idx]);
                    if(col_idx==W-1) begin
                        col_idx<=0;
                        if(oy==HH-1) state<=DRAIN;
                        else begin oy<=oy+1; state<=LINE_FILL; end
                    end else col_idx<=col_idx+1;
                end
                TILE_FILL: begin
                    patch[py*P+px]<=pix(2*ty+py-2,2*tx+px-2);
                    if(px==P-1) begin
                        px<=0;
                        if(py==P-1) begin py<=0; state<=TILE_EMIT; end
                        else py<=py+1;
                    end else px<=px+1;
                end
                TILE_EMIT: begin
                    emit_direct(ty+py,tx+px,2*py+2,2*px+2,1);
                    if(px==TILE-1) begin
                        px<=0;
                        if(py==TILE-1) begin
                            py<=0;
                            if(tx==WW-TILE) begin
                                tx<=0;
                                if(ty==HH-TILE) state<=DRAIN;
                                else begin ty<=ty+TILE; state<=TILE_FILL; end
                            end else begin tx<=tx+TILE; state<=TILE_FILL; end
                        end else py<=py+1;
                    end else px<=px+1;
                end
                DRAIN: if(out_ready) begin
                    if(output_idx==N-1) begin output_idx<=0; state<=LOAD; end
                    else output_idx<=output_idx+1;
                end
                default: state<=LOAD;
            endcase
        end
    end
endmodule
