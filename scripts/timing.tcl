# Timing analysis script - Bryan Kuang MAC peripheral
# Read standard cell library
read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib

# Read synthesized netlist
read_verilog netlist.v

# Link design (corrected module name)
link_design tt_um_BryanKuang_mac_peripheral

# Read timing constraints
read_sdc constraints.sdc

# Generate timing reports
report_checks -path_delay max -fields {startpoint endpoint arrival required slack} -digits 4 > timing_report.txt
report_wns > timing_wns.txt
report_tns > timing_tns.txt

# Additional reports - suitable for MAC peripheral
report_checks -path_delay min > timing_hold_report.txt