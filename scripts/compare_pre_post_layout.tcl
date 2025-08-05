# Compare pre-layout vs post-layout timing results
# This script helps analyze the impact of physical implementation

puts "==================================================="
puts "Pre-layout vs Post-layout Timing Comparison"
puts "==================================================="

# Function to extract slack values from report files
proc extract_slack {filename} {
    if {[file exists $filename]} {
        set fp [open $filename r]
        set content [read $fp]
        close $fp
        # Extract numerical slack value (this is a simplified extraction)
        if {[regexp {(-?\d+\.?\d*)} $content slack]} {
            return $slack
        }
    }
    return "N/A"
}

# Compare setup timing
puts "\n1. SETUP TIMING COMPARISON:"
puts "-----------------------------"
set pre_wns [extract_slack "report/timing_wns.txt"]
set post_wns [extract_slack "post_layout_timing_wns.txt"]
puts "Pre-layout WNS:  $pre_wns ns"
puts "Post-layout WNS: $post_wns ns"

if {$pre_wns != "N/A" && $post_wns != "N/A"} {
    set degradation [expr $pre_wns - $post_wns]
    puts "Timing degradation: $degradation ns"
}

# Compare total negative slack
puts "\n2. TOTAL NEGATIVE SLACK COMPARISON:"
puts "------------------------------------"
set pre_tns [extract_slack "report/timing_tns.txt"]  
set post_tns [extract_slack "post_layout_timing_tns.txt"]
puts "Pre-layout TNS:  $pre_tns ns"
puts "Post-layout TNS: $post_tns ns"

# Hold timing comparison
puts "\n3. HOLD TIMING COMPARISON:"
puts "---------------------------" 
puts "Pre-layout hold analysis available in: report/timing_hold_report.txt"
puts "Post-layout hold analysis available in: post_layout_timing_hold_report.txt"

puts "\n4. RECOMMENDATIONS:"
puts "-------------------"
if {$post_wns != "N/A" && $post_wns < 0} {
    puts "⚠️  SETUP VIOLATIONS DETECTED in post-layout!"
    puts "   Consider: relaxing constraints, design optimization, or physical fixes"
}
if {$pre_wns != "N/A" && $post_wns != "N/A" && [expr $pre_wns - $post_wns] > 1.0} {
    puts "⚠️  SIGNIFICANT TIMING DEGRADATION (>1ns) detected!"
    puts "   Consider: improving floorplan, routing optimization"
}
puts "✅ Check post_layout_summary.txt for detailed analysis"
puts "==================================================="