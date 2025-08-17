# 👥 MinuteMate Admin Guide

Complete guide for administering MinuteMate, including user management, system monitoring, and security features.

## 🛡️ **Admin System Overview**

MinuteMate provides a comprehensive administration system with both web-based and command-line interfaces for managing users, monitoring system health, and maintaining security.

### **Key Features**
- **Web Admin Panel**: Modern, responsive interface for all admin tasks
- **CLI Tools**: Command-line utilities for server management
- **User Management**: Complete user lifecycle management
- **Security**: Enterprise-grade security features
- **Monitoring**: Real-time system health and performance tracking
- **Audit Logging**: Comprehensive activity tracking

---

## 🖥️ **Web Admin Panel**

### **Accessing the Admin Panel**
Navigate to: `http://your-domain.com/frontend/admin.html`

### **Features**

#### **User Management Tab**
- **View All Users**: Comprehensive user listing with search and filtering
- **Create Users**: Add new users with customizable roles and permissions
- **Edit Users**: Modify user information and settings
- **Password Reset**: Admin-initiated password resets
- **User Status**: Activate/deactivate user accounts
- **Delete Users**: Remove users with confirmation prompts

#### **System Tab**
- **System Health**: Real-time server status and performance metrics
- **Database Info**: Database size, user count, and statistics
- **Performance Metrics**: Response times and system load
- **Backup Status**: Last backup time and backup health

#### **Logs Tab**
- **Activity Logs**: Real-time system activity monitoring
- **Error Logs**: System errors and debugging information
- **User Activity**: Login attempts, actions, and security events
- **Log Filtering**: Filter by level (INFO, WARNING, ERROR, DEBUG)

### **User Interface Features**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Search & Filter**: Quick user lookup and filtering options
- **Bulk Actions**: Perform actions on multiple users
- **Real-time Updates**: Live data updates without page refresh
- **Professional Styling**: Clean, modern interface design

---

## ⚡ **Command Line Tools**

### **User Creation Script** (`create_user.py`)

#### **Create User**
```bash
python3 create_user.py create <username> <email> <password> [first_name] [last_name]
```

**Example:**
```bash
python3 create_user.py create johndoe john@example.com securepass123 "John" "Doe"
```

#### **List Users**
```bash
python3 create_user.py list
```

#### **Reset Password**
```bash
python3 create_user.py reset <username_or_email> <new_password>
```

**Example:**
```bash
python3 create_user.py reset johndoe newpassword456
```

### **Advanced Admin CLI** (`admin_cli.py`)

#### **Create User with Options**
```bash
python3 admin_cli.py create <username> <email> [options]
```

**Options:**
- `--password <password>`: Set password (prompts if not provided)
- `--first-name <name>`: Set first name
- `--last-name <name>`: Set last name
- `--admin`: Create as admin user

**Example:**
```bash
python3 admin_cli.py create admin admin@company.com --password admin123 --first-name "Admin" --last-name "User" --admin
```

#### **List Users**
```bash
python3 admin_cli.py list
```

#### **Reset Password**
```bash
python3 admin_cli.py reset-password <username_or_email>
```

---

## 🔐 **Security Features**

### **Password Security**
- **Secure Hashing**: Uses Werkzeug's pbkdf2:sha256 algorithm
- **Salt Generation**: Unique salt for each password
- **Minimum Requirements**: Configurable password complexity rules
- **Password History**: Prevents password reuse (configurable)

### **Session Management**
- **Secure Sessions**: HTTP-only, secure cookies
- **Session Timeout**: Configurable session expiration
- **Concurrent Sessions**: Control multiple login sessions
- **Session Invalidation**: Force logout on security events

### **Password Reset System**
- **Token-Based**: Secure, time-limited reset tokens
- **Email Integration**: Automated reset email sending
- **Token Expiration**: 1-hour default expiration (configurable)
- **Single Use**: Tokens are invalidated after use

