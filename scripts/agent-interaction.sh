#!/bin/bash

# Agent Interaction Script
# This script helps you interact with the multi-agent system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}================================${NC}"
    echo -e "${CYAN}  Multi-Agent Interaction Tool  ${NC}"
    echo -e "${CYAN}================================${NC}"
}

print_menu() {
    echo ""
    echo -e "${BLUE}Available Commands:${NC}"
    echo "1. Start new feature"
    echo "2. Check agent status"
    echo "3. Monitor agent activity"
    echo "4. Send message to agent"
    echo "5. Update agent status"
    echo "6. Check for conflicts"
    echo "7. Run quality checks"
    echo "8. View agent dashboard"
    echo "9. Exit"
    echo ""
}

start_new_feature() {
    echo -e "${GREEN}Starting new feature...${NC}"
    read -p "Enter feature name: " feature_name
    read -p "Enter feature description: " feature_description
    
    # Create feature branch
    git checkout -b "feature/$feature_name"
    
    # Update agent status
    cat > .cursor/agent-coordination/status.md << EOF
## Current Sprint: $feature_name

### Feature Description
$feature_description

### Active Agents
- [ ] Frontend Specialist: [Current task]
- [ ] Backend Specialist: [Current task]
- [ ] DevOps Specialist: [Current task]
- [ ] Testing Specialist: [Current task]
- [ ] Security Specialist: [Current task]
- [ ] Database Specialist: [Current task]
- [ ] UI/UX Specialist: [Current task]
- [ ] Performance Specialist: [Current task]

### Blocked Tasks
- None

### Completed Tasks
- None

### Upcoming Tasks
- [ ] Frontend Specialist: [Upcoming task]
- [ ] Backend Specialist: [Upcoming task]
- [ ] Testing Specialist: [Upcoming task]
EOF

    echo -e "${GREEN}Feature '$feature_name' started!${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Update agent status with specific tasks"
    echo "2. Send messages to relevant agents"
    echo "3. Monitor progress with option 3"
}

check_agent_status() {
    echo -e "${GREEN}Current Agent Status:${NC}"
    echo ""
    cat .cursor/agent-coordination/status.md
}

monitor_agent_activity() {
    echo -e "${GREEN}Monitoring agent activity...${NC}"
    ./.cursor/agent-coordination/monitor-agents.sh
}

send_message_to_agent() {
    echo -e "${GREEN}Send message to agent${NC}"
    echo ""
    echo "Available agents:"
    echo "1. Frontend Specialist"
    echo "2. Backend Specialist"
    echo "3. DevOps Specialist"
    echo "4. Testing Specialist"
    echo "5. Security Specialist"
    echo "6. Database Specialist"
    echo "7. UI/UX Specialist"
    echo "8. Performance Specialist"
    echo "9. All agents"
    echo ""
    
    read -p "Select agent (1-9): " agent_choice
    read -p "Enter message: " message
    
    case $agent_choice in
        1) agent="frontend-specialist" ;;
        2) agent="backend-specialist" ;;
        3) agent="devops-specialist" ;;
        4) agent="testing-specialist" ;;
        5) agent="security-specialist" ;;
        6) agent="database-specialist" ;;
        7) agent="ui-ux-specialist" ;;
        8) agent="performance-specialist" ;;
        9) agent="all-agents" ;;
        *) echo "Invalid choice"; return ;;
    esac
    
    # Create message file
    timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    cat > .cursor/agent-coordination/message_${agent}_$(date +%s).md << EOF
# Message to $agent
**Timestamp:** $timestamp
**From:** User
**Priority:** Normal

## Message
$message

## Response
[Waiting for response...]
EOF
    
    echo -e "${GREEN}Message sent to $agent!${NC}"
    echo -e "${YELLOW}Message saved to: .cursor/agent-coordination/message_${agent}_$(date +%s).md${NC}"
}

update_agent_status() {
    echo -e "${GREEN}Update agent status${NC}"
    echo ""
    echo "Current status:"
    cat .cursor/agent-coordination/status.md
    echo ""
    echo "Enter new status (press Ctrl+D when done):"
    cat > .cursor/agent-coordination/status.md
    echo -e "${GREEN}Status updated!${NC}"
}

check_conflicts() {
    echo -e "${GREEN}Checking for conflicts...${NC}"
    echo ""
    
    # Check git status
    echo "Git status:"
    git status --porcelain
    
    # Check for merge conflicts
    if git diff --name-only --diff-filter=U | grep -q .; then
        echo -e "${RED}Merge conflicts detected:${NC}"
        git diff --name-only --diff-filter=U
    else
        echo -e "${GREEN}No merge conflicts detected${NC}"
    fi
    
    # Check for uncommitted changes
    if git diff --name-only | grep -q .; then
        echo -e "${YELLOW}Uncommitted changes:${NC}"
        git diff --name-only
    else
        echo -e "${GREEN}No uncommitted changes${NC}"
    fi
}

run_quality_checks() {
    echo -e "${GREEN}Running quality checks...${NC}"
    ./scripts/lint-check.sh
}

view_agent_dashboard() {
    echo -e "${GREEN}Agent Dashboard${NC}"
    cat .cursor/agent-coordination/dashboard.md
}

# Main script
print_header

while true; do
    print_menu
    read -p "Select option (1-9): " choice
    
    case $choice in
        1) start_new_feature ;;
        2) check_agent_status ;;
        3) monitor_agent_activity ;;
        4) send_message_to_agent ;;
        5) update_agent_status ;;
        6) check_conflicts ;;
        7) run_quality_checks ;;
        8) view_agent_dashboard ;;
        9) echo -e "${GREEN}Goodbye!${NC}"; exit 0 ;;
        *) echo -e "${RED}Invalid option. Please try again.${NC}" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
done
