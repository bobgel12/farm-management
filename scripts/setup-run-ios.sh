#!/bin/bash

set -euo pipefail

# Setup and run the migrated iOS app project.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
IOS_DIR="${REPO_ROOT}/mobile/ios/RotemFarm-iOS"
PROJECT_NAME="RotemFarm.xcodeproj"

API_BASE_URL="${ROTEM_API_BASE_URL:-http://localhost:8002}"
USERNAME="${ROTEM_IOS_USERNAME:-}"
PASSWORD="${ROTEM_IOS_PASSWORD:-}"
AUTO_INSTALL_XCODEGEN="false"

print_help() {
    echo "Usage: $(basename "$0") [options]"
    echo ""
    echo "Options:"
    echo "  --api-url <url>              Backend API base URL (default: ${API_BASE_URL})"
    echo "  --username <username>        Optional default username for login screen"
    echo "  --password <password>        Optional default password for login screen"
    echo "  --install-xcodegen           Auto-install xcodegen via Homebrew if missing"
    echo "  -h, --help                   Show this help"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0")"
    echo "  $(basename "$0") --api-url http://localhost:8002   # Docker maps API to host :8002"
    echo "  $(basename "$0") --username admin --password admin123"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --api-url)
            API_BASE_URL="$2"
            shift 2
            ;;
        --username)
            USERNAME="$2"
            shift 2
            ;;
        --password)
            PASSWORD="$2"
            shift 2
            ;;
        --install-xcodegen)
            AUTO_INSTALL_XCODEGEN="true"
            shift
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

if [[ ! -d "${IOS_DIR}" ]]; then
    echo "❌ iOS project directory not found: ${IOS_DIR}"
    exit 1
fi

if ! command -v xcodegen >/dev/null 2>&1; then
    if [[ "${AUTO_INSTALL_XCODEGEN}" == "true" ]]; then
        if ! command -v brew >/dev/null 2>&1; then
            echo "❌ Homebrew is required to auto-install xcodegen."
            echo "Install Homebrew first or install xcodegen manually."
            exit 1
        fi
        echo "📦 Installing xcodegen with Homebrew..."
        brew install xcodegen
    else
        echo "❌ xcodegen is not installed."
        echo "Install with: brew install xcodegen"
        echo "Or rerun with: $(basename "$0") --install-xcodegen"
        exit 1
    fi
fi

echo "📱 Preparing iOS project..."
cd "${IOS_DIR}"
xcodegen generate

echo "✅ Generated ${PROJECT_NAME}"
echo "🔧 Launch configuration:"
echo "   ROTEM_API_BASE_URL=${API_BASE_URL}"
if [[ -n "${USERNAME}" ]]; then
    echo "   ROTEM_IOS_USERNAME=${USERNAME}"
fi
if [[ -n "${PASSWORD}" ]]; then
    echo "   ROTEM_IOS_PASSWORD=[set]"
fi

echo "🚀 Opening Xcode project..."
ROTEM_API_BASE_URL="${API_BASE_URL}" \
ROTEM_IOS_USERNAME="${USERNAME}" \
ROTEM_IOS_PASSWORD="${PASSWORD}" \
open "${PROJECT_NAME}"

echo ""
echo "Next in Xcode:"
echo "1) Select an iPhone simulator"
echo "2) Press Cmd+R to run"
