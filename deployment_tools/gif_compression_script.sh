#!/bin/bash

# Path to the assets folder
ASSETS_DIR="../assets"

# Path to the Python script responsible for compressing GIFs
COMPRESS_SCRIPT="./compress_gif.py"

# Path to the virtual environment
VENV_DIR="../venv"

# Size limit for GIFs in MB (Discord limits are 8MB for free accounts)
MAX_SIZE_MB=8

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please create one using 'python3 -m venv venv' and install requirements."
    exit 1
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
pip install Pillow

# Function to compress a single GIF
compress_gif() {
    local input_file="$1"
    local temp_file="${input_file%.gif}.compressed.gif"

    echo "Processing: $input_file"
    # Call the Python compress script using the virtual environment
    python "$COMPRESS_SCRIPT" "$input_file" "$temp_file"

    # Check if the temporary file exists and is smaller than the original
    if [ -f "$temp_file" ]; then
        original_size=$(wc -c <"$input_file")
        compressed_size=$(wc -c <"$temp_file")

        if [ "$compressed_size" -lt "$original_size" ]; then
            mv "$temp_file" "$input_file"  # Replace the original file with the compressed version
            echo "Compressed $input_file successfully (Size: $(($compressed_size / 1024)) KB)"
        else
            rm "$temp_file"  # Remove the temporary file if compression didn't reduce size
            echo "Skipped $input_file: compression did not reduce size."
        fi
    else
        echo "Failed to compress $input_file"
    fi
}

# Ensure the assets directory exists
if [ ! -d "$ASSETS_DIR" ]; then
    echo "Error: $ASSETS_DIR does not exist."
    deactivate  # Deactivate virtual environment before exiting
    exit
fi

# Process all GIFs in the assets folder
compress_gif "$ASSETS_DIR/gifs/welcome.gif"
compress_gif "$ASSETS_DIR/gifs/lider_conselho_politico.gif"
