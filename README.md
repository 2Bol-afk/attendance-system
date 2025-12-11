# Attendance System

A comprehensive Django-based web application for managing student attendance in educational institutions.

## Quick Start

```bash
# Navigate to project directory
cd "d:\midterm Project web Dev\Attendance_System"

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000/`

## Features

- ✅ Multi-role authentication (Admin, Teacher, Student, Parent)
- ✅ Attendance tracking with status (Present, Absent, Late)
- ✅ Subject and course management
- ✅ Teacher-to-subject assignment
- ✅ Comprehensive reporting system
- ✅ Role-based dashboards
- ✅ Account export functionality

## User Roles

- **Admin**: Full system access and management
- **Teacher**: Mark attendance, view student lists
- **Student**: View personal attendance records
- **Parent**: View children's attendance reports

## Management Commands

### Populate Attendance
```bash
python manage.py populate_attendance --start-date 2025-11-24 --end-date 2025-11-28
```

### Assign Teachers to Subjects
```bash
python manage.py create_and_assign_teachers --school-year 2024-2025
```

### Export Accounts
```bash
python manage.py export_accounts
```

## Project Structure

```
Attendance_System/
├── accounts/          # User management
├── academics/        # Academic records & attendance
├── dashboard/        # Role-based dashboards
├── reports/          # Reporting system
├── core/             # Shared resources
└── Attendance_System/ # Project configuration
```

## Technology Stack

- **Framework**: Django 5.2.7
- **Database**: SQLite3
- **Language**: Python
- **Frontend**: HTML, CSS, JavaScript

## Documentation

For detailed documentation, see [DOCUMENTATION.md](DOCUMENTATION.md)

## Key URLs

- `/` - Login page
- `/dashboard/admin/` - Admin dashboard
- `/dashboard/teacher/` - Teacher dashboard
- `/dashboard/student/` - Student dashboard
- `/dashboard/parent-dashboard` - Parent dashboard
- `/academic/mark-attendance/` - Mark attendance
- `/reports/` - Reports

## License

This project is part of a midterm web development project.

---

**Version**: 1.0  
**Last Updated**: November 2025

