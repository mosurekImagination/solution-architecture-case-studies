#!/bin/bash

# Script to generate diagrams for case studies using Docker Compose
# Usage: ./generate-diagrams.sh [case_study_number|latest]
# Example: ./generate-diagrams.sh 01
#          ./generate-diagrams.sh latest  (default)
#          ./generate-diagrams.sh all     (generate all case studies)

set -e  # Exit on error

# Function to find all case study directories
find_case_studies() {
    find . -maxdepth 1 -type d -name '[0-9][0-9]' | sort
}

# Function to get the latest case study number
get_latest_case_study() {
    find_case_studies | tail -1 | sed 's|^\./||'
}

# Function to generate diagrams for a specific case study
generate_case_study() {
    local case_study=$1
    local case_study_dir="./${case_study}"
    
    if [ ! -d "$case_study_dir" ]; then
        echo "❌ Case study directory '$case_study_dir' not found!"
        return 1
    fi
    
    # Find all Python files in the case study directory
    local python_files=$(find "$case_study_dir" -maxdepth 1 -name "*.py" | sort)
    
    if [ -z "$python_files" ]; then
        echo "⚠️  No Python files found in $case_study_dir"
        return 0
    fi
    
    echo "📂 Processing case study: $case_study"
    echo "   Found Python files:"
    echo "$python_files" | sed 's|^|     - |'
    
    # Run each Python file
    local file_count=0
    while IFS= read -r python_file; do
        if [ -n "$python_file" ]; then
            file_count=$((file_count + 1))
            filename=$(basename "$python_file" .py)
            echo ""
            echo "   🎨 Generating diagram from: $(basename $python_file)"
            
            # Create diagrams directory inside case study folder
            mkdir -p "${case_study_dir}/diagrams"
            
            # Convert relative path to path inside container
            # Remove leading ./ if present
            python_file_clean="${python_file#./}"
            python_file_in_container="/app/${python_file_clean}"
            
            # Run the diagram generation
            docker-compose run --rm \
                -e CASE_STUDY_DIR="$case_study" \
                -e PYTHON_FILE="$python_file_in_container" \
                -e OUTPUT_DIR="/app/${case_study}/diagrams" \
                diagrams python "$python_file_in_container"
        fi
    done <<< "$python_files"
    
    if [ $file_count -gt 0 ]; then
        echo ""
        echo "   ✅ Generated $file_count diagram(s) for case study $case_study"
        echo "   📁 Diagrams directory: ${case_study}/diagrams/"
    fi
}

# Parse arguments
CASE_STUDY_ARG="${1:-latest}"

echo "🚀 Starting diagram generation with Docker..."

# Build the image first (if needed)
echo "📦 Building Docker image..."
docker-compose build

# Handle different modes
if [ "$CASE_STUDY_ARG" = "all" ]; then
    echo ""
    echo "🔄 Generating diagrams for ALL case studies..."
    echo ""
    
    case_studies=$(find_case_studies)
    if [ -z "$case_studies" ]; then
        echo "❌ No case study directories found!"
        echo "   Create numbered directories (e.g., 01, 02, 03) with Python files inside."
        exit 1
    fi
    
    total=0
    while IFS= read -r case_study_dir; do
        case_study=$(basename "$case_study_dir")
        generate_case_study "$case_study"
        total=$((total + 1))
    done <<< "$case_studies"
    
    echo ""
    echo "✅ Generated diagrams for $total case study(ies)"
    
elif [ "$CASE_STUDY_ARG" = "latest" ]; then
    latest=$(get_latest_case_study)
    
    if [ -z "$latest" ]; then
        echo "❌ No case study directories found!"
        echo "   Create numbered directories (e.g., 01, 02, 03) with Python files inside."
        exit 1
    fi
    
    echo ""
    echo "📌 Generating diagrams for LATEST case study: $latest"
    echo ""
    generate_case_study "$latest"
    
else
    # Specific case study number
    echo ""
    echo "📌 Generating diagrams for case study: $CASE_STUDY_ARG"
    echo ""
    generate_case_study "$CASE_STUDY_ARG"
fi

# Clean up any remaining containers/networks (if any)
echo ""
echo "🧹 Cleaning up Docker resources..."
docker-compose down 2>/dev/null || true

echo ""
echo "✨ Done!"
echo ""
echo "📁 All generated diagrams are in each case study's 'diagrams/' directory"
