from django.core.management.base import BaseCommand
import pandas as pd
from accounts.models import StudentProfile, TeacherProfile, ParentProfile

class Command(BaseCommand):
    help = "Export all accounts to Excel, with students and parents grouped by Year/Section"

    def handle(self, *args, **kwargs):
        # --- Students by Year/Section ---
        students = StudentProfile.objects.all()
        student_groups = {}
        for s in students:
            key = f"Y{s.year}_S{s.section}"  # Sheet name
            if key not in student_groups:
                student_groups[key] = []
            student_groups[key].append({
                "First Name": s.first_name,
                "Last Name": s.last_name,
                "Email": s.user.email,
                "Password": s.user.plain_password if hasattr(s.user, 'plain_password') else "N/A",
            })

        # --- Parents grouped by their children's section ---
        parents = ParentProfile.objects.all()
        parent_groups = {}
        for p in parents:
            for child in p.students.all():
                key = f"Y{child.year}_S{child.section}"
                if key not in parent_groups:
                    parent_groups[key] = []
                parent_groups[key].append({
                    "Parent First Name": p.first_name,
                    "Parent Last Name": p.last_name,
                    "Child Name": f"{child.first_name} {child.last_name}",
                    "Email": p.user.email,
                    "Password": p.user.plain_password if hasattr(p.user, 'plain_password') else "N/A",
                })

        # --- Teachers (single sheet) ---
        teachers = TeacherProfile.objects.all()
        teacher_records = []
        for t in teachers:
            subjects = ", ".join([s.subject_code for s in t.subjects.all()])
            teacher_records.append({
                "First Name": t.first_name,
                "Last Name": t.last_name,
                "Subjects": subjects,
                "Email": t.user.email,
                "Password": t.user.plain_password if hasattr(t.user, 'plain_password') else "N/A",
            })

        # --- Export to Excel ---
        with pd.ExcelWriter("school_accounts.xlsx") as writer:
            # Students sheets
            for sheet_name, records in student_groups.items():
                df = pd.DataFrame(records)
                df.to_excel(writer, sheet_name=f"Students_{sheet_name}", index=False)

            # Parents sheets
            for sheet_name, records in parent_groups.items():
                df = pd.DataFrame(records)
                df.to_excel(writer, sheet_name=f"Parents_{sheet_name}", index=False)

            # Teachers sheet
            df_teachers = pd.DataFrame(teacher_records)
            df_teachers.to_excel(writer, sheet_name="Teachers", index=False)

        self.stdout.write(self.style.SUCCESS("Accounts exported successfully to school_accounts.xlsx"))
