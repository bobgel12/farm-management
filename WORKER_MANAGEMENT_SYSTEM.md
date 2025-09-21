# 👥 Worker Management System

## Overview
The Chicken House Management System now includes a comprehensive **worker management system** that allows farms to add, edit, and manage workers who will receive daily task reminder emails.

## 🎯 **Key Features**

### **1. Worker Management**
- **Add Workers**: Add new workers to farms with complete information
- **Edit Workers**: Update worker details including contact information and preferences
- **Delete Workers**: Remove workers from farms
- **View Workers**: Display all workers for a farm with their status and roles

### **2. Worker Information**
- **Name**: Worker's full name
- **Email**: Email address for receiving daily task reminders
- **Phone**: Optional phone number
- **Role**: Worker's role (Manager, Supervisor, Worker, etc.)
- **Active Status**: Whether the worker is currently active
- **Email Preferences**: Whether the worker receives daily task emails

### **3. Email Integration**
- **Daily Task Emails**: Workers with `receive_daily_tasks=True` receive farm-based emails
- **Farm Context**: Workers receive emails for their assigned farm only
- **Consolidated Emails**: One email per farm containing all house tasks

---

## 🔧 **Backend API**

### **Worker Endpoints**
```http
# Get all workers (with optional farm filter)
GET /api/workers/?farm_id=1

# Get workers for specific farm
GET /api/farms/1/workers/

# Create new worker
POST /api/workers/
Content-Type: application/json
{
  "farm": 1,
  "name": "John Smith",
  "email": "john@example.com",
  "phone": "+1-555-123-4567",
  "role": "Manager",
  "is_active": true,
  "receive_daily_tasks": true
}

# Update worker
PUT /api/workers/1/
Content-Type: application/json
{
  "name": "John Smith Updated",
  "email": "john.updated@example.com",
  "phone": "+1-555-987-6543",
  "role": "Supervisor",
  "is_active": true,
  "receive_daily_tasks": false
}

# Delete worker
DELETE /api/workers/1/
```

