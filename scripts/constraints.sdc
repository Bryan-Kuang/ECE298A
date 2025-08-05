# Timing constraints file - Bryan Kuang MAC peripheral
# Design features: 2-cycle serial interface + pipelined MAC

# Clock definition - 100MHz (suitable for MAC operations)
set period 10
create_clock -period $period [get_ports clk]

# Input/output delay settings
set clk_period_factor .2
set delay [expr $period * $clk_period_factor]

# TinyTapeout interface timing constraints
set_input_delay $delay -clock clk [get_ports ui_in*]
set_input_delay $delay -clock clk [get_ports uio_in*]
set_input_delay $delay -clock clk [get_ports ena]
set_input_delay $delay -clock clk [get_ports rst_n]

set_output_delay $delay -clock clk [get_ports uo_out*]
set_output_delay $delay -clock clk [get_ports uio_out*]
set_output_delay $delay -clock clk [get_ports uio_oe*]

# Signal transition time
set_input_transition .1 [get_ports ui_in*]
set_input_transition .1 [get_ports uio_in*]
set_input_transition .1 [get_ports ena]
set_input_transition .1 [get_ports rst_n]

# MAC peripheral special constraints
# Relax some combinational logic constraints due to 2-cycle operation
set_max_delay 8 -from [get_ports ui_in*] -to [get_ports uo_out*]