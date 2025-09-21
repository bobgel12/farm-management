# 🌱 Enhanced Seeding Script Documentation

## Overview
The enhanced seeding script creates realistic and varied sample data for the Chicken House Management System, including diverse house dates, task statuses, and worker configurations.

## 🚀 **Usage**

### **Basic Seeding**
```bash
# Clear existing data and seed with defaults
python manage.py seed_data --clear

# Seed with custom parameters
python manage.py seed_data --farms 5 --houses-per-farm 6 --workers-per-farm 4
```

### **Maximum Variety Mode**
```bash
# Create maximum variety in house dates and task statuses
python manage.py seed_data --clear --variety --farms 4 --houses-per-farm 7
```

### **Command Line Options**
- `--clear`: Clear existing data before seeding
- `--farms N`: Number of farms to create (default: 3)
- `--houses-per-farm N`: Number of houses per farm (default: 4)
- `--workers-per-farm N`: Number of workers per farm (default: 3)
- `--variety`: Create maximum variety in house dates and task statuses

---

## 🏠 **House Scenarios**

The script creates houses with 7 different scenarios:

### **1. Setup Phase (0-2 days)**
- **Status**: 🏗️ Setup
- **Description**: Chickens just arrived, initial setup tasks
- **Task Completion**: 10% (very few tasks completed)
- **Example**: House 1 - Day 1

### **2. Early Care Phase (3-7 days)**
- **Status**: 🐣 Early Care
- **Description**: Critical early care period
- **Task Completion**: 30% (some tasks completed)
- **Example**: House 2 - Day 5

### **3. Growth Phase (8-20 days)**
- **Status**: 🌱 Growth
- **Description**: Active growth and development
- **Task Completion**: 60% (most tasks completed)
- **Example**: House 3 - Day 15

### **4. Mature Phase (21-35 days)**
- **Status**: 🐔 Mature
- **Description**: Mature chickens, routine maintenance
- **Task Completion**: 80% (almost all tasks completed)
- **Example**: House 4 - Day 28

### **5. Near Completion (36-40 days)**
- **Status**: 📦 Near Completion
- **Description**: Preparing for chicken out
- **Task Completion**: 90% (nearly all tasks completed)
- **Example**: House 5 - Day 38

### **6. Empty House (45-60 days ago)**
- **Status**: 🏠 Empty
- **Description**: Chickens already out, house empty
- **Task Completion**: 100% (all tasks completed)
- **Example**: House 6 - Completed 10 days ago

### **7. Future House (1-7 days from now)**
- **Status**: ⏳ Preparation
- **Description**: Chickens arriving soon, preparation tasks
- **Task Completion**: 0% (no tasks completed yet)
- **Example**: House 7 - Starting in 3 days

---

## 👥 **Worker Variety**

### **Roles and Distribution**
- **👨‍💼 Farm Manager** (10%): Primary management role
- **👨‍🔧 Supervisor** (20%): Supervisory responsibilities
- **👷 Worker** (50%): General farm workers
- **🔧 Maintenance** (10%): Equipment maintenance
- **👩‍⚕️ Health Inspector** (10%): Health and safety

### **Worker Status**
- **✅ Active** (90%): Currently working
- **❌ Inactive** (10%): Not currently working
- **📧 Receives Emails** (80%): Gets daily task reminders
- **📵 No Emails** (20%): Doesn't receive daily reminders

### **Sample Workers**
- John Smith, Jane Doe, Mike Johnson
- Sarah Wilson, Tom Brown, Emily Davis
- David Lee, Lisa Chen, Mark Wilson
- Anna Rodriguez

---

## 📋 **Task Status Variety**

### **Completion Rates by House Status**
```python
completion_scenarios = {
    'setup': 0.1,           # 10% - Very few tasks completed
    'early_care': 0.3,      # 30% - Some tasks completed
    'growth': 0.6,          # 60% - Most tasks completed
    'mature': 0.8,          # 80% - Almost all tasks completed
    'near_completion': 0.9, # 90% - Nearly all tasks completed
    'empty': 1.0,           # 100% - All tasks completed
    'preparation': 0.0      # 0% - No tasks completed yet
}
```

