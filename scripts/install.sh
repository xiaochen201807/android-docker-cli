#!/data/data/com.termux/files/usr/bin/sh

# Automated installer for android-docker-cli on Termux

# --- Configuration ---
GITHUB_REPO="https://github.com/xiaochen201807/android-docker-cli.git"
INSTALL_DIR="$HOME/.android-docker-cli"
CMD_NAME="docker"
CMD_PATH="/data/data/com.termux/files/usr/bin/$CMD_NAME"
DOCKER_COMPOSE_CMD_NAME="docker-compose"
DOCKER_COMPOSE_CMD_PATH="/data/data/com.termux/files/usr/bin/$DOCKER_COMPOSE_CMD_NAME"

# --- Helper Functions ---
echo_info() {
    echo "[INFO] $1"
}

echo_error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# --- Main Script ---

# 1. Welcome Message
echo_info "Starting installation of android-docker-cli..."

# 2. Check Dependencies
echo_info "Checking dependencies..."
for cmd in git python proot curl tar; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo_error "Dependency '$cmd' is not installed. Please install it with 'pkg install $cmd' and run this script again."
    fi
done
echo_info "✓ Dependencies are satisfied."

# 3. Clone the Repository
if [ -d "$INSTALL_DIR" ]; then
    echo_info "Existing installation found. Removing old version..."
    rm -rf "$INSTALL_DIR"
fi
echo_info "Cloning repository into $INSTALL_DIR..."
git clone "$GITHUB_REPO" "$INSTALL_DIR"
if [ $? -ne 0 ]; then
    echo_error "Failed to clone the repository. Please check your internet connection and permissions."
fi
echo_info "✓ Repository cloned successfully."

# 4. Install Python Dependencies
echo_info "Installing Python dependencies..."
if command -v pip >/dev/null 2>&1; then
    PIP_CMD="pip"
elif command -v pip3 >/dev/null 2>&1; then
    PIP_CMD="pip3"
else
    echo_error "pip or pip3 is not installed. Please install it (e.g., 'pkg install python-pip' in Termux) and run this script again."
fi

# Install from requirements.txt if it exists
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
    echo_info "Installing dependencies from requirements.txt..."
    $PIP_CMD install -r "$INSTALL_DIR/requirements.txt"
else
    echo_info "Installing basic dependencies..."
    $PIP_CMD install PyYAML psutil
fi
echo_info "✓ Python dependencies installed."

# 5. Create the Wrapper Script
echo_info "Creating command wrapper at $CMD_PATH..."
cat > "$CMD_PATH" << 'EOF'
#!/data/data/com.termux/files/usr/bin/sh

# Wrapper script for docker_cli.py
# This allows running the tool with the 'docker' command.

# Set the installation directory
INSTALL_DIR="$HOME/.android-docker-cli"

# Path to the main python script
PYTHON_SCRIPT="$INSTALL_DIR/android_docker/docker_cli.py"

# Check if the main script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: The main script was not found at $PYTHON_SCRIPT" >&2
    echo "Please try reinstalling the tool." >&2
    exit 1
fi

# Execute the python script with all passed arguments
exec env PYTHONPATH="$INSTALL_DIR" python -m android_docker.docker_cli "$@"
EOF
if [ $? -ne 0 ]; then
    echo_error "Failed to create the wrapper script. Please check permissions for $PREFIX/bin."
fi

# 6. Make the Wrapper Executable
chmod +x "$CMD_PATH"
if [ $? -ne 0 ]; then
    echo_error "Failed to make the command executable. Please check permissions."
fi
echo_info "✓ Command wrapper created and made executable."

# 7. Create docker-compose Wrapper
echo_info "Creating command wrapper at $DOCKER_COMPOSE_CMD_PATH..."
cat > "$DOCKER_COMPOSE_CMD_PATH" << 'EOF'
#!/data/data/com.termux/files/usr/bin/sh
# Wrapper for docker_compose_cli.py
INSTALL_DIR="$HOME/.android-docker-cli"
PYTHON_SCRIPT="$INSTALL_DIR/android_docker/docker_compose_cli.py"
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: The main script was not found at $PYTHON_SCRIPT" >&2
    exit 1
fi
exec env PYTHONPATH="$INSTALL_DIR" python -m android_docker.docker_compose_cli "$@"
EOF
chmod +x "$DOCKER_COMPOSE_CMD_PATH"
echo_info "✓ docker-compose command wrapper created."

# 8. Final Success Message
echo_info "-------------------------------------------------"
echo_info "  Installation successful!"
echo_info "  You can now run the tool by typing: docker"
echo_info "  And manage services with: docker-compose"
echo_info "  Example: docker run alpine:latest echo 'Hello'"
echo_info "-------------------------------------------------"
