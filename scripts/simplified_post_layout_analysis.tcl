# Simplified post-layout timing analysis without full PnR
# This provides estimated post-layout timing using enhanced wire load models

puts "================================================="
puts "Simplified Post-Layout Timing Analysis"
puts "Using Enhanced Wire Load Models"
puts "================================================="

# Read standard cell library
read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib

# Read synthesized netlist
read_verilog netlist.v

# Link design
link_design tt_um_BryanKuang_mac_peripheral

# Read timing constraints
read_sdc constraints.sdc

# Set enhanced wire load models to simulate post-layout conditions
# These values are estimated based on typical sky130 routing

# Set more pessimistic wire load model (larger than default)
set_wire_load_model "Large"

# Add additional timing margins to simulate routing delays
# Setup margin: add extra delay to simulate actual routing
set setup_margin 0.5
set hold_margin 0.1

# Apply margins to all timing paths
set_timing_derate -early [expr 1.0 - $hold_margin]
set_timing_derate -late [expr 1.0 + $setup_margin]

# Add extra capacitive load to outputs to simulate actual routing
set_load 0.05 [all_outputs]

# Set more realistic transition times
set_input_transition 0.2 [all_inputs]

puts "\nTiming Analysis Settings:"
puts "-------------------------"
puts "Wire Load Model: Large (pessimistic)"
puts "Setup Timing Margin: +${setup_margin}ns"
puts "Hold Timing Margin: -${hold_margin}ns"
puts "Output Load: 0.05 pF"
puts "Input Transition: 0.2 ns"

# Generate timing reports with margins applied
puts "\nGenerating Simplified Post-Layout Reports..."

report_checks -path_delay max -fields {startpoint endpoint arrival required slack} -digits 4 > simplified_post_layout_timing_report.txt
report_wns > simplified_post_layout_timing_wns.txt
report_tns > simplified_post_layout_timing_tns.txt
report_checks -path_delay min > simplified_post_layout_timing_hold_report.txt

# Generate comparison with original analysis
puts "\nGenerating Comparison Analysis..."

# Create summary report
set summary_file "simplified_post_layout_summary.txt"
set fp [open $summary_file w]

puts $fp "Simplified Post-Layout Timing Analysis Summary"
puts $fp "=============================================="
puts $fp ""
puts $fp "Analysis Method: Enhanced Wire Load Models + Timing Margins"
puts $fp "Setup Margin Applied: +${setup_margin}ns"
puts $fp "Hold Margin Applied: -${hold_margin}ns"
puts $fp ""
puts $fp "IMPORTANT NOTE:"
puts $fp "This is an ESTIMATED post-layout analysis using enhanced wire load models."
puts $fp "For accurate results, full Place & Route with parasitic extraction is required."
puts $fp ""

# Get timing results
puts $fp "Timing Results:"
puts $fp "---------------"

# Capture WNS and TNS
set wns_result ""
set tns_result ""

# Read WNS
if {[catch {
    set wns_fp [open "simplified_post_layout_timing_wns.txt" r]
    set wns_result [read $wns_fp]
    close $wns_fp
}]} {
    set wns_result "N/A"
}

# Read TNS  
if {[catch {
    set tns_fp [open "simplified_post_layout_timing_tns.txt" r]
    set tns_result [read $tns_fp]
    close $tns_fp
}]} {
    set tns_result "N/A"
}

puts $fp "Worst Negative Slack (Setup): $wns_result"
puts $fp "Total Negative Slack: $tns_result"
puts $fp ""

# Compare with pre-layout if available
if {[file exists "report/timing_wns.txt"]} {
    set pre_wns_fp [open "report/timing_wns.txt" r]
    set pre_wns [read $pre_wns_fp]
    close $pre_wns_fp
    
    puts $fp "Comparison with Pre-Layout:"
    puts $fp "---------------------------"
    puts $fp "Pre-layout WNS: $pre_wns"
    puts $fp "Estimated Post-layout WNS: $wns_result"
    puts $fp ""
}

puts $fp "Recommendations:"
puts $fp "----------------"
puts $fp "1. If timing is marginal, consider design optimization"
puts $fp "2. For accurate analysis, run full PnR with OpenROAD"
puts $fp "3. This analysis provides conservative estimates"
puts $fp ""
puts $fp "Generated Files:"
puts $fp "----------------"
puts $fp "- simplified_post_layout_timing_report.txt"
puts $fp "- simplified_post_layout_timing_wns.txt"
puts $fp "- simplified_post_layout_timing_tns.txt"
puts $fp "- simplified_post_layout_timing_hold_report.txt"

close $fp

puts "================================================="
puts "Simplified Post-Layout Analysis Completed!"
puts ""
puts "⚠️  IMPORTANT: This is an ESTIMATED analysis"
puts "   For production designs, use full PnR flow"
puts ""
puts "Generated Reports:"
puts "  📊 simplified_post_layout_summary.txt"
puts "  📈 simplified_post_layout_timing_report.txt"
puts "  ⚡ simplified_post_layout_timing_wns.txt"
puts "================================================="