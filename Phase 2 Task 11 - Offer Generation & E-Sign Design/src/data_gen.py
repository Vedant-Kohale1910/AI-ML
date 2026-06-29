"""
data_gen.py

Task 11 depends on "Integrity data from Week 1" - the human-reviewed
incident labels that say, after the fact, which flagged sessions were
actually cheating and which weren't. We don't have that review log yet
(it's owned by a different team/week), so this builds a stand-in that's
shaped the same way: one row per 60-second monitoring window during an
assessment, the raw signals the proctoring client would have captured,
and a label_cheating column standing in for what a human reviewer
eventually confirmed.

Five behaviour archetypes, because the whole point of this task is that
"honest but unusual" and "actually cheating" can look similar on any
single signal:

  honest_normal            - nothing going on, the common case
  honest_distracted         - notification, glance at phone, briefly
                              checked something - normal human behaviour,
                              NOT cheating, but trips a naive rule
  honest_environment_noise - bad webcam angle / lighting causes face
                              detection to drop out, a roommate talks in
                              the next room - NOT cheating, but also trips
                              a naive rule (this + the one above are the
                              two groups currently driving false positives)
  cheating_lookup            - genuinely looking at a phone/notes/second
                              device, searching answers in another tab
  cheating_collaboration     - someone else in frame, talking to them

Run:
    python src/data_gen.py
"""

import random
import numpy as np
import pandas as pd

SEED = 21
random.seed(SEED)
np.random.seed(SEED)

N_STUDENTS = 420
WINDOWS_PER_STUDENT_RANGE = (4, 9)  # a 30-60 min assessment chopped into ~60s windows

ARCHETYPE_WEIGHTS = {
    "honest_normal": 0.58,
    "honest_distracted": 0.16,
    "honest_environment_noise": 0.10,
    "cheating_lookup": 0.09,
    "cheating_collaboration": 0.07,
}


def _trunc_normal(mean, std, low, high, size=1):
    vals = np.random.normal(mean, std, size=size)
    return np.clip(vals, low, high)


def _gen_window(archetype):
    """One window's raw signals for a given archetype. Numbers are
    hand-tuned to be roughly plausible for a 60s window, not pulled from
    any real proctoring vendor's spec - this is a stand-in dataset."""

    if archetype == "honest_normal":
        eye_away = _trunc_normal(1.5, 1.2, 0, 8)[0]
        face_missing = _trunc_normal(0.5, 0.6, 0, 5)[0]
        tab_switch = np.random.poisson(0.2)
        focus_loss = np.random.poisson(0.15)
        multi_face = 1 if random.random() < 0.005 else 0
        audio_voice = 1 if random.random() < 0.03 else 0
        head_pose = _trunc_normal(6, 4, 0, 30)[0]
        label = 0

    elif archetype == "honest_distracted":
        # checked phone for a notification, glanced away, maybe alt-tabbed
        # to look at a legit reference doc once or twice - all normal
        eye_away = _trunc_normal(8, 3, 2, 20)[0]
        face_missing = _trunc_normal(1.5, 1.2, 0, 6)[0]
        tab_switch = np.random.poisson(1.8)
        focus_loss = np.random.poisson(1.3)
        multi_face = 1 if random.random() < 0.01 else 0
        audio_voice = 1 if random.random() < 0.05 else 0
        head_pose = _trunc_normal(14, 6, 0, 40)[0]
        label = 0

    elif archetype == "honest_environment_noise":
        # bad lighting / webcam angle drops face tracking, a roommate
        # talks in the background - annoying for the system, not cheating
        eye_away = _trunc_normal(3, 2, 0, 10)[0]
        face_missing = _trunc_normal(7, 3, 1, 20)[0]
        tab_switch = np.random.poisson(0.4)
        focus_loss = np.random.poisson(0.3)
        multi_face = 1 if random.random() < 0.05 else 0  # poster/photo on the wall, briefly misread
        audio_voice = 1 if random.random() < 0.65 else 0
        head_pose = _trunc_normal(10, 6, 0, 35)[0]
        label = 0

    elif archetype == "cheating_lookup":
        # genuinely looking at a phone or second device, searching in another tab
        eye_away = _trunc_normal(20, 6, 8, 45)[0]
        face_missing = _trunc_normal(3, 2, 0, 12)[0]
        tab_switch = np.random.poisson(7)
        focus_loss = np.random.poisson(5)
        multi_face = 1 if random.random() < 0.03 else 0
        audio_voice = 1 if random.random() < 0.10 else 0
        head_pose = _trunc_normal(25, 8, 5, 60)[0]
        label = 1

    elif archetype == "cheating_collaboration":
        # someone else is in frame / audible, actively helping
        eye_away = _trunc_normal(11, 5, 2, 30)[0]
        face_missing = _trunc_normal(2, 2, 0, 10)[0]
        tab_switch = np.random.poisson(2.5)
        focus_loss = np.random.poisson(2)
        multi_face = 1 if random.random() < 0.80 else 0
        audio_voice = 1 if random.random() < 0.85 else 0
        head_pose = _trunc_normal(35, 12, 5, 75)[0]
        label = 1

    else:
        raise ValueError(archetype)

    return {
        "eye_away_duration_sec": round(float(eye_away), 1),
        "face_missing_duration_sec": round(float(face_missing), 1),
        "tab_switch_count": int(tab_switch),
        "window_focus_loss_count": int(focus_loss),
        "multiple_faces_detected": int(multi_face),
        "audio_voice_detected": int(audio_voice),
        "head_pose_deviation_deg": round(float(head_pose), 1),
        "label_cheating": label,
        "archetype": archetype,  # kept for analysis/debugging, not a model feature
    }


