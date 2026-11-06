import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.detectors.nli import nli_scores

attendance = "Students must maintain at least 75% attendance to qualify for final examinations."

pairs = [
    ("Supported claim", attendance,
     "Students need 75% attendance to be eligible for the final exams."),
    ("Contradicting claim", attendance,
     "Students do not need any minimum attendance for the final exams."),
    ("Negation flipped",
     "Unused leave cannot be carried over to the next year.",
     "Unused leave can be carried over to the next year."),
    ("Unrelated claim",
     "Merit scholarships are awarded to students with a CGPA of 3.5 or above.",
     "The library closes at 9 pm."),
]

for name, evidence, claim in pairs:
    scores = nli_scores(evidence, claim)
    best = max(scores, key=scores.get)
    shown = ", ".join(f"{k}={v:.2f}" for k, v in scores.items())
    print(f"{name}: {best.upper()}   ({shown})")