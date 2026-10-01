import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge

LD, LDN, AND, OR, XOR, XNOR, ADD, SUB, ST, CC, NEUR, TH, FN, ANDN, RND = range(1, 16)
NOP = 0
H = 15

async def reset(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await FallingEdge(dut.clk)

async def step(dut, op, arg=0, hx=0, go=1):
    """Set inputs while the clock is low, let one rising edge execute, settle."""
    dut.ui_in.value = (op << 4) | arg
    dut.uio_in.value = (go << 1) | hx
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)

def rr(dut):
    return (int(dut.uio_out.value) >> 2) & 1

async def add8(dut, a, b, sub=False):
    await step(dut, CC, 1 if sub else 0)
    res = 0
    for i in range(8):
        await step(dut, LD, H, (a >> i) & 1)
        await step(dut, SUB if sub else ADD, H, (b >> i) & 1)
        await step(dut, ST, H)
        res |= ((int(dut.uio_out.value) >> 4) & 1) << i
    carry = (int(dut.uio_out.value) >> 3) & 1
    return res, carry

@cocotb.test()
async def test_add_sub(dut):
    await reset(dut)
    for a, b in [(100, 57), (200, 100), (255, 255), (0, 0), (17, 200)]:
        s, c = await add8(dut, a, b)
        assert s == (a + b) & 255 and c == (a + b) >> 8, f"{a}+{b}"
        s, c = await add8(dut, a, b, sub=True)
        assert s == (a - b) & 255 and c == int(a >= b), f"{a}-{b}"

@cocotb.test()
async def test_neuron(dut):
    await reset(dut)
    w, v, thr = 0b10110010, 0b10100110, 5
    for k in range(8):
        await step(dut, LD, H, (thr >> k) & 1)
        await step(dut, TH, 2)
    await step(dut, TH, 1)
    for i in range(8):
        await step(dut, LD, H, (w >> i) & 1)
        await step(dut, NEUR, H, (v >> i) & 1)
    assert int(dut.uo_out.value) == 6
    assert (int(dut.uio_out.value) >> 6) & 1 == 1
    await step(dut, TH, 0)
    assert rr(dut) == 1

@cocotb.test()
async def test_logic_tables(dut):
    await reset(dut)
    for t in range(16):
        for r in (0, 1):
            for h in (0, 1):
                await step(dut, LD, H, r)
                await step(dut, FN, t, h)
                assert rr(dut) == (t >> (2 * r + h)) & 1, f"FN {t} r={r} h={h}"

@cocotb.test()
async def test_lfsr(dut):
    await reset(dut)
    lfsr = 0xACE1
    for _ in range(40):
        fb = ((lfsr >> 15) ^ (lfsr >> 14) ^ (lfsr >> 12) ^ (lfsr >> 3)) & 1
        lfsr = ((lfsr << 1) | fb) & 0xFFFF
        await step(dut, RND, 0)
        assert rr(dut) == fb

@cocotb.test()
async def test_go_hold(dut):
    await reset(dut)
    await step(dut, LD, H, 1)
    assert rr(dut) == 1
    await step(dut, LDN, H, 1, go=0)
    assert rr(dut) == 1
