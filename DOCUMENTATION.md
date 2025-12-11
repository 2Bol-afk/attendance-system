# Attendance System Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Database Models](#database-models)
4. [Application Structure](#application-structure)
5. [URL Routing](#url-routing)
6. [Key Features](#key-features)
7. [Management Commands](#management-commands)
8. [Installation & Setup](#installation--setup)
9. [User Roles & Permissions](#user-roles--permissions)
10. [API Endpoints](#api-endpoints)

---

## Project Overview

The **Attendance System** is a comprehensive Django-based web application designed for managing student attendance in an educational institution. The system supports multiple user roles (Admin, Teacher, Student, Parent) and provides features for tracking attendance, managing academic records, and generating reports.

### Technology Stack
- **Framework**: Django 5.2.7
- **Database**: SQLite3
- **Language**: Python
- **Frontend**: HTML, CSS, JavaScript
- **Template Engine**: Django Templates

---

## System Architecture

### Project Structure
```
Attendance_System/
├── Attendance_System/          # Main project configuration
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py                 # WSGI configuration
│   └── asgi.py                 # ASGI configuration
├── accounts/                   # User management app
├── academics/                  # Academic management app
├── dashboard/                  # Dashboard views app
├── reports/                    # Reporting app
├── core/                       # Core utilities and templates
└── manage.py                   # Django management script
```

### Installed Apps
1. **accounts** - User account management (Admin, Teacher, Student, Parent)
2. **academics** - Academic records (Subjects, Courses, Attendance)
3. **dashboard** - Dashboard views for different user roles
4. **reports** - Attendance and academic reports
5. **core** - Shared templates and static files

---

## Database Models

### Accounts App Models

#### CustomUser
- Extends Django's AbstractUser
- **Fields**:
  - `role`: Choices - 'admin', 'teacher', 'student', 'parent'
  - `first_login`: Boolean flag for password change requirement
- **Custom Authentication**: Supports login via username or email

#### TeacherProfile
- One-to-one relationship with CustomUser (role='teacher')
- **Fields**: `first_name`, `middle_name`, `last_name`

#### StudentProfile
- One-to-one relationship with CustomUser (role='student')
- **Fields**:
  - `student_ID`: Primary key (CharField, max_length=10)
  - `first_name`, `middle_name`, `last_name`
  - `course`: ForeignKey to Course
  - `year`: Year level (1st, 2nd, 3rd, 4th)
  - `section`: Section (A, B, C, D)
  - `is_regular`: Student status (Regular/Irregular)
  - `parents`: ManyToMany with ParentProfile
  - `subjects`: ManyToMany with Subject

#### ParentProfile
- One-to-one relationship with CustomUser (role='parent')
- **Fields**: `first_name`, `middle_name`, `last_name`, `contact_number`
- **Relationships**: ManyToMany with StudentProfile (children)

### Academics App Models

#### Course
- **Fields**: `name`, `description`

#### Subject
- **Fields**:
  - `course`: ForeignKey to Course
  - `subject_code`: CharField (max_length=20)
  - `name`: CharField (max_length=255)
  - `semester_number`: Choices - '1st', '2nd'
  - `year_level`: Choices - '1st', '2nd', '3rd', '4th'
- **Unique Constraint**: (subject_code, semester_number, year_level)

#### SubjectOffering
- Represents a concrete offering of a subject
- **Fields**:
  - `subject`: ForeignKey to Subject
  - `teacher`: ForeignKey to TeacherProfile (nullable)
  - `year`: Year level
  - `section`: Section (A, B, C, D)
  - `school_year`: CharField (max_length=20)
- **Unique Constraint**: (subject, year, section, school_year)

#### Attendance
- **Fields**:
  - `student`: ForeignKey to StudentProfile
  - `subject_offering`: ForeignKey to SubjectOffering
  - `date`: DateField
  - `time`: TimeField
  - `status`: Choices - 'present', 'absent', 'late'
- **Unique Constraint**: (student, subject_offering, date)

#### Semester
- **Fields**: `name`, `school_year`
- **Unique Constraint**: (name, school_year)

---

## Application Structure

### Accounts App (`accounts/`)

**Purpose**: Manages user accounts and authentication

**Key Files**:
- `models.py`: User models (CustomUser, TeacherProfile, StudentProfile, ParentProfile)
- `views.py`: Account management views (CRUD operations for users)
- `forms.py`: Forms for user creation and editing
- `backends.py`: Custom authentication backend (email/username login)
- `middleware.py`: FirstLoginMiddleware (redirects first-time users to change password)
- `constants.py`: Constants (YEAR_LEVEL_CHOICES, SECTION_CHOICES, STUDENT_STATUS_CHOICES)
- `urls.py`: URL routing for account management

**Key Features**:
- Custom user authentication (email or username)
- First login password change requirement
- User role-based access control
- Account export functionality

### Academics App (`academics/`)

**Purpose**: Manages academic records, subjects, and attendance

**Key Files**:
- `models.py`: Academic models (Course, Subject, SubjectOffering, Attendance, Semester)
- `views.py`: Academic management views
- `forms.py`: Forms for subject and assignment management
- `urls.py`: URL routing for academic operations
- `management/commands/`: Management commands for data population

**Key Features**:
- Subject management (CRUD)
- Teacher-to-subject assignment
- Attendance marking
- Student enrollment in subjects

### Dashboard App (`dashboard/`)

**Purpose**: Provides role-specific dashboards

**Key Files**:
- `views.py`: Dashboard views for different user roles
- `templates/dashboard/`: HTML templates for dashboards
- `urls.py`: URL routing for dashboards

**Dashboard Types**:
1. **Admin Dashboard**: Overview of system statistics
2. **Teacher Dashboard**: Teaching assignments and attendance marking
3. **Student Dashboard**: Personal attendance overview
4. **Parent Dashboard**: Children's attendance tracking

### Reports App (`reports/`)

**Purpose**: Generates attendance and academic reports

**Key Files**:
- `views.py`: Report generation views
- `templates/reports/`: Report templates
- `urls.py`: URL routing for reports

**Report Types**:
- Attendance summary
- Detailed attendance reports
- Student details report
- Teacher details report
- Class/subject overview
- Parent-child summary
- Attendance timeline

### Core App (`core/`)

**Purpose**: Shared resources and base templates

**Key Files**:
- `templates/`: Base templates (base.html, base_student.html, base_parent.html, teacherbase.html)
- `static/`: CSS, JavaScript, and image files
- `views.py`: Core views

---

## URL Routing

### Root URLs (`Attendance_System/urls.py`)
```
/                           → Login page
/admin/                     → Django admin
/dashboard/                 → Dashboard routes
/academic/                  → Academic management routes
/reports/                   → Report routes
/accounts/                  → Account management routes
```

### Accounts URLs (`accounts/urls.py`)
```
/accounts/teachers/                    → Manage teachers
/accounts/teachers/add/                 → Add teacher
/accounts/teachers/<id>/edit/           → Edit teacher
/accounts/teachers/<id>/delete/        → Delete teacher
/accounts/student/                     → Manage students
/accounts/students/add/                → Add student
/accounts/student/<id>/edit/           → Edit student
/accounts/delete-student/<id>/         → Delete student
/accounts/parent/                      → Manage parents
/accounts/parent/add/                  → Add parent
/accounts/parent/<id>/edit/             → Edit parent
/accounts/parent/<id>/delete/          → Delete parent
/accounts/login/                       → Login
/accounts/change-password/             → Change password
/accounts/logout/                      → Logout
/accounts/accounts-dashboard/          → Accounts dashboard
/accounts/export-accounts/              → Export accounts
```

### Academics URLs (`academics/urls.py`)
```
/academic/subjects/                    → Manage subjects
/academic/subjects/add/                → Add subject
/academic/subjects/edit/<id>/          → Edit subject
/academic/subjects/delete/<id>/        → Delete subject
/academic/assignments/                  → View assignments
/academic/assignments/add-page/        → Add assignment
/academic/assignments/edit-page/<id>/  → Edit assignment
/academic/assignments/delete/<id>/      → Delete assignment
/academic/mark-attendance/             → Mark attendance
/academic/student-list                 → Student list
/academic/subject-assign/              → Subject assignment
```

### Dashboard URLs (`dashboard/urls.py`)
```
/dashboard/admin/                      → Admin dashboard
/dashboard/teacher/                     → Teacher dashboard
/dashboard/student/                     → Student dashboard
/dashboard/student-subjects/            → Student subjects
/dashboard/subject-attendance/          → Subject attendance overview
/dashboard/parent-dashboard            → Parent dashboard
/dashboard/children/                    → Children list
/dashboard/child/<id>/attendance/      → Child attendance overview
/dashboard/child/<id>/attendance/<sub>/ → Attendance detail per subject
```

### Reports URLs (`reports/urls.py`)
```
/reports/admin                          → Admin attendance report
/reports/parent-student                 → Parent student report
/reports/student-details/               → Student details report
/reports/teacher-deatil/                → Teacher details report
/reports/class-overview/                → Class subject overview
/reports/attendance-sumary/             → Attendance summary
/reports/detailed-attendance/           → Detailed attendance
/reports/parent-child-summary/          → Parent child summary
/reports/parent-child-timeline          → Parent attendance timeline
```

---

## Key Features

### 1. Multi-Role Authentication
- **Admin**: Full system access
- **Teacher**: Mark attendance, view student lists
- **Student**: View personal attendance
- **Parent**: View children's attendance

### 2. Custom Authentication Backend
- Login using username or email
- First-time login requires password change
- Middleware enforces password change on first login

### 3. Attendance Management
- Mark attendance by subject, date, and time
- Status options: Present, Absent, Late
- Unique constraint prevents duplicate entries per student/subject/date

### 4. Subject Management
- Create and manage subjects
- Assign teachers to subjects
- Organize by course, year level, and section
- Automatic student enrollment based on course/year/section

### 5. Reporting System
- Multiple report types for different stakeholders
- Attendance summaries and detailed reports
- Timeline views for attendance tracking
- Export capabilities

### 6. User Management
- CRUD operations for all user types
- Account export functionality
- Role-based access control

---

## Management Commands

### 1. Populate Attendance (`populate_attendance.py`)
**Purpose**: Populate attendance records for a date range

**Usage**:
```bash
python manage.py populate_attendance --start-date 2025-11-24 --end-date 2025-11-28
```

**Options**:
- `--start-date`: Start date in YYYY-MM-DD format (default: 2025-11-24)
- `--end-date`: End date in YYYY-MM-DD format (default: 2025-11-28)
- `--status`: Attendance status - 'present', 'absent', 'late', or 'random' (default: random)

**Features**:
- Creates attendance records for all students enrolled in all subject offerings
- Generates random attendance times (8 AM - 5 PM)
- Assigns random status if not specified

### 2. Assign Teachers (`assign_teachers.py`)
**Purpose**: Assign teachers to existing subject offerings

**Usage**:
```bash
python manage.py assign_teachers --school-year 2024-2025
```

**Options**:
- `--school-year`: School year for assignments (default: 2024-2025)
- `--assign-unassigned-only`: Only assign to offerings without teachers

**Features**:
- Round-robin distribution of teachers
- Skips already assigned offerings
- Provides summary by teacher

### 3. Create and Assign Teachers (`create_and_assign_teachers.py`)
**Purpose**: Create subject offerings and assign teachers

**Usage**:
```bash
python manage.py create_and_assign_teachers --school-year 2024-2025
```

**Options**:
- `--school-year`: School year for offerings (default: 2024-2025)

**Features**:
- Creates offerings based on existing students
- Automatically enrolls students in subjects
- Distributes teachers evenly
- Handles all year/section combinations

### 4. Export Accounts (`export_accounts.py`)
**Purpose**: Export all accounts to Excel

**Usage**:
```bash
python manage.py export_accounts
```

**Features**:
- Exports students grouped by year/section
- Exports parents grouped by children's sections
- Exports teachers with assigned subjects
- Creates Excel file: `school_accounts.xlsx`

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Django 5.2.7
- SQLite3 (included with Python)

### Installation Steps

1. **Clone or navigate to the project directory**
```bash
cd "d:\midterm Project web Dev\Attendance_System"
```

2. **Install dependencies** (if using requirements.txt)
```bash
pip install django==5.2.7
```

3. **Run migrations**
```bash
python manage.py migrate
```

4. **Create superuser** (optional)
```bash
python manage.py createsuperuser
```

5. **Run development server**
```bash
python manage.py runserver
```

6. **Access the application**
- Open browser: `http://127.0.0.1:8000/`
- Login with your credentials

### Initial Data Setup

1. **Create courses and subjects** (via admin or UI)
2. **Create teachers, students, and parents** (via accounts management)
3. **Assign teachers to subjects**:
```bash
python manage.py create_and_assign_teachers --school-year 2024-2025
```
4. **Populate attendance** (optional):
```bash
python manage.py populate_attendance --start-date 2025-11-24 --end-date 2025-11-28
```

---

## User Roles & Permissions

### Admin
- **Full Access**: All features
- **Can Manage**: Users, subjects, courses, assignments
- **Can View**: All reports and dashboards
- **Can Export**: Account data

### Teacher
- **Can Mark**: Attendance for assigned subjects
- **Can View**: Student lists, assigned subjects
- **Can Access**: Teacher dashboard
- **Cannot**: Manage users or system settings

### Student
- **Can View**: Personal attendance, enrolled subjects
- **Can Access**: Student dashboard
- **Cannot**: Mark attendance or view other students

### Parent
- **Can View**: Children's attendance, reports
- **Can Access**: Parent dashboard
- **Cannot**: Mark attendance or manage data

---

## API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout
- `POST /accounts/change-password/` - Change password

### Account Management (Admin only)
- `GET /accounts/teachers/` - List teachers
- `POST /accounts/teachers/add/` - Create teacher
- `POST /accounts/teachers/<id>/edit/` - Update teacher
- `POST /accounts/teachers/<id>/delete/` - Delete teacher
- Similar endpoints for students and parents

### Academic Management (Admin/Teacher)
- `GET /academic/subjects/` - List subjects
- `POST /academic/subjects/add/` - Create subject
- `GET /academic/assignments/` - List assignments
- `POST /academic/mark-attendance/` - Mark attendance

### Reports
- `GET /reports/admin` - Admin attendance report
- `GET /reports/student-details/` - Student details
- `GET /reports/attendance-sumary/` - Attendance summary

---

## Database Schema Relationships

```
CustomUser (1) ──→ (1) TeacherProfile
CustomUser (1) ──→ (1) StudentProfile
CustomUser (1) ──→ (1) ParentProfile

StudentProfile (N) ──→ (1) Course
StudentProfile (N) ──→ (N) Subject (ManyToMany)
StudentProfile (N) ──→ (N) ParentProfile (ManyToMany)

Subject (N) ──→ (1) Course
SubjectOffering (N) ──→ (1) Subject
SubjectOffering (N) ──→ (1) TeacherProfile

Attendance (N) ──→ (1) StudentProfile
Attendance (N) ──→ (1) SubjectOffering
```

---

## Constants

### Year Levels (`accounts/constants.py`)
- '1st' - 1st Year
- '2nd' - 2nd Year
- '3rd' - 3rd Year
- '4th' - 4th Year

### Sections
- 'a' - Section A
- 'b' - Section B
- 'c' - Section C
- 'd' - Section D

### Student Status
- 'reg' - Regular
- 'irreg' - Irregular

### Attendance Status
- 'present' - Present
- 'absent' - Absent
- 'late' - Late

---

## Security Features

1. **CSRF Protection**: Enabled for all forms
2. **Authentication Required**: Most views require login
3. **Role-Based Access**: Views check user roles
4. **Password Validation**: Django's built-in validators
5. **First Login Enforcement**: Middleware redirects first-time users
6. **SQL Injection Protection**: Django ORM prevents SQL injection

---

## Static Files

### CSS Files (`core/static/css/`)
- `styles.css` - Main stylesheet
- `login.css` - Login page styles
- `teacher.css` - Teacher dashboard styles
- `student_sub.css` - Student subject styles
- `report.css` - Report styles
- `assign_teacher.css` - Assignment page styles

### JavaScript Files (`core/static/js/`)
- `scripts.js` - Main JavaScript
- `reports.js` - Report functionality

### Images (`core/static/images/`)
- Various icons and logos for the application

---

## Future Enhancements

Potential improvements for the system:
1. Email notifications for attendance
2. Mobile app support
3. Advanced analytics and charts
4. Bulk attendance import/export
5. Integration with external systems
6. Real-time attendance tracking
7. QR code-based attendance
8. Automated report scheduling

---

## Troubleshooting

### Common Issues

1. **First Login Redirect Loop**
   - Ensure `FirstLoginMiddleware` is in `MIDDLEWARE` settings
   - Check that `first_login` field is properly set

2. **Attendance Not Saving**
   - Verify unique constraint: (student, subject_offering, date)
   - Check that student is enrolled in the subject

3. **Teacher Assignment Issues**
   - Ensure subject offerings exist
   - Check year/section combinations match student data

4. **Static Files Not Loading**
   - Run `python manage.py collectstatic` (production)
   - Check `STATICFILES_DIRS` in settings.py

---

## Contact & Support

For issues or questions about the Attendance System, please refer to the project repository or contact the development team.

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Django Version**: 5.2.7