def make_dataset():
    archetypes = list(ARCHETYPE_WEIGHTS.keys())
    weights = list(ARCHETYPE_WEIGHTS.values())

    rows = []
    session_counter = 1
    for student_id in range(1, N_STUDENTS + 1):
        # most students are consistently one archetype for their whole
        # assessment (people don't usually switch behaviour mid-test),
        # with a small chance of one stray window going the other way
        primary = random.choices(archetypes, weights=weights, k=1)[0]
        n_windows = random.randint(*WINDOWS_PER_STUDENT_RANGE)
        session_id = f"S{session_counter:05d}"
        session_counter += 1

        for w in range(n_windows):
            archetype = primary
            if random.random() < 0.08:  # one odd window - nobody is perfectly consistent
                archetype = random.choices(archetypes, weights=weights, k=1)[0]

            row = _gen_window(archetype)
            row.update({
                "session_id": session_id,
                "student_id": student_id,
                "window_index": w + 1,
            })
            rows.append(row)

    df = pd.DataFrame(rows)
    cols = [
        "session_id", "student_id", "window_index",
        "eye_away_duration_sec", "face_missing_duration_sec", "tab_switch_count",
        "window_focus_loss_count", "multiple_faces_detected", "audio_voice_detected",
        "head_pose_deviation_deg", "label_cheating", "archetype",
    ]
    df = df[cols].sample(frac=1, random_state=SEED).reset_index(drop=True)

    # split by student, not by row - windows from the same student must
    # stay in one split, otherwise the model could "learn the student"
    # rather than learn the signal, and the held-out numbers would lie.
    student_ids = df["student_id"].unique().tolist()
    random.shuffle(student_ids)
    n = len(student_ids)
    n_train = round(n * 0.7)
    n_val = round(n * 0.15)
    train_ids = set(student_ids[:n_train])
    val_ids = set(student_ids[n_train:n_train + n_val])
    test_ids = set(student_ids[n_train + n_val:])

    def split_for(sid):
        if sid in train_ids:
            return "train"
        if sid in val_ids:
            return "val"
        return "test"

    df["split"] = df["student_id"].apply(split_for)
    return df


if __name__ == "__main__":
    df = make_dataset()
    df.to_csv("../data/proctoring_events.csv", index=False)
    print(f"wrote {len(df)} rows -> data/proctoring_events.csv")
    print(df["split"].value_counts())
    print()
    print("label balance overall:")
    print(df["label_cheating"].value_counts(normalize=True).round(3))
    print()
    print("archetype counts:")
    print(df["archetype"].value_counts())
