"""
make_payment_snapshot.py

Task 7 already gives us `data/students.csv` - that's the "browse" skill
profile, read straight from the student's record. Once the Pay-100-and-Apply
flow went live, the matching call on the apply side doesn't read that table
directly anymore - it reads whatever skill snapshot the payment service
forwards at the moment the student confirms payment.

In a perfect world that snapshot is identical to the browse profile. In
practice it isn't always, for boring reasons:
  - the student edited their skills in the few seconds between browsing and
    paying, and the snapshot was taken slightly before the edit landed
  - the payment service timed out talking to the profile service and fell
    back to whatever it had cached
  - (rare) the snapshot arrives empty - profile service was down, payment
    still went through

This script builds that snapshot so Task 9 has something real to compare
against, instead of just running the same input twice and calling it a
day. Rates below are deliberately small - most students should look
identical, this is about catching the edge cases, not manufacturing chaos.

Run:
    python src/make_payment_snapshot.py
"""

import random
import pandas as pd

SEED = 7  # different seed from data_gen.py on purpose - this is a separate noise process
random.seed(SEED)

STALE_RATE = 0.04   # snapshot is missing one skill the student has now
EMPTY_RATE = 0.01   # snapshot arrives empty - simulates profile service being unreachable


def build_snapshot(students_df):
    rows = []
    for _, srow in students_df.iterrows():
        skills = [s.strip() for s in str(srow["skills"]).split(",") if s.strip()]
        roll = random.random()

        if roll < EMPTY_RATE:
            snapshot_skills = ""
            note = "empty_snapshot"
        elif roll < EMPTY_RATE + STALE_RATE and len(skills) > 1:
            dropped = random.choice(skills)
            snapshot_skills = ",".join(s for s in skills if s != dropped)
            note = f"stale_snapshot (missing {dropped})"
        else:
            snapshot_skills = ",".join(skills)
            note = "clean"

        rows.append({
            "student_id": srow["student_id"],
            "skills_at_payment": snapshot_skills,
            "snapshot_note": note,
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    students_df = pd.read_csv("../data/students.csv")
    snap_df = build_snapshot(students_df)
    snap_df.to_csv("../data/payment_snapshot.csv", index=False)

    print(f"wrote {len(snap_df)} rows -> data/payment_snapshot.csv")
    print(snap_df["snapshot_note"].apply(lambda n: n.split(" ")[0]).value_counts())
