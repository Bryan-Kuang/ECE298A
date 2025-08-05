#!/bin/bash
# Create necessary technology files for sky130 OpenROAD flow

echo "Creating sky130 technology configuration files..."

# Create tracks.info file for sky130
cat > tracks.info << 'EOF'
# Sky130 technology tracks information
# Format: layer_name X/Y offset pitch
# Metal layers for sky130

li1 X 0.170 0.460
li1 Y 0.170 0.340

met1 X 0.170 0.340
met1 Y 0.170 0.340

met2 X 0.230 0.460
met2 Y 0.230 0.340

met3 X 0.340 0.680
met3 Y 0.340 0.460

met4 X 0.340 0.680
met4 Y 0.340 0.680

met5 X 1.700 3.400
met5 Y 1.700 3.400
EOF

# Create basic technology LEF file (simplified)
cat > sky130_tech.lef << 'EOF'
VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

UNITS
    DATABASE MICRONS 1000 ;
END UNITS

LAYER li1
    TYPE ROUTING ;
    DIRECTION HORIZONTAL ;
    PITCH 0.460 ;
    WIDTH 0.170 ;
    SPACING 0.170 ;
    RESISTANCE RPERSQ 12.8 ;
    CAPACITANCE CPERSQDIST 1.644e-4 ;
END li1

LAYER met1
    TYPE ROUTING ;
    DIRECTION VERTICAL ;
    PITCH 0.340 ;
    WIDTH 0.140 ;
    SPACING 0.140 ;
    RESISTANCE RPERSQ 0.125 ;
    CAPACITANCE CPERSQDIST 1.449e-4 ;
END met1

LAYER met2
    TYPE ROUTING ;
    DIRECTION HORIZONTAL ;
    PITCH 0.460 ;
    WIDTH 0.140 ;
    SPACING 0.140 ;
    RESISTANCE RPERSQ 0.125 ;
    CAPACITANCE CPERSQDIST 1.331e-4 ;
END met2

LAYER met3
    TYPE ROUTING ;
    DIRECTION VERTICAL ;
    PITCH 0.680 ;
    WIDTH 0.300 ;
    SPACING 0.300 ;
    RESISTANCE RPERSQ 0.047 ;
    CAPACITANCE CPERSQDIST 1.013e-4 ;
END met3

LAYER met4
    TYPE ROUTING ;
    DIRECTION HORIZONTAL ;
    PITCH 0.680 ;
    WIDTH 0.300 ;
    SPACING 0.300 ;
    RESISTANCE RPERSQ 0.047 ;
    CAPACITANCE CPERSQDIST 1.013e-4 ;
END met4

LAYER met5
    TYPE ROUTING ;
    DIRECTION VERTICAL ;
    PITCH 3.400 ;
    WIDTH 1.600 ;
    SPACING 1.600 ;
    RESISTANCE RPERSQ 0.029 ;
    CAPACITANCE CPERSQDIST 9.109e-5 ;
END met5

SITE unithd
    CLASS CORE ;
    SIZE 0.460 BY 2.720 ;
END unithd

END LIBRARY
EOF

# Create power planning configuration
cat > power_config.tcl << 'EOF'
# Power planning configuration for TinyTapeout design

# VDD/VSS net names (adjust if different in your design)
set power_nets "VDD VPWR"
set ground_nets "VSS VGND"

# Power ring configuration (for larger designs)
# For TinyTapeout, this might not be needed
set power_ring_width 2.0
set power_ring_spacing 1.0
EOF

# Create floorplan constraints
cat > floorplan_config.tcl << 'EOF'
# Floorplan configuration for MAC peripheral
# TinyTapeout has a fixed tile size

# Die area (adjust based on TinyTapeout specifications)
set die_width 100
set die_height 100

# Core area (leave margin for I/O and power)
set core_margin 5
set core_width [expr $die_width - 2 * $core_margin]
set core_height [expr $die_height - 2 * $core_margin]

puts "Floorplan configuration:"
puts "  Die area: ${die_width} x ${die_height}"
puts "  Core area: ${core_width} x ${core_height}"
EOF

echo "✅ Technology configuration files created:"
echo "   • tracks.info         - Metal layer routing tracks"
echo "   • sky130_tech.lef     - Basic technology LEF"
echo "   • power_config.tcl    - Power planning settings"
echo "   • floorplan_config.tcl - Floorplan constraints"