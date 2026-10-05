from django.core.management.base import BaseCommand
from screening.models import JobRole, User


class Command(BaseCommand):
    help = "Create deterministic local evaluator accounts and the sample job role."

    def handle(self, *args, **options):
        role, _ = JobRole.objects.update_or_create(code="PY-DJ", defaults={"name":"Python Django Fresher", "required_skills":"python,django,postgresql,rest", "min_experience_months":6, "max_salary":700000, "is_active":True})
        accounts = [
            ("admin", "admin@example.com", "ADMIN", True),
            ("hr", "hr@example.com", "HR", False),
            ("interviewer", "interviewer@example.com", "INTERVIEWER", False),
        ]
        for username, email, user_role, staff in accounts:
            user, _ = User.objects.get_or_create(username=username, defaults={"email":email})
            user.email, user.role, user.is_staff = email, user_role, staff
            user.is_superuser = user_role == "ADMIN"
            user.set_password("Assessment@123")
            user.save()
        self.stdout.write(self.style.SUCCESS(f"Seeded role {role.code} and admin/hr/interviewer accounts."))
