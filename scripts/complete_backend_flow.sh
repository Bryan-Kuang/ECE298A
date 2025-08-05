#!/bin/bash
# Complete backend flow: Synthesis → PnR → SPEF → Post-layout STA
# Bryan Kuang MAC peripheral backend automation

echo "================================================================="
echo "Complete Backend Flow for MAC Peripheral"
echo "Starting from synthesized netlist → Post-layout STA"
echo "================================================================="

# Check prerequisites
echo "Step 0: Checking prerequisites..."

REQUIRED_FILES=("netlist.v" "sky130_fd_sc_hd__tt_025C_1v80.lib" "constraints.sdc")
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ ERROR: Required file '$file' not found!"
        exit 1
    fi
done

# Check if OpenROAD is available
if ! command -v openroad &> /dev/null; then
    echo "❌ ERROR: OpenROAD not found in PATH!"
    echo "   Please install OpenROAD or load the appropriate module"
    exit 1
fi

# Check if STA is available
if ! command -v sta &> /dev/null; then
    echo "❌ ERROR: OpenSTA not found in PATH!"
    echo "   Please install OpenSTA or load the appropriate module"
    exit 1
fi

echo "✅ All prerequisites satisfied!"

# Create necessary configuration files
echo ""
echo "Step 1: Creating technology configuration files..."
./create_tech_files.sh

# Step 1: Place and Route
echo ""
echo "Step 2: Running Place and Route with OpenROAD..."
echo "This may take several minutes..."

if openroad openroad_pnr.tcl > pnr.log 2>&1; then
    echo "✅ Place and Route completed successfully!"
    echo "   Check pnr.log for detailed information"
else
    echo "❌ Place and Route failed!"
    echo "   Check pnr.log for error details:"
    tail -20 pnr.log
    exit 1
fi

# Verify PnR outputs
if [[ ! -f "post_route_design.db" ]] || [[ ! -f "post_route_netlist.v" ]]; then
    echo "❌ ERROR: PnR did not generate required output files!"
    exit 1
fi

# Step 2: SPEF Extraction
echo ""
echo "Step 3: Extracting parasitic parameters (SPEF)..."

if openroad spef_extraction.tcl > spef_extraction.log 2>&1; then
    echo "✅ SPEF extraction completed successfully!"
    echo "   Check spef_extraction.log for detailed information"
else
    echo "❌ SPEF extraction failed!"
    echo "   Check spef_extraction.log for error details:"
    tail -10 spef_extraction.log
    exit 1
fi

# Verify SPEF output
if [[ ! -f "post_route_parasitics.spef" ]]; then
    echo "❌ ERROR: SPEF extraction did not generate parasitic file!"
    exit 1
fi

# Step 3: Post-layout STA
echo ""
echo "Step 4: Running Post-layout Static Timing Analysis..."

# Update post-layout STA script to use actual files
sed -i.bak \
    -e "s|read_verilog netlist.v|read_verilog post_route_netlist.v|" \
    -e "s|# read_spef parasitic.spef|read_spef post_route_parasitics.spef|" \
    timing_post_layout.tcl

if sta timing_post_layout.tcl > post_layout_sta.log 2>&1; then
    echo "✅ Post-layout STA completed successfully!"
    echo "   Check post_layout_sta.log for detailed information"
else
    echo "❌ Post-layout STA failed!"
    echo "   Check post_layout_sta.log for error details:"
    tail -10 post_layout_sta.log
    exit 1
fi

# Step 4: Generate comparison report
echo ""
echo "Step 5: Generating pre-layout vs post-layout comparison..."

if sta compare_pre_post_layout.tcl > comparison.log 2>&1; then
    echo "✅ Comparison analysis completed!"
else
    echo "⚠️  Comparison analysis had issues (check comparison.log)"
fi

# Summary
echo ""
echo "================================================================="
echo "Backend Flow Completed Successfully! 🎉"
echo "================================================================="
echo ""
echo "Generated Files:"
echo "----------------"
echo "📁 Physical Design:"
echo "   • post_route_netlist.v        - Final routed netlist"
echo "   • post_route_design.def       - Physical layout (DEF format)"
echo "   • post_route_design.db        - OpenROAD database"
echo ""
echo "📁 Parasitic Analysis:"
echo "   • post_route_parasitics.spef  - Extracted parasitics"
echo "   • parasitics_summary.txt      - Extraction summary"
echo ""
echo "📁 Timing Analysis:"
echo "   • post_layout_timing_report.txt    - Detailed timing"
echo "   • post_layout_timing_wns.txt       - Worst negative slack"
echo "   • post_layout_timing_tns.txt       - Total negative slack"
echo "   • post_layout_summary.txt          - Overall summary"
echo ""
echo "📁 Log Files:"
echo "   • pnr.log                     - Place & Route log"
echo "   • spef_extraction.log         - SPEF extraction log"
echo "   • post_layout_sta.log         - Post-layout STA log"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. Review post_layout_summary.txt for timing closure"
echo "2. Check for setup/hold violations"
echo "3. Analyze critical paths if timing fails"
echo "4. Iterate design if necessary"
echo ""
echo "================================================================="

# Quick timing summary
echo "Quick Timing Summary:"
echo "====================="
if [[ -f "post_layout_timing_wns.txt" ]]; then
    echo "Post-layout Worst Negative Slack:"
    cat post_layout_timing_wns.txt
fi
if [[ -f "post_layout_timing_tns.txt" ]]; then
    echo "Post-layout Total Negative Slack:"
    cat post_layout_timing_tns.txt
fi