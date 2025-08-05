#!/bin/bash
# Try to load EDA tools using module system

echo "Attempting to load EDA modules..."

# Common module names for OpenROAD and related tools
POSSIBLE_MODULES=(
    "openroad"
    "OpenROAD" 
    "eda"
    "EDA"
    "vlsi"
    "VLSI"
    "digital"
    "asic"
    "openroad-flow"
    "openroad-flow-scripts"
    "yosys"
    "sta"
    "opensta"
)

# Function to try loading a module
try_load_module() {
    local module_name=$1
    echo -n "Trying to load module '$module_name': "
    
    if command -v module &> /dev/null; then
        if module load "$module_name" 2>/dev/null; then
            echo "✅ Success"
            return 0
        else
            echo "❌ Failed"
            return 1
        fi
    elif command -v ml &> /dev/null; then
        if ml "$module_name" 2>/dev/null; then
            echo "✅ Success"
            return 0
        else
            echo "❌ Failed"
            return 1
        fi
    else
        echo "❌ No module system"
        return 1
    fi
}

# Try loading modules
echo "=========================================="
echo "Attempting to Load EDA Modules"
echo "=========================================="

LOADED_MODULES=()
for module in "${POSSIBLE_MODULES[@]}"; do
    if try_load_module "$module"; then
        LOADED_MODULES+=("$module")
    fi
done

echo ""
echo "Results:"
echo "--------"
if [[ ${#LOADED_MODULES[@]} -gt 0 ]]; then
    echo "✅ Successfully loaded modules:"
    for module in "${LOADED_MODULES[@]}"; do
        echo "   - $module"
    done
else
    echo "❌ No modules could be loaded"
fi

echo ""
echo "Current tool availability after loading modules:"
echo "================================================"
echo -n "OpenROAD: "
if command -v openroad &> /dev/null; then
    echo "✅ Available at $(which openroad)"
else
    echo "❌ Still not available"
fi

echo -n "OpenSTA: "
if command -v sta &> /dev/null; then
    echo "✅ Available at $(which sta)"
else
    echo "❌ Still not available"
fi

echo -n "Yosys: "
if command -v yosys &> /dev/null; then
    echo "✅ Available at $(which yosys)"
else
    echo "❌ Still not available"
fi