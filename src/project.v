`default_nettype none

module tt_um_tiny1_cpu (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);

  wire [3:0] op  = ui_in[7:4];
  wire [3:0] arg = ui_in[3:0];
  wire       hx  = uio_in[0];
  wire       go  = uio_in[1];

  reg        rr, cy, dout, wr;
  reg [15:0] regs;
  reg [7:0]  cnt, thr;
  reg [15:0] lfsr;

  wire [15:0] rv = {hx, regs[14:0]};
  wire        x  = rv[arg];

  wire xs   = (op == 4'h8) ? ~x : x;
  wire sum  = rr ^ xs ^ cy;
  wire cout = (rr & xs) | (cy & (rr ^ xs));
  wire ge   = (cnt >= thr);
  wire fb   = lfsr[15] ^ lfsr[14] ^ lfsr[12] ^ lfsr[3];

  always @(posedge clk) begin
    if (!rst_n) begin
      rr <= 1'b0; cy <= 1'b0; dout <= 1'b0; wr <= 1'b0;
      regs <= 16'd0; cnt <= 8'd0; thr <= 8'd0; lfsr <= 16'hACE1;
    end else begin
      wr <= 1'b0;
      if (go) begin
        case (op)
          4'h1: rr <= x;
          4'h2: rr <= ~x;
          4'h3: rr <= rr & x;
          4'h4: rr <= rr | x;
          4'h5: rr <= rr ^ x;
          4'h6: rr <= ~(rr ^ x);
          4'h7, 4'h8: begin rr <= sum; cy <= cout; end
          4'h9: begin
            if (arg == 4'hF) begin dout <= rr; wr <= 1'b1; end
            else regs[arg] <= rr;
          end
          4'hA: begin
            case (arg[1:0])
              2'd0: cy <= 1'b0;
              2'd1: cy <= 1'b1;
              2'd2: cy <= rr;
              2'd3: rr <= cy;
            endcase
          end
          4'hB: if (rr == x) cnt <= cnt + 8'd1;
          4'hC: begin
            case (arg[1:0])
              2'd0: rr <= ge;
              2'd1: cnt <= 8'd0;
              2'd2: thr <= {rr, thr[7:1]};
              2'd3: cnt <= cnt + {7'd0, rr};
            endcase
          end
          4'hD: rr <= arg[{rr, hx}];
          4'hE: rr <= rr & ~x;
          4'hF: begin
            case (arg[1:0])
              2'd0: begin rr <= fb; lfsr <= {lfsr[14:0], fb}; end
              2'd1: lfsr <= {lfsr[14:0], rr};
              default: ;
            endcase
          end
          default: ;
        endcase
      end
    end
  end

  assign uo_out  = cnt;
  assign uio_out = {1'b0, ge, wr, dout, cy, rr, 2'b00};
  assign uio_oe  = 8'h7C;

  wire _unused = &{ena, uio_in[7:2], 1'b0};

endmodule
