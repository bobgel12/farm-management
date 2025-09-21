# Frontend Email Features

## Overview
The Chicken House Management System now includes comprehensive email management features in the frontend, allowing users to send daily task reminders and test emails on demand.

## 🎯 **New Frontend Components**

### **1. EmailManager Component**
**Location**: `frontend/src/components/EmailManager.tsx`

**Features**:
- **Send Daily Tasks**: Trigger daily task emails for all farms or specific farm
- **Send Test Email**: Send test emails to verify email configuration
- **View Email History**: See previously sent emails and their status
- **Real-time Feedback**: Success/error notifications with snackbar alerts

**Props**:
```typescript
interface EmailManagerProps {
  farmId?: number;        // Optional: Specific farm ID
  farmName?: string;      // Optional: Farm name for display
}
```

**Usage**:
```tsx
// Global email management (Dashboard)
<EmailManager />

// Farm-specific email management
<EmailManager farmId={1} farmName="Main Farm" />
```

### **2. EmailStatus Component**
**Location**: `frontend/src/components/EmailStatus.tsx`

**Features**:
- **Email Status Indicator**: Shows last email sent time and count
- **Quick Actions Menu**: Send daily tasks with one click
- **Status Colors**: Visual indicators for email status
- **Badge Counter**: Shows total emails sent

**Usage**:
```tsx
// Added to main navigation bar
<EmailStatus onSendEmail={() => console.log('Email sent!')} />
```

---

## 📍 **Component Locations**

### **Dashboard Page**
- **File**: `frontend/src/components/Dashboard.tsx`
- **Location**: Added before Quick Actions section
- **Purpose**: Global email management for all farms

### **Farm Detail Page**
- **File**: `frontend/src/components/FarmDetail.tsx`
- **Location**: Added before Houses section
- **Purpose**: Farm-specific email management

### **House Detail Page**
- **File**: `frontend/src/components/HouseDetail.tsx`
- **Location**: Added before Tasks section
- **Purpose**: House-specific email management (inherits farm context)

### **Main Navigation**
- **File**: `frontend/src/components/Layout.tsx`
- **Location**: Added to top navigation bar
- **Purpose**: Quick email status and actions

---

## 🎨 **UI Features**

### **EmailManager Component UI**

#### **Main Card**
- **Title**: "📧 Email Management" with optional farm name
- **Description**: Brief explanation of email functionality
- **Action Buttons**: Three main action buttons

#### **Action Buttons**
1. **Send Daily Tasks** (Primary)
   - Color: Primary (blue)
   - Icon: Send icon
   - Function: Sends daily task emails to all workers

2. **Send Test Email** (Secondary)
   - Color: Outlined
   - Icon: Email icon
   - Function: Opens dialog for test email

3. **View History** (Secondary)
   - Color: Outlined
   - Icon: History icon
   - Function: Shows email history dialog

#### **Test Email Dialog**
- **Email Input**: Text field for recipient email
- **Validation**: Email format validation
- **Actions**: Cancel and Send buttons
- **Loading State**: Shows spinner during sending

#### **Email History Dialog**
- **List View**: Shows all sent emails
- **Information**: Farm name, sent date, task count, status
- **Status Chips**: Color-coded status indicators
- **Close Button**: Easy dialog dismissal

#### **Success/Error Notifications**
- **Snackbar**: Bottom-right positioned notifications
- **Auto-hide**: 6-second timeout
- **Colors**: Green for success, red for error
- **Dismissible**: Manual close option

### **EmailStatus Component UI**

#### **Navigation Icon**
- **Email Icon**: Material-UI email icon
- **Badge**: Shows total email count
- **Tooltip**: "Email Status & Actions"

#### **Dropdown Menu**
- **Send Daily Tasks**: Primary action with loading state
- **Status Information**: Last sent time and email count
- **Status Colors**: Success (green), warning (yellow), error (red)

---

## 🔧 **API Integration**

### **Endpoints Used**

#### **1. Send Daily Tasks**
```typescript
POST /api/tasks/send-daily-tasks/
// Sends daily task emails to all active workers
```

