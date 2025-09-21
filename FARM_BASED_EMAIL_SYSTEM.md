# Farm-Based Email System

## Overview
The Chicken House Management System now supports **farm-based email sending** instead of house-based sending. This means that workers receive one email per farm containing all tasks for all houses within that farm, rather than separate emails for each house.

## 🎯 **How Farm-Based Email Works**

### **Email Structure**
- **One Email Per Farm**: Each farm sends one email to all its active workers
- **All Houses Included**: The email contains tasks from all active houses in the farm
- **Worker Recipients**: All active workers with `receive_daily_tasks=True` receive the email
- **Task Organization**: Tasks are grouped by house within the email

### **Email Content Per Farm**
```
📧 Daily Task Reminder - [Farm Name]
[Date]

TODAY'S SUMMARY
================
Active Houses: 3
Total Tasks: 15
Today's Tasks: 8 + 4 + 3

========================================
HOUSE 1
========================================
Day: 5
Status: Early Care
Chicken In Date: Jan 15, 2024

TODAY'S TASKS (3)
----------------------------------------
• Increase water pressure by 1 half turn
• Death chicken pickup
• Turn on feed manually (morning)

TOMORROW'S TASKS (2)
--------------------------------------------
• Turn on feed manually (afternoon)
• Check feeder motor

========================================
HOUSE 2
========================================
Day: 12
Status: Growth
Chicken In Date: Jan 8, 2024

TODAY'S TASKS (4)
----------------------------------------
• Check feeder motor on last pan
• Clean up turbo line
• Raise feeder line
• Increase water pressure

[Additional houses...]
```

---

## 🔧 **Backend Implementation**

### **API Endpoints**

#### **1. Send Daily Tasks (All Farms)**
```http
POST /api/tasks/send-daily-tasks/
Content-Type: application/json

{}
```
**Response:**
```json
{
  "message": "Successfully sent 3 daily task reminder emails"
}
```

#### **2. Send Daily Tasks (Specific Farm)**
```http
POST /api/tasks/send-daily-tasks/
Content-Type: application/json

{
  "farm_id": 1
}
```
**Response:**
```json
{
  "message": "Successfully sent daily task reminder email for Main Farm"
}
```

### **Email Service Methods**

#### **`send_daily_task_reminders()`**
- Sends emails to all active farms
- Returns total count of emails sent
- Used for global email sending

#### **`send_farm_task_reminders(farm)`**
- Sends email to specific farm
- Returns 1 if successful, 0 if failed
- Used for farm-specific email sending

#### **`_get_farm_task_data(farm)`**
- Collects all tasks for all houses in a farm
- Groups tasks by house
- Returns structured data for email template

---

## 🎨 **Frontend Implementation**

### **EmailManager Component**

#### **Global Email Management (Dashboard)**
```tsx
<EmailManager />
// Sends emails to all farms
// Button text: "Send All Farm Tasks"
// Description: "Send daily task reminders and test emails to workers for all farms."
```

#### **Farm-Specific Email Management (Farm Detail)**
```tsx
<EmailManager farmId={1} farmName="Main Farm" />
// Sends emails only for this farm
// Button text: "Send Farm Tasks"
// Description: "Send daily task reminders and test emails to workers for Main Farm."
```

#### **House Context (House Detail)**
```tsx
<EmailManager farmId={house.farm_id} farmName={house.farm_name} />
// Sends emails for the farm that owns this house
// Inherits farm context from house
```

### **EmailStatus Component**

#### **Global Status (Navigation)**
```tsx
<EmailStatus />
// Shows status for all farms
// Menu item: "Send All Farm Tasks"
```

#### **Farm-Specific Status**
```tsx
<EmailStatus farmId={1} />
// Shows status for specific farm
// Menu item: "Send Farm Tasks"
```

---

## 📊 **Email Data Structure**

### **Farm Task Data**
```typescript
interface FarmTaskData {
  farm_name: string;
  date: string;
  houses: HouseTaskData[];
}

interface HouseTaskData {
  id: number;
  house_number: number;
  current_day: number;
  status: string;
  chicken_in_date: string;
  today_tasks: TaskData[];
  tomorrow_tasks: TaskData[];
}

interface TaskData {
  id: number;
  name: string;
  description: string;
  type: string;
}
```

### **Email Recipients**
- **Farm Workers**: All active workers assigned to the farm
- **Filter**: Only workers with `receive_daily_tasks=True`
- **Status**: Only workers with `is_active=True`

---

## 🎯 **Benefits of Farm-Based Email System**

### **1. Consolidated Communication**
- **Single Email**: Workers receive one email per farm instead of multiple
- **Complete Overview**: All tasks for all houses in one place
- **Reduced Email Clutter**: Less inbox pollution

