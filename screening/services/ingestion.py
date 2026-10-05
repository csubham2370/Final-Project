"""CSV/XLSX validation and cleaning with explicit core-Python examples for viva."""
import copy
import re
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = (
    "candidate_name", "email", "phone", "college", "applied_role", "skills",
    "experience_months", "notice_period_days", "expected_salary", "resume_text",
    "portfolio_url", "historical_selection_status",
)
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[1-9]\d{9,14}$")


class IngestionError(Exception):
    pass


class MissingColumnsError(IngestionError):
    pass


class RowValidationError(IngestionError):
    pass


def normalize_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (TypeError, ValueError) as exc:
            raise RowValidationError(str(exc)) from exc
    return wrapper


@dataclass(frozen=True)
class Score:
    value: float = 0

    def __add__(self, other):
        return Score(self.value + (other.value if isinstance(other, Score) else float(other)))


class BaseCleaner:
    def clean(self, value):
        raise NotImplementedError


class StringCleaner(BaseCleaner):
    def clean(self, value):
        text = "" if pd.isna(value) else str(value).strip()
        text = text.removeprefix("mailto:").removesuffix(".")
        parts = [piece for piece in text.split() if piece]
        return " ".join(parts)


def recursive_flatten(items):
    if not items:
        return []
    head, *tail = items
    return (recursive_flatten(head) if isinstance(head, list) else [head]) + recursive_flatten(tail)


def demonstrate_scope():
    global INGESTION_RUNS
    try:
        INGESTION_RUNS += 1
    except NameError:
        INGESTION_RUNS = 1
    count = 0
    def increment():
        nonlocal count
        count += 1
    increment()
    return INGESTION_RUNS, count


@normalize_errors
def clean_record(record, *required, **options):
    cleaner = StringCleaner()
    working = copy.copy(record)
    original = copy.deepcopy(record)
    fields = required or REQUIRED_COLUMNS
    cleaned = {key: cleaner.clean(working.get(key, "")) for key in fields}
    cleaned["candidate_name"] = cleaned["candidate_name"].title()
    cleaned["email"] = cleaned["email"].lower()
    cleaned["phone"] = re.sub(r"[\s()-]", "", cleaned["phone"])
    cleaned["applied_role"] = cleaned["applied_role"].upper()
    skill_tuple = tuple(s.strip().lower() for s in cleaned["skills"].split(",") if s.strip())
    skill_set = {s for s in skill_tuple}
    cleaned["skills"] = ", ".join(sorted(skill_set))
    cleaned["skill_fingerprint"] = frozenset(skill_set)
    if not cleaned["candidate_name"]:
        raise RowValidationError("candidate_name is required")
    if not EMAIL_RE.fullmatch(cleaned["email"]):
        raise RowValidationError("invalid email")
    if not PHONE_RE.fullmatch(cleaned["phone"]):
        raise RowValidationError("invalid phone")
    for field in ("experience_months", "notice_period_days", "expected_salary"):
        number = float(cleaned[field])
        if number < 0:
            raise RowValidationError(f"{field} cannot be negative")
        cleaned[field] = int(number) if field != "expected_salary" else number
    if options.get("include_original"):
        cleaned["original"] = original
    return cleaned


def read_dataframe(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        frame = pd.read_csv(path)
    elif suffix == ".xlsx":
        frame = pd.read_excel(path)
    else:
        raise IngestionError("Only CSV and XLSX files are supported.")
    if frame.empty:
        raise IngestionError("The uploaded file is empty.")
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise MissingColumnsError("Missing columns: " + ", ".join(sorted(missing)))
    return frame


def ingest_file(path, accepted_path, rejected_path, progress=None):
    frame = read_dataframe(path).drop_duplicates()
    accepted, rejected = [], []
    rows = iter(frame.to_dict(orient="records"))
    index = 0
    while True:
        try:
            row = next(rows)
        except StopIteration:
            break
        index += 1
        if not any(str(v).strip() for v in row.values()):
            continue
        try:
            cleaned = clean_record(row)
            cleaned.pop("skill_fingerprint", None)
            accepted.append(cleaned)
        except RowValidationError as exc:
            rejected.append({**row, "error_reason": str(exc)})
        if progress:
            progress(index, len(frame), len(accepted), len(rejected))
    pd.DataFrame(accepted, columns=REQUIRED_COLUMNS).to_csv(accepted_path, index=False)
    pd.DataFrame(rejected, columns=(*REQUIRED_COLUMNS, "error_reason")).to_csv(rejected_path, index=False)
    demonstrate_scope()
    return accepted, rejected
