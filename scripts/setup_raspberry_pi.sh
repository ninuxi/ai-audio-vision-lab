#!/bin/bash

# ============================================================================
# AI Audio Vision Lab - Raspberry Pi Setup Script
# Copyright (c) 2025 Antonio Mainenti
# 
# This script sets up the demo environment on Raspberry Pi 4.
# For production setup with full features, contact: oggettosonoro@gmail.com
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="AI Audio Vision Lab"
REPO_NAME="ai-audio-vision-lab"
PYTHON_VERSION="3.9"
VENV_NAME="aavl_env"

# System information
RPI_MODEL=$(cat /proc/device-tree/model 2>/dev/null || echo "Unknown")
OS_VERSION=$(lsb_release -d 2>/dev/null | cut -f2 | head -n1 || echo "Unknown")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

print_header() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}🎛️  $1${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}▶️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root"
        exit 1
    fi
}

check_raspberry_pi() {
    if [[ ! "$RPI_MODEL" =~ "Raspberry Pi" ]]; then
        print_warning "This script is optimized for Raspberry Pi"
        echo "Detected system: $RPI_MODEL"
        echo -n "Continue anyway? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_memory() {
    local memory_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local memory_gb=$((memory_kb / 1024 / 1024))
    
    if [ $memory_gb -lt 4 ]; then
        print_warning "Less than 4GB RAM detected (${memory_gb}GB)"
        print_warning "Performance may be limited. Consider Raspberry Pi 4 with 4GB+ RAM"
    else
        print_success "Memory check passed: ${memory_gb}GB RAM"
    fi
}

# ============================================================================
# SYSTEM SETUP
# ============================================================================

update_system() {
    print_step "Updating system packages..."
    sudo apt-get update -qq
    sudo apt-get upgrade -y -qq
    print_success "System updated"
}

install_system_dependencies() {
    print_step "Installing system dependencies..."
    
    # Essential packages
    local packages=(
        "python3"
        "python3-pip"
        "python3-venv"
        "python3-dev"
        "git"
        "curl"
        "wget"
        "build-essential"
        "cmake"
        "pkg-config"
    )
    
    # Audio dependencies
    packages+=(
        "libasound2-dev"
        "portaudio19-dev"
        "libsndfile1-dev"
        "pulseaudio"
        "alsa-utils"
    )
    
    # Computer vision dependencies
    packages+=(
        "libopencv-dev"
        "python3-opencv"
        "libatlas-base-dev"
        "libhdf5-dev"
        "libhdf5-serial-dev"
        "libhdf5-103"
        "libqtgui4"
        "libqtwebkit4"
        "libqt4-test"
        "python3-pyqt5"
    )
    
    # Additional utilities
    packages+=(
        "htop"
        "tree"
        "nano"
        "screen"
        "tmux"
        "zip"
        "unzip"
    )
    
    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            print_step "Installing $package..."
            sudo apt-get install -y -qq "$package" || {
                print_warning "Failed to install $package, continuing..."
            }
        fi
    done
    
    print_success "System dependencies installed"
}

configure_audio() {
    print_step "Configuring audio system..."
    
    # Add user to audio group
    sudo usermod -a -G audio $USER
    
    # Configure ALSA
    if [ ! -f ~/.asoundrc ]; then
        cat > ~/.asoundrc << EOF
pcm.!default {
    type hw
    card 0
}
ctl.!default {
    type hw
    card 0
}
EOF
        print_success "ALSA configuration created"
    fi
    
    # Test audio setup
    if command -v speaker-test >/dev/null 2>&1; then
        print_step "Testing audio system (5 seconds)..."
        timeout 5s speaker-test -c2 -twav >/dev/null 2>&1 || {
            print_warning "Audio test failed - you may need to configure audio manually"
        }
    fi
    
    print_success "Audio system configured"
}

