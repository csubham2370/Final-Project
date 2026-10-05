from django.core.cache import cache
from .nlp import analyze_resume


def rule_score(candidate):
    required = {x.strip().lower() for x in candidate.job_role.required_skills.split(",") if x.strip()}
    actual = {x.strip().lower() for x in candidate.skills.split(",") if x.strip()}
    skill_score = len(required & actual) / max(len(required), 1)
    experience = min(candidate.experience_months / max(candidate.job_role.min_experience_months, 1), 1)
    salary = 1.0 if not candidate.job_role.max_salary or candidate.expected_salary <= candidate.job_role.max_salary else 0.25
    return round((skill_score * 60 + experience * 25 + salary * 15), 2)


def nlp_score(candidate):
    return analyze_resume(candidate.resume_text, candidate.job_role.required_skills.split(","))["skill_match_score"]


def cache_top_candidates(role_id, payload, seconds=300):
    cache.set(f"top-candidates:{role_id}", payload, seconds)