#### **2. Send Test Email**
```typescript
POST /api/tasks/send-test-email/
Body: {
  farm_id: number,
  test_email: string
}
// Sends test email to specific address
```

#### **3. Get Email History**
```typescript
GET /api/tasks/email-history/?farm_id={id}
// Returns list of sent emails
```

### **Error Handling**
- **Network Errors**: Displayed in snackbar notifications
- **Validation Errors**: Shown in form fields
- **API Errors**: Parsed from response and displayed
- **Loading States**: Spinners and disabled buttons

---

## 📱 **Responsive Design**

### **Mobile Optimization**
- **Button Layout**: Stacked vertically on mobile
- **Dialog Size**: Full width on small screens
- **Typography**: Responsive font sizes
- **Spacing**: Adjusted margins and padding

### **Desktop Features**
- **Button Layout**: Horizontal arrangement
- **Dialog Size**: Centered with max width
- **Hover Effects**: Interactive button states
- **Tooltips**: Helpful hover information

---

## 🎯 **User Experience Features**

### **1. Real-time Feedback**
- **Loading States**: Visual feedback during operations
- **Success Messages**: Confirmation of successful actions
- **Error Messages**: Clear error descriptions
- **Status Updates**: Live status information

### **2. Intuitive Interface**
- **Clear Labels**: Descriptive button and field labels
- **Icon Usage**: Meaningful icons for actions
- **Color Coding**: Consistent color scheme
- **Progressive Disclosure**: Information revealed as needed

### **3. Accessibility**
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: Proper ARIA labels
- **Color Contrast**: WCAG compliant colors
- **Focus Management**: Proper focus handling

---

## 🚀 **Usage Examples**

### **1. Send Daily Tasks from Dashboard**
```tsx
// User clicks "Send Daily Tasks" button
// System sends emails to all active workers
// Success message: "Successfully sent 5 daily task reminder emails"
```

### **2. Send Test Email for Farm**
```tsx
// User clicks "Send Test Email" button
// Dialog opens with email input field
// User enters "worker@example.com"
// System sends test email
// Success message: "Test email sent successfully"
```

### **3. View Email History**
```tsx
// User clicks "View History" button
// Dialog opens showing list of sent emails
// Each entry shows: Farm name, sent date, task count, status
// User can close dialog when done
```

### **4. Quick Send from Navigation**
```tsx
// User clicks email icon in navigation
// Dropdown menu opens
// User clicks "Send Daily Tasks"
// System sends emails and updates status
// Badge count increases
```

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000/api

# Email Settings (handled by backend)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### **Component Props**
```typescript
// EmailManager props
interface EmailManagerProps {
  farmId?: number;        // Optional farm ID for specific farm emails
  farmName?: string;      // Optional farm name for display
}

// EmailStatus props
interface EmailStatusProps {
  onSendEmail?: () => void;  // Optional callback after email sent
}
```

---

## 📊 **Status Indicators**

### **Email Status Colors**
- **Green (Success)**: Email sent within last 24 hours
- **Yellow (Warning)**: Email sent 24-48 hours ago
- **Red (Error)**: Email sent more than 48 hours ago or never sent
- **Gray (Default)**: No email data available

### **Button States**
- **Normal**: Ready to send emails
- **Loading**: Currently sending emails (with spinner)
- **Disabled**: Cannot send emails (no configuration)

---

## 🎉 **Benefits**

### **1. On-Demand Email Sending**
- **Immediate Action**: Send emails when needed
- **No Waiting**: Don't wait for scheduled emails
- **Emergency Notifications**: Send urgent task reminders

### **2. Email Testing**
- **Configuration Verification**: Test email setup
- **Template Preview**: See how emails look
- **Troubleshooting**: Debug email issues

### **3. Email Monitoring**
- **Send History**: Track all sent emails
- **Status Monitoring**: See email delivery status
- **Usage Statistics**: Monitor email usage

### **4. User Convenience**
- **Quick Access**: Email actions in multiple locations
- **Visual Feedback**: Clear status indicators
- **Easy Testing**: Simple test email functionality

---

The frontend email features provide a complete email management solution that integrates seamlessly with the existing Chicken House Management System, giving users full control over daily task email delivery! 🐔📧
