# Post-layout timing analysis script - Bryan Kuang MAC peripheral
# This script performs STA with actual parasitic extraction

# Read standard cell library
read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib

# Read post-route netlist (replace with your actual post-route netlist)
# read_verilog post_route_netlist.v
read_verilog netlist.v  # Change this to your post-route netlist

# Link design
link_design tt_um_BryanKuang_mac_peripheral

# Read timing constraints
read_sdc constraints.sdc

# Read parasitic information (uncomment when you have SPEF file)
# read_spef parasitic.spef
# OR read SDF file
# read_sdf -path [get_cells] design.sdf

# Alternative: If you have DEF file with RC extraction
# read_def design.def

# Generate post-layout timing reports
report_checks -path_delay max -fields {startpoint endpoint arrival required slack} -digits 4 > post_layout_timing_report.txt
report_wns > post_layout_timing_wns.txt  
report_tns > post_layout_timing_tns.txt

# Hold time analysis (more critical in post-layout)
report_checks -path_delay min > post_layout_timing_hold_report.txt

# Additional post-layout specific reports
report_checks -group_count 10 > post_layout_top10_paths.txt
report_clock_skew > post_layout_clock_skew.txt

# Power analysis (if available)
# report_power > post_layout_power_report.txt

# Summary report
echo "Post-layout STA Analysis Summary:" > post_layout_summary.txt
echo "================================" >> post_layout_summary.txt
echo "" >> post_layout_summary.txt
echo "Worst Negative Slack (Setup):" >> post_layout_summary.txt
report_wns >> post_layout_summary.txt
echo "" >> post_layout_summary.txt  
echo "Total Negative Slack:" >> post_layout_summary.txt
report_tns >> post_layout_summary.txt
echo "" >> post_layout_summary.txt
echo "Worst Hold Slack:" >> post_layout_summary.txt
report_worst_slack -min >> post_layout_summary.txt