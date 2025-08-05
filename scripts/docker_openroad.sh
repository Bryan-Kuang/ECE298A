#!/bin/bash
# Run OpenROAD flow using Docker container

echo "=========================================="
echo "Running OpenROAD via Docker Container"
echo "=========================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker or use another method."
    exit 1
fi

echo "✅ Docker found: $(docker --version)"

# OpenROAD Docker image
OPENROAD_IMAGE="openroad/openroad:latest"

# Check if image exists, if not pull it
echo ""
echo "Checking OpenROAD Docker image..."
if ! docker image inspect "$OPENROAD_IMAGE" &> /dev/null; then
    echo "🔄 Pulling OpenROAD Docker image (this may take a while)..."
    docker pull "$OPENROAD_IMAGE"
else
    echo "✅ OpenROAD Docker image already available"
fi

# Function to run OpenROAD command in container
run_openroad_docker() {
    local script_file=$1
    echo "🐳 Running OpenROAD script: $script_file"
    
    docker run --rm \
        -v "$(pwd):/work" \
        -w /work \
        "$OPENROAD_IMAGE" \
        openroad "$script_file"
}

# Function to run OpenSTA command in container  
run_sta_docker() {
    local script_file=$1
    echo "🐳 Running OpenSTA script: $script_file"
    
    docker run --rm \
        -v "$(pwd):/work" \
        -w /work \
        "$OPENROAD_IMAGE" \
        sta "$script_file"
}

echo ""
echo "=========================================="
echo "Running Complete Backend Flow via Docker"
echo "=========================================="

# Step 1: Create tech files
echo "Step 1: Creating technology files..."
./create_tech_files.sh

# Step 2: Place & Route
echo ""
echo "Step 2: Running Place & Route..."
if [[ -f "openroad_pnr.tcl" ]]; then
    run_openroad_docker "openroad_pnr.tcl"
else
    echo "❌ openroad_pnr.tcl not found!"
    exit 1
fi

# Step 3: SPEF Extraction
echo ""
echo "Step 3: Running SPEF extraction..."
if [[ -f "spef_extraction.tcl" ]]; then
    run_openroad_docker "spef_extraction.tcl"
else
    echo "❌ spef_extraction.tcl not found!"
    exit 1
fi

# Step 4: Post-layout STA
echo ""
echo "Step 4: Running Post-layout STA..."
if [[ -f "timing_post_layout.tcl" ]]; then
    # Update script to use actual files
    sed -i.bak \
        -e "s|read_verilog netlist.v|read_verilog post_route_netlist.v|" \
        -e "s|# read_spef parasitic.spef|read_spef post_route_parasitics.spef|" \
        timing_post_layout.tcl
    
    run_sta_docker "timing_post_layout.tcl"
else
    echo "❌ timing_post_layout.tcl not found!"
    exit 1
fi

# Step 5: Comparison
echo ""
echo "Step 5: Running comparison analysis..."
if [[ -f "compare_pre_post_layout.tcl" ]]; then
    run_sta_docker "compare_pre_post_layout.tcl"
fi

echo ""
echo "=========================================="
echo "Docker-based Backend Flow Completed!"
echo "=========================================="