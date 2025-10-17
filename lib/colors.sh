#!/usr/bin/env bash

# Color formatting helpers for Claude Code Gists
# Based on formattingHelpers.sh from web-app-deployments

# Color definitions using tput for better compatibility
red=$(tput setaf 1)
green=$(tput setaf 2)
yellow=$(tput setaf 3)
blue=$(tput setaf 4)
purple=$(tput setaf 5)
cyan=$(tput setaf 6)
gray=$(tput setaf 8)
bold=$(tput bold)
reset=$(tput sgr0)

# Color functions
color() {
    local color=$1
    local text=$2
    local is_bold=${3:-"false"}
    
    if [[ $is_bold == "true" ]]; then
        printf "${bold}${color}${text}${reset}\n"
    else
        printf "${color}${text}${reset}\n"
    fi
}

# Individual color functions
print_red() {
    color "${red}" "$1" "${2:-false}"
}

print_green() {
    color "${green}" "$1" "${2:-false}"
}

print_yellow() {
    color "${yellow}" "$1" "${2:-false}"
}

print_blue() {
    color "${blue}" "$1" "${2:-false}"
}

print_purple() {
    color "${purple}" "$1" "${2:-false}"
}

print_cyan() {
    color "${cyan}" "$1" "${2:-false}"
}

print_gray() {
    color "${gray}" "$1" "${2:-false}"
}

print_bold() {
    printf "${bold}$1${reset}\n"
}

# Utility functions
horizontal_line() {
    echo "========================================"
}

section_header() {
    local title="$1"
    echo ""
    print_blue "$title" "true"
    horizontal_line
    echo ""
}

success_message() {
    print_green "✓ $1"
}

warning_message() {
    print_yellow "⚠ $1"
}

error_message() {
    print_red "✗ $1"
}

info_message() {
    print_blue "$1"
}
