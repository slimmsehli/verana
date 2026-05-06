TOP := tb_dut
RTL := rtl/dut.sv
TB := tb/tb_dut.sv
SIMV := simv_demo
WAVE := waves/demo.vcd

.PHONY: all lint build run yosys clean

all: lint build run

lint:
	verilator --lint-only -Wall $(RTL) $(TB)

build:
	verilator -Wall --binary -o $(SIMV) --top-module $(TOP) $(RTL) $(TB)

run:
	./obj_dir/$(SIMV)

yosys:
	yosys -p "read_verilog $(RTL); hierarchy -check -top dut; proc; opt; stat;"

clean:
	rm -rf obj_dir waves *.log

