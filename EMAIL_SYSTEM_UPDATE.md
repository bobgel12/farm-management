# Email System Update: Farm-Based Email Sending

## Overview
The email system has been updated to support **farm-based email sending** instead of house-based sending. This provides a more organized and efficient way to send daily task reminders.

## ✅ **Changes Made**

### **Backend Updates**

#### **1. New API Endpoint Support**
- **`POST /api/tasks/send-daily-tasks/`** now accepts optional `farm_id` parameter
- **All Farms**: `{}` - Sends emails to all active farms
- **Specific Farm**: `{"farm_id": 1}` - Sends email only to specified farm

#### **2. New Email Service Method**
- **`TaskEmailService.send_farm_task_reminders(farm)`** - Sends emails for specific farm
- **`TaskEmailService.send_daily_task_reminders()`** - Sends emails for all farms (existing)

#### **3. Updated Management Command**
- **`python manage.py send_daily_tasks`** - Sends to all farms (default)
- **`python manage.py send_daily_tasks --farm-id 1`** - Sends to specific farm
- **`python manage.py send_daily_tasks --test --farm-id 1 --test-email user@example.com`** - Test email

### **Frontend Updates**

#### **1. EmailManager Component**
- **Farm-Specific Sending**: Pass `farmId` prop to send emails for specific farm
- **Dynamic Button Text**: "Send Farm Tasks" vs "Send All Farm Tasks"
- **Context-Aware Descriptions**: Different descriptions based on farm context

#### **2. EmailStatus Component**
- **Farm-Specific Status**: Pass `farmId` prop for farm-specific status
- **Dynamic Menu Items**: "Send Farm Tasks" vs "Send All Farm Tasks"

#### **3. Component Integration**
- **Dashboard**: Global email management (all farms)
- **Farm Detail**: Farm-specific email management
- **House Detail**: Inherits farm context from house

---

## 🎯 **How It Works Now**

### **Email Structure Per Farm**
```
📧 Daily Task Reminder - [Farm Name]
[Date]

TODAY'S SUMMARY
================
Active Houses: 3
Total Tasks: 15

========================================
HOUSE 1
========================================
Day: 5
Status: Early Care

TODAY'S TASKS (3)
----------------------------------------
• Task 1
• Task 2
• Task 3

TOMORROW'S TASKS (2)
--------------------------------------------
• Task 4
• Task 5

========================================
HOUSE 2
========================================
[Additional houses...]
```

### **Email Recipients**
- **Per Farm**: All active workers assigned to that farm
- **Filter**: Only workers with `receive_daily_tasks=True` and `is_active=True`
- **One Email Per Farm**: Workers receive one email per farm, not per house

---

## 🚀 **Usage Examples**

### **1. Send All Farm Emails (Dashboard)**
```tsx
// User clicks "Send All Farm Tasks" on dashboard
// API call: POST /api/tasks/send-daily-tasks/ with {}
// Result: "Successfully sent 3 daily task reminder emails"
```

### **2. Send Specific Farm Email (Farm Detail)**
```tsx
// User clicks "Send Farm Tasks" on Main Farm page
// API call: POST /api/tasks/send-daily-tasks/ with {"farm_id": 1}
// Result: "Successfully sent daily task reminder email for Main Farm"
```

### **3. Send Farm Email from House (House Detail)**
```tsx
// User clicks "Send Farm Tasks" on House 1 page
// API call: POST /api/tasks/send-daily-tasks/ with {"farm_id": 1}
// Result: "Successfully sent daily task reminder email for Main Farm"
```

### **4. Command Line Usage**
```bash
# Send to all farms
python manage.py send_daily_tasks

# Send to specific farm
python manage.py send_daily_tasks --farm-id 1

# Test email for specific farm
python manage.py send_daily_tasks --test --farm-id 1 --test-email user@example.com
```

---

## 📊 **Benefits**

### **1. Better Organization**
- **Consolidated Emails**: One email per farm instead of multiple per house
- **Complete Overview**: All tasks for all houses in one email
- **Clear Context**: Workers know which farm the tasks are for

### **2. Improved Efficiency**
- **Less Email Clutter**: Workers receive fewer emails
- **Better Planning**: Workers can plan across all houses in their farm
- **Reduced Confusion**: Clear farm and house context

### **3. Scalability**
- **Multiple Houses**: Easily handle farms with many houses
- **Worker Assignment**: Workers can be assigned to specific farms
- **Flexible Management**: Send emails per farm or globally

---

## 🔧 **Configuration**

### **No Changes Required**
- **Environment Variables**: Same email configuration
- **Database**: Same models and structure
- **Workers**: Same worker management
- **Tasks**: Same task generation

### **New Features Available**
- **Farm-Specific Sending**: Send emails to specific farms
- **Global Sending**: Send emails to all farms
- **Command Line Options**: More flexible command line usage
- **API Flexibility**: Support for both global and farm-specific sending

---

## 📱 **User Interface**

### **Dashboard**
- **EmailManager**: Global email management
- **Button**: "Send All Farm Tasks"
- **Description**: "Send daily task reminders and test emails to workers for all farms."

### **Farm Detail**
- **EmailManager**: Farm-specific email management
- **Button**: "Send Farm Tasks"
- **Description**: "Send daily task reminders and test emails to workers for [Farm Name]."

### **House Detail**
- **EmailManager**: Inherits farm context from house
- **Button**: "Send Farm Tasks"
- **Description**: "Send daily task reminders and test emails to workers for [Farm Name]."

---

## 🎉 **Summary**

The email system now supports **farm-based email sending** while maintaining all existing functionality. Workers receive consolidated emails containing all tasks for all houses within their assigned farm, making it easier to plan and execute their daily work.

**Key Changes:**
- ✅ **Farm-based email sending** instead of house-based
- ✅ **One email per farm** containing all house tasks
- ✅ **API support** for both global and farm-specific sending
- ✅ **Frontend components** updated for farm context
- ✅ **Command line** support for farm-specific sending
- ✅ **Backward compatibility** maintained

The system is now more organized, efficient, and scalable for farms with multiple houses! 🐔📧
