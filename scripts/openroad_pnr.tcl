# OpenROAD Place and Route script for Bryan Kuang MAC peripheral
# Optimized for TinyTapeout constraints

puts "================================================="
puts "OpenROAD PnR Flow for MAC Peripheral (TinyTapeout)"
puts "================================================="

# Source configuration files
source floorplan_config.tcl
source power_config.tcl

# Read technology files
read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib

# Read LEF files (if available)
if {[file exists "sky130_tech.lef"]} {
    read_lef sky130_tech.lef
}

# Read synthesized netlist
read_verilog netlist.v

# Link the design
link_design tt_um_BryanKuang_mac_peripheral

# Read timing constraints
read_sdc constraints.sdc

# Report initial design statistics
puts "\nDesign Statistics:"
puts "------------------"
report_units
report_design_area

# Initialize floorplan for TinyTapeout
# TinyTapeout tile is typically small, adjust based on your allocation
init_floorplan -die_area "0 0 $die_width $die_height" \
               -core_area "$core_margin $core_margin [expr $die_width - $core_margin] [expr $die_height - $core_margin]" \
               -site unithd

# Add power/ground connections (TinyTapeout specific)
add_global_connection -net VPWR -pin_pattern {^VPWR$} -power
add_global_connection -net VGND -pin_pattern {^VGND$} -ground
add_global_connection -net VDD -pin_pattern {^VDD$} -power
add_global_connection -net VSS -pin_pattern {^VSS$} -ground

# Global placement with timing optimization
puts "\nRunning Global Placement..."
global_placement -timing_driven \
                 -density 0.6 \
                 -pad_left $core_margin \
                 -pad_right $core_margin \
                 -pad_top $core_margin \
                 -pad_bottom $core_margin

# Check placement legality
puts "\nChecking Placement..."
check_placement -verbose

# Clock tree synthesis (if design has clocks)
puts "\nRunning Clock Tree Synthesis..."
if {[get_clocks] != ""} {
    clock_tree_synthesis -buf_list "sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_2" \
                         -sink_clustering_enable \
                         -distance_between_buffers 100
} else {
    puts "No clocks found, skipping CTS"
}

# Detailed placement
puts "\nRunning Detailed Placement..."
detailed_placement

# Report placement statistics
puts "\nPlacement Statistics:"
puts "--------------------"
report_design_area

# Global routing with congestion awareness
puts "\nRunning Global Routing..."
set_routing_layers -signal li1:met4 -clock li1:met5
global_route -congestion_iterations 100 \
             -verbose

# Detailed routing
puts "\nRunning Detailed Routing..."
detailed_route -output_drc post_route_drc.rpt \
               -output_maze_log post_route_maze.log \
               -save_guide_updates \
               -verbose 1

# Check routing quality
puts "\nChecking Routing Quality..."
check_antennas -verbose
report_route_status

# Final design checks
puts "\nFinal Design Checks:"
puts "-------------------"
check_setup -verbose
report_power -verbose

# Write output files
puts "\nWriting Output Files..."
write_verilog post_route_netlist.v
write_def post_route_design.def
write_sdc post_route_constraints.sdc
write_db post_route_design.db

# Generate reports
report_checks -path_delay max > post_route_timing_preview.rpt
report_design_area > post_route_area.rpt
report_power > post_route_power.rpt

puts "================================================="
puts "PnR Flow Completed Successfully!"
puts ""
puts "Output Files Generated:"
puts "  📄 post_route_netlist.v       - Routed netlist"
puts "  📄 post_route_design.def      - Physical layout"
puts "  📄 post_route_design.db       - Database for SPEF"
puts "  📄 post_route_constraints.sdc - Updated constraints"
puts ""
puts "Report Files Generated:"
puts "  📊 post_route_timing_preview.rpt - Quick timing check"
puts "  📊 post_route_area.rpt           - Area utilization"
puts "  📊 post_route_power.rpt          - Power analysis"
puts "  📊 post_route_drc.rpt            - DRC violations"
puts ""
puts "Next: Run SPEF extraction"
puts "================================================="