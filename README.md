# A Tiered Peer-Critique Architecture for AI Answers

**Nothing picks a model. Nothing assigns the work. The hub never writes.**

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22357227.svg)](https://doi.org/10.5281/zenodo.22357227)  v1.1: [10.5281/zenodo.22325883](https://doi.org/10.5281/zenodo.22325883)

A working draft proposing what should happen *after* a panel of AI models is convened: the answer has to earn its release. Version 1.2 adds the results of the preregistered pilot. The current models from every major lab, grouped into class-matched tiers, decompose a request, bid on its parts, critique each other's drafts under seat anonymity with evidence required, and revise until they agree. A dedicated hub that never writes an answer interrogates the result within a question budget and enforces verifiable checks. Nothing ships until the panel agrees, the hub has no open questions, and every check passes. A persistent, version-stamped catalogue records who was challenged, corrected, and later shown wrong, and feeds the hub's questions.

The paper positions the design against AI safety via debate, multi-agent debate, mixture-of-agents, LLM-as-a-judge, and model routing; states what it does not claim; and specifies a compute-matched pilot on checkable tasks that could falsify it.

## What's here

| Path | What it is |
| --- | --- |
| `proposal/tiered-peer-critique-proposal.pdf` | The paper (working draft v1.2). Same content as the HTML. |
| `proposal/tiered-peer-critique-proposal.html` | Single-file, styled, printable version of the paper. |
| `prototype/peer-critique-panel.html` | A single-file browser prototype of the six-step protocol: decompose, bid, critique, revise, interrogate, release. Includes a single-model baseline on the same request and a persistent catalogue. |
| `pilot/` | The compute-matched evaluation described in the paper: 64 original checkable tasks, five conditions, every model call, and the report. See `pilot/README.md` and `pilot/results/report.md`. |

## Running the prototype

Open `prototype/peer-critique-panel.html` in a browser. It has two modes:

- **Live panel through OpenRouter.** Paste your own OpenRouter key, pick a tier, and the seats are filled with models from several labs. The hub is a separate model that only asks questions. This is the mode that exercises the design as written.
- **Simulation.** One model (Claude Sonnet 4.6) sits in several seats, each with a different lens, plus a hub that only asks. This mode only works when the file is hosted inside Claude's artifact viewer, where the API key is supplied by the environment.

Nothing leaves your browser except the calls to the model API you chose. The catalogue is stored locally.

## Status

Working draft v1.2, September 2026. The pilot has been run (September 5, 2026, about $34 of model calls). In one line: on 64 checkable tasks, every answered item was right in every condition, so neither preregistered test was passed at this sample size (panel minus compute-matched single model +3.1 points, interval [0, +7.8]; hub minus no hub, 0.0); what separated the conditions was whether an answer came back at all: the single frontier endpoint declined 8 of 20 coding prompts at both temperatures, twelve samples reduced that to 2, and the four-lab panel answered all 64. Full numbers and the readout are in `pilot/results/report.md`; the paper's *Pilot results* section says what they do and do not show. Comments, objections, and pointers to prior work I have missed are welcome as GitHub Issues.

Pilot 2, on a harder 240-task set, has been run (October 14 to 17, 2026, on a local machine, about $171 of model calls). In one line: on the 104 tasks that at least one mid-class seat missed alone (plus 30 none missed), the four-lab panel with the hub scored 96/104, without the hub 97/104, and a second hub pass that read the catalogue 93/104, against 101/104 for the frontier model alone (Claude Opus 5, one pass) and 98/104 for the best seat alone (DeepSeek V4 Pro); panel with hub minus panel without hub is -1.0 points [-7.7, +5.8], so the hub test was not passed, the compute-matched single-model test was not run, and the second hub pass minus the frontier model is -7.7 points with an interval that excludes zero. The hub sent back about 90% of right answers; over the two hub runs it repaired 4 wrong answers and turned 8 right ones wrong (two of those by losing the answer's format line). Full numbers are in `pilot/results2/report.md`; `pilot/README.md` ("Pilot 2, second attempt") records the runs, the harness fixes made along the way, and the one answer-key correction. Working draft v1.3 of the paper, with these results, is being written.

## Cite

```bibtex
@misc{peer_critique_2026,
  author       = {Lott, George W.},
  title        = {A Tiered Peer-Critique Architecture for AI Answers},
  year         = {2026},
  month        = {September},
  note         = {Working draft v1.2},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.22357227},
  url          = {https://doi.org/10.5281/zenodo.22357227}
}
```

A `CITATION.cff` file is included, so GitHub's "Cite this repository" button works once the DOI is filled in.

## License

The paper (everything under `proposal/`) is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The code (everything under `prototype/` and `pilot/`) is licensed MIT; see `LICENSE`.

## Acknowledgment

Drafted with Claude (Anthropic). The design, the decisions, and the mistakes are George W. Lott's.
