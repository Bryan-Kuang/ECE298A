# Complete Backend Flow Guide

## From Synthesis to Post-Layout STA

### 🎯 Overview

This guide walks you through the complete backend implementation flow for the Bryan Kuang MAC peripheral, from synthesized netlist to post-layout static timing analysis.

### 📋 Prerequisites

- ✅ `netlist.v` - Synthesized netlist (you have this)
- ✅ `sky130_fd_sc_hd__tt_025C_1v80.lib` - Standard cell library (you have this)
- ✅ `constraints.sdc` - Timing constraints (you have this)
- 🔧 OpenROAD - For Place & Route
- 🔧 OpenSTA - For timing analysis

### 🚀 Quick Start (One Command)

```bash
# Make scripts executable and run complete flow
chmod +x *.sh
./complete_backend_flow.sh
```

### 🔄 Step-by-Step Manual Flow

If you prefer to run each step manually:

#### Step 1: Create Technology Files

```bash
chmod +x create_tech_files.sh
./create_tech_files.sh
```

#### Step 2: Place & Route

```bash
openroad openroad_pnr.tcl
```

#### Step 3: Extract Parasitics

```bash
openroad spef_extraction.tcl
```

#### Step 4: Post-Layout STA

```bash
sta timing_post_layout.tcl
```

#### Step 5: Compare Results

```bash
sta compare_pre_post_layout.tcl
```

### 📊 Generated Files

After successful completion, you'll have:

**Physical Design:**

- `post_route_netlist.v` - Final routed netlist
- `post_route_design.def` - Physical layout (DEF format)
- `post_route_design.db` - OpenROAD database

**Parasitic Analysis:**

- `post_route_parasitics.spef` - Extracted RC parasitics
- `parasitics_summary.txt` - Extraction summary

**Timing Analysis:**

- `post_layout_timing_report.txt` - Detailed timing paths
- `post_layout_timing_wns.txt` - Worst Negative Slack
- `post_layout_timing_tns.txt` - Total Negative Slack
- `post_layout_summary.txt` - Overall summary

### 🔍 How to Interpret Results

#### Timing Closure Check:

```bash
# Check worst setup slack
cat post_layout_timing_wns.txt
# Should be positive for timing closure

# Check total negative slack
cat post_layout_timing_tns.txt
# Should be 0 for no violations

# Review critical paths
grep "slack" post_layout_timing_report.txt
```

#### Success Criteria:

- ✅ **Setup Time**: WNS ≥ 0 ns
- ✅ **Hold Time**: No negative hold slack
- ✅ **No DRC Violations**: Check `post_route_drc.rpt`

### 🛠️ Troubleshooting

#### Common Issues:

**PnR Fails:**

- Check `pnr.log` for errors
- Verify floorplan constraints in `floorplan_config.tcl`
- Adjust placement density if congested

**SPEF Extraction Fails:**

- Ensure `post_route_design.db` exists
- Check if routing completed successfully
- Verify technology parameters

**Timing Violations:**

- Review critical paths in timing reports
- Consider design optimization
- Adjust timing constraints if appropriate

**File Not Found Errors:**

- Ensure all prerequisite files exist
- Check file permissions
- Verify current working directory

### 📞 Getting Help

If you encounter issues:

1. Check the log files (`.log` extensions)
2. Review error messages in detail
3. Verify all input files are present and valid
4. Check OpenROAD/OpenSTA installation

### 🎉 Success!

If all steps complete successfully, you now have:

- A placed and routed design
- Accurate parasitic extraction
- Post-layout timing analysis
- Comparison with pre-layout results

This represents a complete backend implementation ready for tapeout!
