# Makefile
# See https://docs.cocotb.org/en/stable/quickstart.html for more info

# defaults
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
SRC_DIR := /Users/bryan/Library/CloudStorage/OneDrive-UniversityofWaterloo/Waterloo/2B/ECE\ 298A/src
PROJECT_SOURCES = tt_um_BryanKuang_mac_peripheral.v nibble_interface.v components/input_registers.v components/change_detector.v components/pipeline_registers.v components/accumulator_17bit.v builtin_components/TC_Mul.v

# Common Verilog sources (without testbench)
COMMON_VERILOG_SOURCES = ../src/tt_um_BryanKuang_mac_peripheral.v ../src/nibble_interface.v ../src/components/input_registers.v ../src/components/change_detector.v ../src/components/pipeline_registers.v ../src/components/accumulator_17bit.v ../src/builtin_components/TC_Mul.v

ifneq ($(GATES),yes)

# RTL simulation:
SIM_BUILD				= sim_build/rtl

else

# Gate level simulation:
SIM_BUILD				= sim_build/gl
COMPILE_ARGS    += -DGL_TEST
COMPILE_ARGS    += -DFUNCTIONAL
COMPILE_ARGS    += -DSIM
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_io/verilog/sg13g2_io.v
VERILOG_SOURCES += $(PDK_ROOT)/ihp-sg13g2/libs.ref/sg13g2_stdcell/verilog/sg13g2_stdcell.v

# this gets copied in by the GDS action workflow
VERILOG_SOURCES += gate_level_netlist.v

endif

# Allow sharing configuration between design and testbench via `include`:
COMPILE_ARGS 		+= -I../src

# Default test: original MAC tests
test_mac:
	$(MAKE) VERILOG_SOURCES="$(COMMON_VERILOG_SOURCES) tb_mac_simple.v" TOPLEVEL=tb_mac_simple MODULE=test_mac sim

# Default target
all: test_mac

# Backward compatibility - default to MAC test
VERILOG_SOURCES = $(COMMON_VERILOG_SOURCES) tb_mac_simple.v
TOPLEVEL = tb_mac_simple
MODULE = test_mac

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