### **Access Control**
- **Role-Based Access**: Admin and user roles
- **Permission System**: Granular permission control
- **API Authentication**: JWT tokens for API access
- **Rate Limiting**: Protection against brute force attacks

---

## 📊 **System Monitoring**

### **Health Checks**
- **Server Status**: Application health and uptime
- **Database Health**: Connection status and performance
- **Disk Space**: Available storage monitoring
- **Memory Usage**: RAM utilization tracking

### **Performance Metrics**
- **Response Times**: API endpoint performance
- **Request Volume**: Traffic monitoring and analysis
- **Error Rates**: System error tracking
- **User Activity**: Active sessions and usage patterns

### **Audit Logging**
- **User Actions**: Login, logout, and user activities
- **Admin Actions**: User management and system changes
- **Security Events**: Failed logins and suspicious activities
- **System Events**: Startup, shutdown, and configuration changes

---

## 🛠️ **Database Management**

### **Database Migration**
```bash
python3 migrate_db.py
```

### **Database Backup**
```bash
# SQLite backup
cp minutemate.db minutemate_backup_$(date +%Y%m%d_%H%M%S).db

# PostgreSQL backup (production)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### **Database Cleanup**
```bash
# Clean old sessions
python3 -c "from models import db, User; db.session.query(User).filter(User.last_login < datetime.now() - timedelta(days=90)).delete()"
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **User Cannot Login**
1. Check user status: `python3 create_user.py list`
2. Reset password: `python3 create_user.py reset username newpassword`
3. Check logs for authentication errors

#### **Admin Panel Not Loading**
1. Verify server is running: `curl http://localhost:5000/api/health`
2. Check browser console for JavaScript errors
3. Verify admin user has proper permissions

#### **Database Errors**
1. Run migration: `python3 migrate_db.py`
2. Check database permissions
3. Verify database connection string

### **Log Analysis**
```bash
# View recent logs
tail -f logs/minutemate.log

# Search for errors
grep "ERROR" logs/minutemate.log

# Filter by user
grep "user:johndoe" logs/minutemate.log
```

---

## 🔧 **Configuration**

### **Admin Settings**
```python
# config.py
ADMIN_SETTINGS = {
    'SESSION_TIMEOUT': 3600,  # 1 hour
    'PASSWORD_RESET_TIMEOUT': 3600,  # 1 hour
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 900,  # 15 minutes
    'REQUIRE_EMAIL_VERIFICATION': False,
    'ALLOW_SELF_REGISTRATION': True
}
```

### **Security Configuration**
```python
SECURITY_SETTINGS = {
    'PASSWORD_MIN_LENGTH': 8,
    'PASSWORD_REQUIRE_UPPERCASE': True,
    'PASSWORD_REQUIRE_LOWERCASE': True,
    'PASSWORD_REQUIRE_NUMBERS': True,
    'PASSWORD_REQUIRE_SYMBOLS': False,
    'PASSWORD_HISTORY_COUNT': 5
}
```

---

## 📈 **Best Practices**

### **User Management**
- **Regular Audits**: Review user accounts monthly
- **Access Reviews**: Verify user permissions quarterly
- **Inactive Users**: Deactivate unused accounts after 90 days
- **Strong Passwords**: Enforce password complexity requirements

### **Security**
- **Regular Backups**: Daily database backups
- **Log Monitoring**: Review security logs weekly
- **Update Management**: Keep system dependencies updated
- **Access Logging**: Monitor admin panel access

### **Performance**
- **Database Maintenance**: Regular cleanup and optimization
- **Log Rotation**: Implement log rotation to manage disk space
- **Monitoring**: Set up alerts for system health metrics
- **Capacity Planning**: Monitor growth and plan for scaling

---

## 🆘 **Support**

For additional support:
- **Documentation**: Check other docs in the `/docs` folder
- **Issues**: Report bugs on GitHub Issues
- **Community**: Join our Discord community
- **Email**: Contact support@minutemate.com

---

*This guide covers the essential admin functions. For advanced configuration and customization, refer to the Configuration Guide and API Documentation.*
