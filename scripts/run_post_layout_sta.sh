#!/bin/bash
# Post-layout STA analysis workflow

echo "==================================================="
echo "Post-layout STA Analysis for MAC Peripheral"
echo "==================================================="

# Check if required files exist
echo "Checking for required files..."

if [[ ! -f "sky130_fd_sc_hd__tt_025C_1v80.lib" ]]; then
    echo "❌ ERROR: Liberty file not found!"
    exit 1
fi

if [[ ! -f "constraints.sdc" ]]; then
    echo "❌ ERROR: Constraints file not found!"
    exit 1
fi

# Check for post-layout files
POST_LAYOUT_NETLIST=""
PARASITIC_FILE=""

# Look for post-route netlist
for netlist in post_route_netlist.v final_netlist.v *post*.v; do
    if [[ -f "$netlist" ]]; then
        POST_LAYOUT_NETLIST="$netlist"
        break
    fi
done

# Look for parasitic files
for parasitic in *.spef *.sdf parasitic.*; do
    if [[ -f "$parasitic" ]]; then
        PARASITIC_FILE="$parasitic"
        break
    fi
done

if [[ -z "$POST_LAYOUT_NETLIST" ]]; then
    echo "⚠️  WARNING: No post-layout netlist found!"
    echo "    Using original netlist.v (this will be pre-layout analysis)"
    echo "    To get true post-layout results, you need to run P&R first."
    POST_LAYOUT_NETLIST="netlist.v"
else
    echo "✅ Found post-layout netlist: $POST_LAYOUT_NETLIST"
fi

if [[ -z "$PARASITIC_FILE" ]]; then
    echo "⚠️  WARNING: No parasitic file found!"
    echo "    Analysis will use wire load models (less accurate)"
else
    echo "✅ Found parasitic file: $PARASITIC_FILE"
fi

# Update timing script with actual file names
sed -i.bak \
    -e "s|read_verilog netlist.v|read_verilog $POST_LAYOUT_NETLIST|" \
    -e "s|# read_spef parasitic.spef|read_spef $PARASITIC_FILE|" \
    timing_post_layout.tcl

echo ""
echo "Running post-layout STA analysis..."
sta timing_post_layout.tcl

echo ""
echo "Comparing pre-layout vs post-layout results..."
sta compare_pre_post_layout.tcl

echo "==================================================="
echo "Analysis complete! Check these files:"
echo "📊 post_layout_summary.txt      - Overall summary"
echo "📈 post_layout_timing_report.txt - Detailed timing"
echo "⚡ post_layout_timing_wns.txt   - Worst slack"
echo "🔍 post_layout_top10_paths.txt  - Critical paths"
echo "==================================================="