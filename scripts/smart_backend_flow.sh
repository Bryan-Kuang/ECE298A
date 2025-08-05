#!/bin/bash
# Smart backend flow - tries multiple approaches based on available tools

echo "================================================================="
echo "Smart Backend Flow - MAC Peripheral"
echo "Automatically detects available tools and runs appropriate flow"
echo "================================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to try loading modules
try_load_modules() {
    echo "🔄 Attempting to load EDA modules..."
    if [[ -f "load_eda_modules.sh" ]]; then
        chmod +x load_eda_modules.sh
        ./load_eda_modules.sh
        return $?
    else
        echo "⚠️  Module loading script not found"
        return 1
    fi
}

# Function to check Docker availability
check_docker() {
    if command_exists docker; then
        if docker info >/dev/null 2>&1; then
            echo "✅ Docker available and running"
            return 0
        else
            echo "⚠️  Docker installed but not running"
            return 1
        fi
    else
        echo "❌ Docker not available"
        return 1
    fi
}

# Function to run full OpenROAD flow
run_full_openroad_flow() {
    echo ""
    echo "🚀 Running Full OpenROAD Backend Flow"
    echo "====================================="
    
    if [[ -f "complete_backend_flow.sh" ]]; then
        chmod +x complete_backend_flow.sh
        ./complete_backend_flow.sh
        return $?
    else
        echo "❌ Complete backend flow script not found"
        return 1
    fi
}

# Function to run Docker-based flow
run_docker_flow() {
    echo ""
    echo "🐳 Running Docker-based Backend Flow"
    echo "===================================="
    
    if [[ -f "docker_openroad.sh" ]]; then
        chmod +x docker_openroad.sh
        ./docker_openroad.sh
        return $?
    else
        echo "❌ Docker flow script not found"
        return 1
    fi
}

# Function to run simplified analysis
run_simplified_analysis() {
    echo ""
    echo "📊 Running Simplified Post-Layout Analysis"
    echo "=========================================="
    
    if command_exists sta; then
        if [[ -f "simplified_post_layout_analysis.tcl" ]]; then
            sta simplified_post_layout_analysis.tcl
            return $?
        else
            echo "❌ Simplified analysis script not found"
            return 1
        fi
    else
        echo "❌ OpenSTA not available for simplified analysis"
        return 1
    fi
}

# Main flow logic
echo ""
echo "Step 1: Checking prerequisites..."
echo "================================="

# Check required files
REQUIRED_FILES=("netlist.v" "sky130_fd_sc_hd__tt_025C_1v80.lib" "constraints.sdc")
for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ ERROR: Required file '$file' not found!"
        exit 1
    fi
done
echo "✅ All required files present"

# Check for existing pre-layout results
if [[ -d "report" ]]; then
    echo "✅ Pre-layout STA results found for comparison"
else
    echo "⚠️  No pre-layout results found"
fi

echo ""
echo "Step 2: Detecting available tools..."
echo "===================================="

# Check current tool availability
echo "Current tool status:"
echo -n "  OpenROAD: "
if command_exists openroad; then
    echo "✅ Available"
    OPENROAD_AVAILABLE=true
else
    echo "❌ Not available"
    OPENROAD_AVAILABLE=false
fi

echo -n "  OpenSTA: "
if command_exists sta; then
    echo "✅ Available"
    STA_AVAILABLE=true
else
    echo "❌ Not available"
    STA_AVAILABLE=false
fi

echo -n "  Docker: "
if check_docker; then
    DOCKER_AVAILABLE=true
else
    DOCKER_AVAILABLE=false
fi

# Try to improve tool availability
if [[ "$OPENROAD_AVAILABLE" == false ]]; then
    echo ""
    echo "Step 3: Attempting to load EDA tools..."
    echo "======================================"
    
    try_load_modules
    
    # Re-check after module loading
    echo ""
    echo "Re-checking tool availability after module loading:"
    if command_exists openroad; then
        echo "✅ OpenROAD now available!"
        OPENROAD_AVAILABLE=true
    else
        echo "❌ OpenROAD still not available"
    fi
    
    if command_exists sta; then
        echo "✅ OpenSTA now available!"
        STA_AVAILABLE=true
    else
        echo "❌ OpenSTA still not available"
    fi
fi

echo ""
echo "Step 4: Determining optimal flow..."
echo "=================================="

# Decision logic for which flow to run
if [[ "$OPENROAD_AVAILABLE" == true && "$STA_AVAILABLE" == true ]]; then
    echo "🎯 Running FULL BACKEND FLOW (OpenROAD + OpenSTA)"
    run_full_openroad_flow
    FLOW_STATUS=$?
    
elif [[ "$DOCKER_AVAILABLE" == true ]]; then
    echo "🎯 Running DOCKER-BASED FLOW"
    run_docker_flow
    FLOW_STATUS=$?
    
elif [[ "$STA_AVAILABLE" == true ]]; then
    echo "🎯 Running SIMPLIFIED ANALYSIS (OpenSTA only)"
    echo "⚠️  This provides estimated post-layout results"
    run_simplified_analysis
    FLOW_STATUS=$?
    
else
    echo "❌ No suitable tools available for backend flow!"
    echo ""
    echo "Options to resolve:"
    echo "1. Install OpenROAD and OpenSTA"
    echo "2. Install Docker and use containerized flow"
    echo "3. Contact system administrator for EDA tool access"
    echo "4. Use remote EDA platforms"
    exit 1
fi

echo ""
echo "================================================================="
if [[ $FLOW_STATUS -eq 0 ]]; then
    echo "✅ Backend Flow Completed Successfully!"
    echo ""
    echo "Check the following files for results:"
    if [[ -f "post_layout_summary.txt" ]]; then
        echo "  📊 post_layout_summary.txt - Full analysis summary"
    elif [[ -f "simplified_post_layout_summary.txt" ]]; then
        echo "  📊 simplified_post_layout_summary.txt - Simplified analysis summary"
    fi
    
    if [[ -f "post_layout_timing_wns.txt" ]]; then
        echo "  ⚡ post_layout_timing_wns.txt - Timing results"
    elif [[ -f "simplified_post_layout_timing_wns.txt" ]]; then
        echo "  ⚡ simplified_post_layout_timing_wns.txt - Estimated timing"
    fi
    
else
    echo "❌ Backend Flow Failed!"
    echo ""
    echo "Check log files for error details:"
    echo "  📋 *.log files in current directory"
fi
echo "================================================================="