### **2. Better Organization**
- **Farm Context**: Workers understand which farm the tasks are for
- **House Grouping**: Tasks are clearly organized by house
- **Status Overview**: See all house statuses at once

### **3. Improved Efficiency**
- **Less Email Processing**: Fewer emails to read and process
- **Better Planning**: Workers can plan their day across all houses
- **Reduced Confusion**: Clear farm and house context

### **4. Scalability**
- **Multiple Houses**: Easily handle farms with many houses
- **Worker Assignment**: Workers can be assigned to specific farms
- **Flexible Management**: Send emails per farm or globally

---

## 🔄 **Email Sending Workflow**

### **1. Global Email Sending (Dashboard)**
```
User clicks "Send All Farm Tasks"
↓
System iterates through all active farms
↓
For each farm:
  - Get active workers
  - Collect tasks from all houses
  - Send one email per farm
↓
Return total count of emails sent
```

### **2. Farm-Specific Email Sending**
```
User clicks "Send Farm Tasks" on farm detail page
↓
System gets specific farm
↓
Get active workers for this farm
↓
Collect tasks from all houses in this farm
↓
Send one email to all workers
↓
Return success/failure status
```

### **3. Automatic Daily Sending (Cron)**
```
Cron job runs at 9 PM UTC daily
↓
Calls send_daily_task_reminders()
↓
Sends emails to all active farms
↓
Logs results and counts
```

---

## 📱 **User Interface Features**

### **Dashboard Email Management**
- **Global Control**: Send emails to all farms
- **Status Overview**: See email status for all farms
- **Quick Actions**: Send all farm tasks with one click

### **Farm Detail Email Management**
- **Farm-Specific Control**: Send emails only for this farm
- **Farm Context**: Clear indication of which farm
- **Targeted Sending**: Only affects this farm's workers

### **House Detail Email Management**
- **Inherited Context**: Uses farm context from house
- **Farm Scope**: Sends emails for the farm that owns this house
- **Contextual Actions**: Actions are scoped to the relevant farm

---

## 🎨 **Email Template Features**

### **Farm Header**
- **Farm Name**: Clear identification of the farm
- **Date**: Current date
- **Summary**: Total houses and tasks

### **House Sections**
- **House Number**: Clear house identification
- **Current Day**: Chicken age in days
- **Status**: House status (setup, early_care, etc.)
- **Chicken In Date**: When chickens arrived

### **Task Lists**
- **Today's Tasks**: All incomplete tasks for current day
- **Tomorrow's Tasks**: All tasks for next day
- **Task Details**: Name, description, and type
- **Organization**: Grouped by house within farm

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Email settings (same as before)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### **Database Requirements**
- **Farms**: Must have active farms
- **Workers**: Must have active workers with `receive_daily_tasks=True`
- **Houses**: Must have active houses with tasks
- **Tasks**: Must have generated tasks for houses

---

## 📊 **Monitoring and Analytics**

### **Email Tracking**
- **EmailTask Model**: Tracks sent emails per farm
- **Sent Date**: When email was sent
- **Farm Reference**: Which farm the email was for
- **Task Count**: How many tasks were included

### **Success Metrics**
- **Delivery Rate**: Percentage of successful email sends
- **Farm Coverage**: How many farms received emails
- **Worker Reach**: How many workers received emails
- **Task Coverage**: How many tasks were included

---

## 🚀 **Usage Examples**

### **1. Send All Farm Emails (Dashboard)**
```tsx
// User clicks "Send All Farm Tasks" on dashboard
// System sends emails to all 3 farms
// Result: "Successfully sent 3 daily task reminder emails"
```

### **2. Send Specific Farm Email (Farm Detail)**
```tsx
// User clicks "Send Farm Tasks" on Main Farm page
// System sends email only to Main Farm workers
// Result: "Successfully sent daily task reminder email for Main Farm"
```

### **3. Send Farm Email from House (House Detail)**
```tsx
// User clicks "Send Farm Tasks" on House 1 page
// System sends email for the farm that owns House 1
// Result: "Successfully sent daily task reminder email for Main Farm"
```

---

## 🎉 **Summary**

The farm-based email system provides a more organized and efficient way to send daily task reminders. Workers receive consolidated emails containing all tasks for all houses within their assigned farm, making it easier to plan and execute their daily work. The system supports both global email sending (all farms) and targeted email sending (specific farms), providing flexibility for different management needs.

**Key Benefits:**
- ✅ **One email per farm** instead of one per house
- ✅ **All house tasks** included in each farm email
- ✅ **Better organization** with clear farm and house context
- ✅ **Reduced email clutter** for workers
- ✅ **Flexible sending** (global or farm-specific)
- ✅ **Scalable design** for farms with many houses

The system maintains all existing functionality while providing a more logical and user-friendly email structure! 🐔📧
