# SPEF extraction script for post-route parasitic analysis
# This script extracts RC parasitics from the routed design

puts "================================================="
puts "SPEF Extraction for MAC Peripheral"
puts "================================================="

# Read technology files
read_liberty sky130_fd_sc_hd__tt_025C_1v80.lib

# Read the post-route database
if {[file exists "post_route_design.db"]} {
    read_db post_route_design.db
    puts "✅ Loaded post-route database"
} else {
    puts "❌ Error: post_route_design.db not found!"
    puts "   Please run OpenROAD PnR first"
    exit 1
}

# Define RC extraction parameters for sky130
# These values are typical for sky130 technology
define_process_corner -ext_model_index 0 \
                      -temperature 25 \
                      -voltage 1.8

# Set extraction options
set_rcx_options -max_resistance 1000 \
                -coupling_threshold 0.1 \
                -total_cc_current_density_threshold 0.1 \
                -relative_cc_current_density_threshold 0.01

# Extract RC parasitics
extract_parasitics -output post_route_parasitics.spef

# Also generate detailed RC report
report_parasitics > parasitics_summary.txt

# Verify extraction
if {[file exists "post_route_parasitics.spef"]} {
    puts "✅ SPEF extraction completed successfully!"
    puts "Generated files:"
    puts "  - post_route_parasitics.spef  (Parasitic data)"
    puts "  - parasitics_summary.txt      (Extraction summary)"
    
    # Show SPEF file size and line count
    puts ""
    puts "SPEF file statistics:"
    set spef_size [file size post_route_parasitics.spef]
    puts "  File size: [expr $spef_size / 1024] KB"
    
} else {
    puts "❌ Error: SPEF extraction failed!"
    exit 1
}

puts "================================================="