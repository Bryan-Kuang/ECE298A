#!/bin/bash
# Check for available EDA tools on the system

echo "=========================================="
echo "Checking for EDA Tools on Remote Server"
echo "=========================================="

# Check if module system is available
echo "1. Checking module system..."
if command -v module &> /dev/null; then
    echo "✅ Module system found!"
    echo ""
    echo "Available EDA modules:"
    module avail 2>&1 | grep -i -E "(openroad|eda|synopsys|cadence|mentor|open)" || echo "   No EDA modules found with 'module avail'"
    echo ""
    echo "Try searching for OpenROAD specifically:"
    module avail openroad 2>&1 || echo "   No openroad module found"
    echo ""
    echo "Try searching for general EDA/VLSI tools:"
    module avail 2>&1 | grep -i -E "(vlsi|asic|digital)" || echo "   No VLSI-related modules found"
elif command -v ml &> /dev/null; then
    echo "✅ Lmod system found!"
    echo ""
    echo "Available EDA modules:"
    ml avail 2>&1 | grep -i -E "(openroad|eda|synopsys|cadence|mentor)" || echo "   No EDA modules found"
else
    echo "❌ No module system (module/ml) found"
fi

echo ""
echo "2. Checking for directly available tools..."

# Check for OpenROAD
echo -n "OpenROAD: "
if command -v openroad &> /dev/null; then
    echo "✅ Found at $(which openroad)"
    openroad -version 2>/dev/null || echo "   (version check failed)"
else
    echo "❌ Not found"
fi

# Check for OpenSTA
echo -n "OpenSTA: "
if command -v sta &> /dev/null; then
    echo "✅ Found at $(which sta)"
    sta -version 2>/dev/null || echo "   (version check failed)"
else
    echo "❌ Not found"
fi

# Check for other EDA tools
echo -n "Yosys: "
if command -v yosys &> /dev/null; then
    echo "✅ Found at $(which yosys)"
else
    echo "❌ Not found"
fi

echo -n "Magic: "
if command -v magic &> /dev/null; then
    echo "✅ Found at $(which magic)"
else
    echo "❌ Not found"
fi

echo -n "Klayout: "
if command -v klayout &> /dev/null; then
    echo "✅ Found at $(which klayout)"
else
    echo "❌ Not found"
fi

echo ""
echo "3. Checking system information..."
echo "Operating System: $(uname -a)"
echo "Architecture: $(uname -m)"
echo "Distribution: "
if [[ -f /etc/os-release ]]; then
    cat /etc/os-release | grep PRETTY_NAME
elif [[ -f /etc/redhat-release ]]; then
    cat /etc/redhat-release
elif [[ -f /etc/debian_version ]]; then
    echo "Debian $(cat /etc/debian_version)"
fi

echo ""
echo "4. Checking common installation paths..."
COMMON_PATHS=(
    "/usr/local/bin/openroad"
    "/opt/openroad/bin/openroad"
    "/tools/openroad/bin/openroad"
    "/software/openroad/bin/openroad"
    "/usr/bin/openroad"
    "$HOME/.local/bin/openroad"
    "/snap/bin/openroad"
)

echo "Looking for OpenROAD in common paths:"
for path in "${COMMON_PATHS[@]}"; do
    if [[ -f "$path" ]]; then
        echo "✅ Found OpenROAD at: $path"
    fi
done

echo ""
echo "5. Environment information..."
echo "PATH: $PATH"
echo "USER: $USER"
echo "HOME: $HOME"

echo ""
echo "=========================================="
echo "Summary and Recommendations:"
echo "=========================================="

if command -v module &> /dev/null; then
    echo "💡 You have a module system. Try:"
    echo "   module load openroad"
    echo "   module load eda"
    echo "   module load vlsi"
elif command -v ml &> /dev/null; then
    echo "💡 You have Lmod. Try:"
    echo "   ml openroad"
    echo "   ml eda"
fi

echo ""
echo "💡 If no modules found, you may need to:"
echo "   1. Install OpenROAD manually"
echo "   2. Contact system administrator"
echo "   3. Use alternative tools/approaches"
echo ""
echo "💡 Alternative approaches:"
echo "   1. Use Docker containers"
echo "   2. Use pre-built binaries"
echo "   3. Use online EDA platforms"