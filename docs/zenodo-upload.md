# Getting the dated, citable record (Zenodo + GitHub)

Two independent timestamps under your name: a Zenodo DOI (permanent, citable, run by CERN) and a GitHub release. Budget about 30 minutes.

## Before you start

1. **ORCID.** Done: 0009-0004-3401-7369. Sign in to Zenodo with it so the record links to your profile automatically.
2. **Zenodo account.** Go to zenodo.org and sign in with GitHub or ORCID.
3. **No placeholders remain.** The DOI 10.5281/zenodo.22325883 and the repository https://github.com/glott1993/peer-critique-panel are in every file.

## Zenodo upload

1. **New upload.** Drag in `proposal/tiered-peer-critique-proposal.pdf`. You can add the HTML too.
2. **Reserve the DOI first.** In the upload form, under Digital Object Identifier, choose to get a DOI now (Zenodo reserves it before you publish). Copy it. That lets the DOI appear inside the PDF, README, and CITATION.cff before the record goes live. Send it to me and I'll drop it in and rebuild; then replace the uploaded PDF with the rebuilt one.
3. **Fill the fields** (copy from below).
4. **Publish.** A published Zenodo record cannot be deleted, which is the point: the timestamp is permanent. Fixes go in as new versions, and the concept DOI always resolves to the latest one.

### Fields to paste

- **Resource type:** Publication, then Preprint (Working paper also fits).
- **Title:** A Tiered Peer-Critique Architecture for AI Answers
- **Creators:** Lott, George W.; ORCID 0009-0004-3401-7369; affiliation optional (an LLC or "Independent" is fine).
- **Publication date:** the day you publish.
- **Version:** 1.1
- **License:** Creative Commons Attribution 4.0 International
- **Keywords:** multi-agent debate; scalable oversight; LLM-as-a-judge; model routing; mixture of agents; peer critique; AI evaluation; ensemble methods
- **Related works** (optional): the GitHub repository URL, relation "is supplemented by".
- **Description:** the abstract below.

### Abstract

No single AI model is best at everything, and none is reliable at knowing its own weak spots. Multi-model councils are now shipped products and multi-agent debate is an active research line. This working paper proposes what should happen after a panel of models is convened: the answer has to earn its release. The current models from every major lab, grouped into class-matched tiers, decompose a request, bid on its parts, challenge each other's drafts under seat anonymity with evidence required, and revise until they agree. A dedicated hub that never writes an answer interrogates the result within a question budget and enforces verifiable checks: code runs, sources resolve, figures recompute. Release requires panel agreement, no open hub questions, and passing checks; deadlocks escalate across tiers or ship with the dispute flagged to the user. A persistent, version-stamped catalogue records who was challenged, corrected, and later shown wrong, and feeds the hub's questions so the same class of error is caught sooner. The paper positions the design against AI safety via debate, multi-agent debate, mixture-of-agents, LLM-as-a-judge, and model routing; states what it does not claim; and specifies a compute-matched pilot on checkable tasks that could falsify it. A single-file browser prototype of the protocol accompanies the paper.

### Additional notes field

Drafted with the assistance of Claude (Anthropic). A browser prototype of the protocol is available in the linked repository. Pilot results will be added as a new version when available.

## GitHub

1. Create a **public** repository (a name like `peer-critique-panel` works). Upload the contents of the zip so `README.md` sits at the root.
2. Once the DOI is filled in, create a **release** tagged `v1.1` and attach the PDF. The commit and release timestamps are your second, independent dating.
3. Optional but worth it: in Zenodo, open the GitHub integration and switch the repository on. Every future GitHub release then gets its own archived DOI automatically.

## After publishing

- Put the DOI in `README.md` (the badge and the BibTeX), `CITATION.cff`, and the proposal footer. I'll do this if you send me the DOI.
- The DOI link is what goes in the LessWrong post, the Show HN post, and the notes to researchers.


## Version 1.2 (results)

1. On the published record, choose **New version**. Zenodo copies the metadata.
2. Delete the old PDF from the new version's files, upload `proposal/tiered-peer-critique-proposal.pdf` (v1.2).
3. Reserve the DOI for the new version and send it; the PDF footer, README, and CITATION.cff get it, then replace the file once more.
4. Set Version to 1.2, publication date to the day you publish, and update the description's last sentence: "Version 1.2 adds the results of the preregistered pilot: on 64 checkable tasks neither test was passed at this sample size; every answered item was right in every condition, and the conditions separated only on whether an answer arrived at all."
5. Publish. The concept DOI on the record always resolves to the latest version; the v1.1 DOI keeps resolving to v1.1.
6. On GitHub, create release `v1.2` with the new PDF attached.

## Version 1.3 (second pilot), October 2026

Done October 17, 2026, by the same route as 1.2: New version on the 1.2 record, PDF swapped, DOI reserved (10.5281/zenodo.23444219) and put into the paper, README and CITATION.cff before publishing, Version 1.3, publication date the day of publishing, the description's last paragraph extended for the second pilot, the additional description updated. Zenodo's GitHub integration was switched on for the repository the same day, so the `v1.3` GitHub release is archived automatically with a software DOI of its own; the paper record above is the one to cite.
