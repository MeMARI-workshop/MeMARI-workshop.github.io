"""Create lists of papers and program committee members.

TODO Needs testing.
"""
import getpass
from pathlib import Path

import openreview
import pandas as pd
from tqdm import tqdm

client = openreview.Client(
    baseurl="https://api.openreview.net",
    username=input("username: "),
    password=getpass.getpass("password: "),
)

memari_orig = pd.read_csv("~/Downloads/MemARI_2022_@_NeurIPS_paper_status.csv")

memari_orig = memari_orig[memari_orig["decision"] != "Reject"].reset_index()

videos = pd.read_csv("~/Downloads/MemARI Decision spreadsheet - Sheet1.csv")

memari = pd.merge(
    memari_orig, videos, left_on="number", right_on="paper_number"
)

memari["idx"] = memari.index + 1

memari["paper"] = memari.apply(
    lambda x: f" [Paper](papers/paper_{x['number']}.pdf)."
    if x["Archival"] == "Yes"
    else "",
    axis=1,
)

memari["paper_or_poster"] = memari["paper"] + memari.apply(
    lambda x: f" [Poster](posters/poster_{x['number']}.pdf)."
    if pd.notna(x["poster"])
    else ""
    if x["Archival"] == "Yes"
    else " [Poster](unavailable).",
    axis=1,
)

accepted = (
    memari["idx"].astype("string")
    + ". "
    + memari["title"]
    + ". "
    + memari["authors"].str.replace("|", ", ", regex=False)
    + "."
    + memari["paper_or_poster"]
    + " "
    + "[Video]("
    + memari["Youtube Link"].fillna("unavailable")
    + ")."
)
accepted[0]

accepted.to_csv("accepted.md", header=False, index=False, sep="\t")

notes = client.get_all_notes(
    content={"venueid": "NeurIPS.cc/2022/Workshop/MemARI"}
)
accepted_and_archival = memari.loc[
    (memari["Archival"] == "Yes") & (memari["decision"] != "Reject"), "number"
]
notes_latest = {}
for note in notes:
    if note.number not in accepted_and_archival:
        continue
    previous = notes_latest.get(note.number)
    if previous is None or note.tmdate > previous.tmdate:
        notes_latest[note.number] = note
for note in tqdm(notes_latest.values()):
    (Path("papers") / f"paper_{note.number}.pdf").write_bytes(
        client.get_pdf(note.id)
    )

reviewers = pd.read_csv(
    "~/Downloads/MemARI_2022_@_NeurIPS_reviewer_status.csv"
)

reviewers_true = reviewers.loc[
    reviewers["num submitted reviews"] > 0, :
].reset_index()

reviewers_true["idx"] = reviewers_true.index + 1

(
    reviewers_true["idx"].astype("string")
    + ". "
    + reviewers_true["name"]
    + ". "
    + reviewers_true["institution name"]
    + "."
).to_csv("reviewers.md", header=False, index=False, sep="\t")