### **Task Completion Details**
- **Completed By**: Random worker names or "System"
- **Completion Notes**: Realistic notes based on task type
- **Completion Date**: Randomly within the last few days
- **Task Types**: Feeding, Health, Maintenance, Cleaning

### **Sample Completion Notes**
- **Feeding**: "Completed morning feeding routine", "All feeders checked and refilled"
- **Health**: "Health inspection completed", "No issues found during check"
- **Maintenance**: "Equipment checked and functioning", "Water system operating normally"
- **Cleaning**: "House cleaned and sanitized", "Waste removed and disposed"

---

## 🎯 **Variety Mode vs Normal Mode**

### **Normal Mode**
- Randomly selects house scenarios
- May have similar houses across farms
- Good for general testing

### **Variety Mode (`--variety`)**
- Cycles through all 7 house scenarios
- Ensures maximum variety across farms
- Perfect for comprehensive testing
- Guarantees different house statuses

---

## 📊 **Sample Output**

### **Farm Creation**
```
Created farm: Sunny Acres Farm
Created farm: Green Valley Poultry #2
Created farm: Mountain View Chickens #3
```

### **Worker Creation**
```
Created worker: John Smith for Sunny Acres Farm 👨‍💼 Farm Manager ✅ 📧
Created worker: Jane Doe for Sunny Acres Farm 👨‍🔧 Supervisor ✅ 📧
Created worker: Mike Johnson for Sunny Acres Farm 👷 Worker ❌ 📵
```

### **House Creation**
```
Created house: 1 for Sunny Acres Farm 🏗️ (Setup) - Day 1
Created house: 2 for Sunny Acres Farm 🐣 (Early Care) - Day 5
Created house: 3 for Sunny Acres Farm 🌱 (Growth) - Day 15
Created house: 4 for Sunny Acres Farm 🐔 (Mature) - Day 28
```

### **Task Generation**
```
Generated tasks for house 1
  → Marked 2/20 tasks as completed (10.0% completion rate) for house 1
Generated tasks for house 2
  → Marked 6/20 tasks as completed (30.0% completion rate) for house 2
```

---

## 🔧 **Technical Details**

### **Date Calculations**
- **Past Dates**: `timezone.now().date() - timedelta(days=scenario['days_ago'])`
- **Future Dates**: `timezone.now().date() + timedelta(days=abs(scenario['days_ago']))`
- **Out Dates**: `start_date + timedelta(days=scenario['out_day'])`

### **Task Completion Logic**
```python
# Mark tasks as completed based on completion rate
tasks_to_complete = int(len(all_tasks) * completion_rate)
completed_tasks = random.sample(list(all_tasks), min(tasks_to_complete, len(all_tasks)))
```

### **Worker Role Distribution**
```python
roles = ["Farm Manager", "Supervisor", "Worker", "Maintenance", "Health Inspector"]
role_weights = [0.1, 0.2, 0.5, 0.1, 0.1]  # More workers, fewer managers
```

---

## 🎉 **Benefits**

### **1. Realistic Testing Data**
- Houses in different phases of chicken lifecycle
- Realistic task completion rates
- Varied worker roles and statuses

### **2. Comprehensive Testing**
- Test all house statuses and ages
- Test different task completion scenarios
- Test worker management features

### **3. Better Development Experience**
- Visual variety in the UI
- Realistic data for demos
- Easy to test edge cases

### **4. Flexible Configuration**
- Customizable number of farms, houses, workers
- Variety mode for maximum diversity
- Clear existing data option

---

## 🚀 **Quick Start Examples**

### **Basic Development Setup**
```bash
python manage.py seed_data --clear --farms 3 --houses-per-farm 4 --workers-per-farm 3
```

### **Comprehensive Testing Setup**
```bash
python manage.py seed_data --clear --variety --farms 4 --houses-per-farm 7 --workers-per-farm 5
```

### **Demo/Production-like Setup**
```bash
python manage.py seed_data --clear --farms 6 --houses-per-farm 8 --workers-per-farm 4
```

The enhanced seeding script provides realistic, varied data that makes the Chicken House Management System much more interesting and useful for testing and development! 🌱🐔✨
