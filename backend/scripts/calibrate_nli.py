import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.detectors.nli import nli_scores
from app.detectors.similarity import similarity

ATTENDANCE = "Students must maintain at least 75% attendance to qualify for final examinations."
LEAVE = "Full-time staff receive 15 days of annual paid leave per calendar year."
CARRY = "Unused leave cannot be carried over to the next year."
SCHOLAR = "Merit scholarships are awarded to students with a CGPA of 3.5 or above."

pairs = [
    ("1 supported", ATTENDANCE, "Students need 75% attendance to be eligible for the final exams."),
    ("2 contradicting", ATTENDANCE, "Students do not need any minimum attendance for the final exams."),
    ("3 negation flipped", CARRY, "Unused leave can be carried over to the next year."),
    ("4 unrelated (library)", SCHOLAR, "The library closes at 9 pm."),
    ("5 unrelated (cafeteria)", ATTENDANCE, "The cafeteria serves lunch at noon."),
    ("6 related, not in evidence", SCHOLAR, "Scholarships are only given to students from the computer science department."),
    ("7 related, not in evidence", LEAVE, "Part-time staff also receive paid leave."),
    ("8 paraphrase supported", SCHOLAR, "Students with a high CGPA can get a merit scholarship."),
]

for name, evidence, claim in pairs:
    sim = similarity(evidence, claim)
    scores = nli_scores(evidence, claim)
    best = max(scores, key=scores.get)
    shown = ", ".join(f"{k[:5]}={v:.2f}" for k, v in scores.items())
    print(f"{name:28s} sim={sim:.2f}  NLI={best.upper():13s} ({shown})")