enable_camera() {
    print_step "Checking camera configuration..."
    
    # Check if camera is enabled in config
    if ! grep -q "^camera_auto_detect=1" /boot/config.txt 2>/dev/null; then
        print_step "Enabling camera interface..."
        
        # Use raspi-config to enable camera
        sudo raspi-config nonint do_camera 0
        
        print_warning "Camera enabled - reboot required after setup completion"
    else
        print_success "Camera interface already enabled"
    fi
    
    # Install camera-specific packages
    if ! dpkg -l | grep -q "^ii  python3-picamera"; then
        print_step "Installing camera support..."
        sudo apt-get install -y -qq python3-picamera || {
            print_warning "Failed to install picamera, continuing..."
        }
    fi
}

optimize_system() {
    print_step "Applying Raspberry Pi optimizations..."
    
    # Increase GPU memory split for better performance
    local current_gpu_mem=$(vcgencmd get_mem gpu | cut -d= -f2 | cut -dM -f1)
    if [ "$current_gpu_mem" -lt 128 ]; then
        print_step "Increasing GPU memory to 128MB..."
        sudo raspi-config nonint do_memory_split 128
        print_warning "GPU memory split changed - reboot required"
    fi
    
    # Enable performance governor
    echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1 || true
    
    # Increase swap file for compilation
    local current_swap=$(free -m | awk '/^Swap:/ {print $2}')
    if [ "$current_swap" -lt 2048 ]; then
        print_step "Increasing swap file to 2GB for compilation..."
        sudo dphys-swapfile swapoff
        sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
        print_success "Swap file increased"
    fi
    
    print_success "System optimizations applied"
}

# ============================================================================
# PYTHON ENVIRONMENT SETUP
# ============================================================================

setup_python_environment() {
    print_step "Setting up Python virtual environment..."
    
    # Remove existing environment if it exists
    if [ -d "$HOME/$VENV_NAME" ]; then
        print_step "Removing existing virtual environment..."
        rm -rf "$HOME/$VENV_NAME"
    fi
    
    # Create new virtual environment
    python3 -m venv "$HOME/$VENV_NAME"
    source "$HOME/$VENV_NAME/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip wheel setuptools
    
    print_success "Python environment created: $HOME/$VENV_NAME"
}

install_python_dependencies() {
    print_step "Installing Python dependencies (this may take 20-30 minutes)..."
    
    source "$HOME/$VENV_NAME/bin/activate"
    
    # Install from piwheels for faster installation on Raspberry Pi
    pip install --extra-index-url https://www.piwheels.org/simple --no-cache-dir -r requirements.txt
    
    # Verify critical installations
    print_step "Verifying installations..."
    python -c "import torch; print(f'PyTorch: {torch.__version__}')" || print_warning "PyTorch installation issue"
    python -c "import cv2; print(f'OpenCV: {cv2.__version__}')" || print_warning "OpenCV installation issue"
    python -c "import librosa; print(f'Librosa: {librosa.__version__}')" || print_warning "Librosa installation issue"
    
    print_success "Python dependencies installed"
}

# ============================================================================
# PROJECT SETUP
# ============================================================================

clone_repository() {
    print_step "Checking project repository..."
    
    local project_dir="$HOME/$REPO_NAME"
    
    if [ -d "$project_dir" ]; then
        print_step "Project directory exists, updating..."
        cd "$project_dir"
        git pull origin main || print_warning "Failed to update repository"
    else
        print_step "Cloning repository..."
        cd "$HOME"
        git clone "https://github.com/ninuxi/$REPO_NAME.git" || {
            print_error "Failed to clone repository"
            exit 1
        }
    fi
    
    cd "$project_dir"
    print_success "Repository ready: $project_dir"
}

create_demo_assets() {
    print_step "Creating demo assets directory structure..."
    
    local assets_dir="demo/assets"
    mkdir -p "$assets_dir/sample_objects"
    mkdir -p "$assets_dir/generated_music"
    mkdir -p "$assets_dir/videos"
    
    # Create placeholder files if they don't exist
    if [ ! -f "$assets_dir/generated_music/demo_ambient.mp3" ]; then
        print_step "Demo audio files will be created when running the demo"
        touch "$assets_dir/generated_music/.gitkeep"
    fi
    
    print_success "Demo assets structure created"
}

