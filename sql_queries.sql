-- PostgreSQL examples for the recruitment intelligence portal.
-- Table names follow Django's default app_model naming convention.

-- SELECT, WHERE, AND, OR, LIKE, ORDER BY and LIMIT candidate search.
SELECT c.id, c.candidate_name, c.email, c.skills, c.expected_salary
FROM screening_candidate AS c
WHERE c.is_valid = TRUE
  AND (c.candidate_name ILIKE '%ana%' OR c.skills ILIKE '%python%')
ORDER BY c.created_at DESC
LIMIT 25;

-- BETWEEN salary filter.
SELECT candidate_name, expected_salary
FROM screening_candidate
WHERE expected_salary BETWEEN 400000 AND 800000
ORDER BY expected_salary;

-- COUNT, SUM, MIN, MAX, AVG, GROUP BY and HAVING.
SELECT r.code, COUNT(c.id) AS candidate_count,
       SUM(c.expected_salary) AS salary_sum,
       MIN(c.expected_salary) AS salary_min,
       MAX(c.expected_salary) AS salary_max,
       AVG(c.expected_salary) AS salary_avg
FROM screening_jobrole AS r
LEFT JOIN screening_candidate AS c ON c.job_role_id = r.id
GROUP BY r.id, r.code
HAVING COUNT(c.id) >= 2
ORDER BY candidate_count DESC;

-- Selected/rejected aggregation.
SELECT s.status, COUNT(*) AS total, AVG(s.rule_score) AS average_rule_score
FROM screening_screeningresult AS s
GROUP BY s.status
ORDER BY s.status;

-- INNER JOIN candidates and roles.
SELECT c.candidate_name, c.email, r.code, r.name
FROM screening_candidate AS c
INNER JOIN screening_jobrole AS r ON r.id = c.job_role_id;

-- FULL OUTER JOIN shows roles without candidates and candidates without an available role.
SELECT r.code, r.name, c.candidate_name
FROM screening_jobrole AS r
FULL OUTER JOIN screening_candidate AS c ON c.job_role_id = r.id
ORDER BY r.code NULLS LAST, c.candidate_name NULLS LAST;

-- NATURAL JOIN demonstration. CTE aliases make the shared key intentional and safe.
WITH candidates AS (SELECT id AS candidate_id, candidate_name FROM screening_candidate),
     results AS (SELECT candidate_id, status, rule_score FROM screening_screeningresult)
SELECT candidate_id, candidate_name, status, rule_score
FROM candidates NATURAL JOIN results;

-- UNION ALL selected and waitlisted candidates.
SELECT c.id, c.candidate_name, 'selected' AS pool
FROM screening_candidate c JOIN screening_screeningresult s ON s.candidate_id = c.id
WHERE s.status = 'SELECTED'
UNION ALL
SELECT c.id, c.candidate_name, 'waitlisted' AS pool
FROM screening_candidate c JOIN screening_screeningresult s ON s.candidate_id = c.id
WHERE s.status = 'WAITLISTED';

-- INTERSECT candidates whose skills contain both Python and Django.
SELECT id, candidate_name FROM screening_candidate WHERE skills ILIKE '%python%'
INTERSECT
SELECT id, candidate_name FROM screening_candidate WHERE skills ILIKE '%django%';