### **Worker Model**
```python
class Worker(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='workers')
    name = models.CharField(max_length=100)
    email = models.EmailField(validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    receive_daily_tasks = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 🎨 **Frontend Components**

### **1. WorkerContext**
- **State Management**: Manages worker data and API calls
- **CRUD Operations**: Create, read, update, delete workers
- **Error Handling**: Handles API errors and loading states
- **Farm Integration**: Fetches workers for specific farms

### **2. WorkerList Component**
- **Worker Display**: Shows all workers for a farm
- **Status Indicators**: Visual indicators for active/inactive status
- **Role Badges**: Color-coded role badges
- **Email Status**: Shows which workers receive daily emails
- **Actions**: Edit and delete worker buttons

### **3. WorkerForm Component**
- **Add/Edit Form**: Single form for adding and editing workers
- **Validation**: Client-side validation for required fields
- **Role Selection**: Dropdown for common roles
- **Toggle Switches**: For active status and email preferences
- **Error Handling**: Displays validation errors

---

## 📱 **User Interface**

### **Farm Detail Page**
The worker management section is located on the Farm Detail page:

```
┌─────────────────────────────────────────────────────────┐
│ 🏠 Farm Detail - Main Farm                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📧 Email Management                                    │
│  [Send Farm Tasks] [Send Test Email] [View History]    │
│                                                         │
│  👥 Workers - Main Farm                                │
│  [Add Worker]                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ John Smith                    [Active] [Manager] │   │
│  │ 📧 john@example.com                             │   │
│  │ 📞 +1-555-123-4567                             │   │
│  │ 💼 Manager • ✅ Receives Emails                 │   │
│  │                                    [Edit] [Del] │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  🏠 Houses                                             │
│  [Add House]                                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### **Worker Form Dialog**
```
┌─────────────────────────────────────────────────────────┐
│ Add New Worker - Main Farm                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Name: [John Smith                    ] *               │
│  Email: [john@example.com             ] *               │
│  Phone: [+1-555-123-4567              ]                 │
│  Role: [Manager                       ]                 │
│                                                         │
│  ☑ Active Worker                                       │
│  ☑ Receive Daily Task Emails                           │
│                                                         │
│                                    [Cancel] [Add]      │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 **Workflow**

### **1. Adding Workers**
1. Navigate to Farm Detail page
2. Scroll to "Workers" section
3. Click "Add Worker" button
4. Fill in worker information
5. Set active status and email preferences
6. Click "Add" to save

### **2. Managing Workers**
1. View all workers in the Workers section
2. Click "Edit" to modify worker details
3. Click "Delete" to remove worker
4. Toggle switches for active status and email preferences

### **3. Email Integration**
1. Workers with `receive_daily_tasks=True` receive emails
2. Emails are sent per farm (not per worker)
3. Each farm sends one email to all its active workers
4. Email contains tasks from all houses in the farm

---

## 📊 **Worker Status Indicators**

### **Active Status**
- **🟢 Active**: Worker is currently working
- **🔴 Inactive**: Worker is not currently working

### **Role Badges**
- **🔵 Manager**: Primary management role
- **🟣 Supervisor**: Supervisory role
- **⚪ Worker**: General worker role

### **Email Status**
- **✅ Receives Emails**: Worker gets daily task reminders
- **❌ No Emails**: Worker doesn't receive daily task reminders

---

## 🎯 **Benefits**

### **1. For Farm Managers**
- **Complete Worker Management**: Add, edit, and remove workers easily
- **Email Control**: Control who receives daily task emails
- **Role Organization**: Assign and track worker roles
- **Contact Management**: Keep worker contact information up to date

### **2. For Workers**
- **Clear Communication**: Receive organized daily task emails
- **Farm Context**: Know which farm the tasks are for
- **Role Clarity**: Understand their role and responsibilities
- **Easy Updates**: Managers can easily update their information

### **3. For System**
- **Email Efficiency**: Send emails to the right people
- **Data Organization**: Keep worker data organized and accessible
- **Scalability**: Easily manage workers across multiple farms
- **Integration**: Seamlessly integrates with existing email system

---

## 🔧 **Configuration**

### **No Additional Setup Required**
- **Database**: Uses existing database schema
- **API**: Uses existing Django REST framework
- **Authentication**: Uses existing authentication system
- **Email**: Uses existing email configuration

### **Worker Roles**
Common roles that can be assigned:
- **Manager**: Farm manager with full access
- **Supervisor**: Supervisory role with oversight responsibilities
- **Worker**: General farm worker
- **Custom**: Any custom role can be entered

---

## 📈 **Usage Examples**

### **1. Adding a New Worker**
```typescript
// WorkerForm component
const workerData = {
  farm: 1,
  name: "Jane Doe",
  email: "jane@example.com",
  phone: "+1-555-987-6543",
  role: "Supervisor",
  is_active: true,
  receive_daily_tasks: true
};

await createWorker(workerData);
```

### **2. Updating Worker Information**
```typescript
// WorkerForm component
const updatedData = {
  name: "Jane Doe Updated",
  email: "jane.updated@example.com",
  role: "Manager",
  receive_daily_tasks: false
};

await updateWorker(workerId, updatedData);
```

### **3. Fetching Farm Workers**
```typescript
// WorkerList component
const workers = await getFarmWorkers(farmId);
// Returns array of workers for the specified farm
```

---

## 🎉 **Summary**

The worker management system provides a complete solution for managing farm workers and their email preferences. It integrates seamlessly with the existing farm-based email system, ensuring that the right people receive the right information at the right time.

**Key Features:**
- ✅ **Complete CRUD operations** for worker management
- ✅ **Role-based organization** with visual indicators
- ✅ **Email preference control** for daily task reminders
- ✅ **Farm-specific worker management** for multi-farm operations
- ✅ **Intuitive UI** with clear status indicators
- ✅ **Seamless integration** with existing email system

The system is now ready for managing workers and sending them organized, farm-based daily task reminders! 👥📧✨

---

## 🔗 **Related Components**

- **WorkerContext**: State management for worker operations
- **WorkerList**: Display and manage workers for a farm
- **WorkerForm**: Add and edit worker information
- **FarmDetail**: Integration point for worker management
- **EmailManager**: Sends emails to farm workers
- **EmailStatus**: Shows email status for farm workers

---

## 📝 **Notes**

- Workers are farm-specific and cannot be shared between farms
- Email addresses must be unique within each farm
- Inactive workers don't receive daily task emails
- Worker roles are customizable and can be any text
- Phone numbers are optional but validated when provided
- All worker operations are logged and auditable