setup_systemd_service() {
    print_step "Setting up systemd service for auto-start (optional)..."
    
    local service_file="/etc/systemd/system/ai-audio-vision-lab.service"
    local project_dir="$HOME/$REPO_NAME"
    
    if [ ! -f "$service_file" ]; then
        sudo tee "$service_file" > /dev/null << EOF
[Unit]
Description=AI Audio Vision Lab Demo
After=network.target sound.target
Wants=network.target sound.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$project_dir
Environment=PATH=$HOME/$VENV_NAME/bin
ExecStart=$HOME/$VENV_NAME/bin/python demo/simple_demo.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        print_success "Systemd service created (not enabled by default)"
        print_step "To enable auto-start: sudo systemctl enable ai-audio-vision-lab"
        print_step "To start service: sudo systemctl start ai-audio-vision-lab"
    else
        print_success "Systemd service already exists"
    fi
}

# ============================================================================
# TESTING AND VALIDATION
# ============================================================================

run_system_tests() {
    print_step "Running system tests..."
    
    source "$HOME/$VENV_NAME/bin/activate"
    
    # Test Python imports
    print_step "Testing Python imports..."
    python -c "
import sys
import torch
import cv2
import librosa
import numpy as np
import yaml
print('✅ All critical imports successful')
print(f'Python: {sys.version}')
print(f'PyTorch: {torch.__version__}')
print(f'OpenCV: {cv2.__version__}')
print(f'NumPy: {np.__version__}')
" || {
        print_error "Python import tests failed"
        exit 1
    }
    
    # Test audio system
    print_step "Testing audio system..."
    python -c "
import pygame
pygame.mixer.init()
print('✅ Audio system test passed')
" || print_warning "Audio system test failed"
    
    # Test camera (if available)
    if [ -e /dev/video0 ]; then
        print_step "Testing camera..."
        python -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print('✅ Camera test passed')
    cap.release()
else:
    print('⚠️ Camera test failed')
" || print_warning "Camera test failed"
    else
        print_warning "No camera detected at /dev/video0"
    fi
    
    print_success "System tests completed"
}

create_demo_script() {
    print_step "Creating convenient demo launcher..."
    
    local launcher_script="$HOME/run_aavl_demo.sh"
    
    cat > "$launcher_script" << EOF
#!/bin/bash
# AI Audio Vision Lab Demo Launcher

echo "🎛️ Starting AI Audio Vision Lab Demo..."
echo ""

cd "$HOME/$REPO_NAME"
source "$HOME/$VENV_NAME/bin/activate"

# Check system status
echo "System Status:"
echo "- CPU Temperature: \$(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
echo "- Memory Usage: \$(free -h | grep '^Mem:' | awk '{print \$3 "/" \$2}')"
echo "- CPU Load: \$(uptime | awk -F'load average:' '{print \$2}')"
echo ""

# Run the demo
python demo/simple_demo.py

echo ""
echo "Demo finished. Thank you for trying AI Audio Vision Lab!"
EOF
    
    chmod +x "$launcher_script"
    print_success "Demo launcher created: $launcher_script"
}

# ============================================================================
# PERFORMANCE OPTIMIZATION
# ============================================================================

optimize_for_performance() {
    print_step "Applying performance optimizations..."
    
    # Set CPU governor to performance mode
    echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor >/dev/null 2>&1
    
    # Disable unnecessary services to free up resources
    local services_to_disable=(
        "bluetooth"
        "hciuart"
        "cups"
        "cups-browsed"
    )
    
    for service in "${services_to_disable[@]}"; do
        if systemctl is-enabled "$service" >/dev/null 2>&1; then
            print_step "Disabling $service to free up resources..."
            sudo systemctl disable "$service" >/dev/null 2>&1
            sudo systemctl stop "$service" >/dev/null 2>&1
        fi
    done
    
    # Add performance settings to ~/.bashrc
    if ! grep -q "AI Audio Vision Lab" ~/.bashrc; then
        cat >> ~/.bashrc << 'EOF'

# AI Audio Vision Lab Performance Settings
export OMP_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export MKL_NUM_THREADS=4

# Convenient aliases
alias aavl-demo='cd ~/ai-audio-vision-lab && source ~/aavl_env/bin/activate && python demo/simple_demo.py'
alias aavl-status='vcgencmd measure_temp && free -h && uptime'
alias aavl-env='cd ~/ai-audio-vision-lab && source ~/aavl_env/bin/activate'
EOF
        print_success "Performance settings added to ~/.bashrc"
    fi
    
    print_success "Performance optimizations applied"
}

# ============================================================================
# CLEANUP AND FINALIZATION
# ============================================================================

cleanup_installation() {
    print_step "Cleaning up installation files..."
    
    # Clear pip cache
    source "$HOME/$VENV_NAME/bin/activate"
    pip cache purge >/dev/null 2>&1
    
    # Clear apt cache
    sudo apt-get autoremove -y -qq
    sudo apt-get autoclean -qq
    
    # Reset swap size to default if we increased it
    if [ -f /etc/dphys-swapfile ]; then
        local current_swap_setting=$(grep "^CONF_SWAPSIZE=" /etc/dphys-swapfile | cut -d= -f2)
        if [ "$current_swap_setting" = "2048" ]; then
            print_step "Resetting swap file to default size..."
            sudo dphys-swapfile swapoff
            sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=100/' /etc/dphys-swapfile
            sudo dphys-swapfile setup
            sudo dphys-swapfile swapon
        fi
    fi
    
    print_success "Cleanup completed"
}

print_final_instructions() {
    print_header "Installation Complete! 🎉"
    
    echo "Your AI Audio Vision Lab demo is ready to use!"
    echo ""
    echo -e "${GREEN}Quick Start:${NC}"
    echo "  1. Run the demo: ~/run_aavl_demo.sh"
    echo "  2. Or manually: cd ~/ai-audio-vision-lab && source ~/aavl_env/bin/activate && python demo/simple_demo.py"
    echo ""
    echo -e "${GREEN}Useful Commands:${NC}"
    echo "  • aavl-demo     - Start the demo"
    echo "  • aavl-status   - Check system status"
    echo "  • aavl-env      - Activate environment"
    echo ""
    echo -e "${GREEN}System Information:${NC}"
    echo "  • Project: ~/ai-audio-vision-lab"
    echo "  • Environment: ~/aavl_env"
    echo "  • Launcher: ~/run_aavl_demo.sh"
    echo "  • Service: ai-audio-vision-lab (disabled by default)"
    echo ""
    
    if grep -q "reboot required" /tmp/setup.log 2>/dev/null; then
        print_warning "A reboot is recommended to activate all changes"
        echo "Run: sudo reboot"
        echo ""
    fi
    
    echo -e "${BLUE}For support and full version access:${NC}"
    echo "  📧 Email: oggettosonoro@gmail.com"
    echo "  🐙 GitHub: https://github.com/ninuxi/ai-audio-vision-lab"
    echo ""
    echo -e "${GREEN}Happy music making! 🎵${NC}"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    print_header "$PROJECT_NAME - Raspberry Pi Setup"
    
    echo "Setting up AI Audio Vision Lab on your Raspberry Pi..."
    echo "This will install dependencies and configure the demo environment."
    echo ""
    echo "System Information:"
    echo "  • Model: $RPI_MODEL"
    echo "  • OS: $OS_VERSION"
    echo "  • User: $USER"
    echo ""
    
    # Confirmation
    echo -n "Continue with installation? (y/N): "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi
    
    # Create log file
    exec 1> >(tee -a /tmp/setup.log)
    exec 2> >(tee -a /tmp/setup.log >&2)
    
    # Run setup steps
    print_header "System Checks"
    check_root
    check_raspberry_pi
    check_memory
    
    print_header "System Setup"
    update_system
    install_system_dependencies
    configure_audio
    enable_camera
    optimize_system
    
    print_header "Python Environment"
    setup_python_environment
    
    print_header "Project Setup"
    clone_repository
    install_python_dependencies
    create_demo_assets
    
    print_header "Configuration"
    setup_systemd_service
    create_demo_script
    optimize_for_performance
    
    print_header "Testing"
    run_system_tests
    
    print_header "Finalization"
    cleanup_installation
    print_final_instructions
}

# Handle script interruption
trap 'echo -e "\n${RED}Setup interrupted by user${NC}"; exit 1' INT

# Run main function
main "$@"