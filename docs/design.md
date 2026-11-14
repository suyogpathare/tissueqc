# TissueQC design document

<!--
TEMPLATE. To be written by Suyog Pathare. The prompts under each heading
are reminders of what the section should answer; replace them with your
own text. The code's current behaviour is described in each metric's
docstring — where this document and the code disagree, this document is
the specification and the code gets changed.
-->

Author: Suyog Pathare
Status: draft
Last updated: YYYY-MM-DD

## 1. Purpose

<!-- What problem does TissueQC solve, for whom, and at what point in a
workflow (after acquisition, before analysis, run-to-run monitoring)?
What decisions should its output inform, and which should it not? -->

## 2. Scope and inputs

<!-- Supported modalities (Xenium Protein morphology images, CODEX/
PhenoCycler, cyclic IF, mIF), file formats, bit depths, single image vs.
whole slide. What is explicitly out of scope for v0.1? -->

## 3. Metric definitions

<!-- For each metric: the exact formula, the biological/technical
question it answers, inputs, parameter defaults and why, units, and what
counts as undefined. -->

### 3.1 Tissue mask

<!-- Thresholding method, per-channel vs. consensus mask, manual override,
handling of constant or sparse channels. -->

### 3.2 Saturation fraction

<!-- Saturation value (container vs. detector depth), whole image vs.
tissue-only, pixel vs. object level. -->

### 3.3 Signal-to-background (descriptive)

<!-- Signal statistic (mean/median), background definition (non-tissue
pixels vs. control image), why "descriptive", what it does not measure. -->

### 3.4 Tile-based uniformity

<!-- Tile size (pixels vs. microns), tissue-tile cut-off, CV estimator,
separating technical non-uniformity from biological heterogeneity. -->

### 3.5 Reproducibility manifest

<!-- What is recorded and why; what would be needed to reproduce a
result exactly. -->

## 4. Validation plan

<!-- Datasets (public only: source, accession, license), ground truth or
reference for each metric, known-answer synthetic tests, perturbation
experiments, acceptance criteria, how external users will test it. -->

### 4.1 Datasets

| Dataset | Source / accession | License | Used to validate |
|---|---|---|---|
|  |  |  |  |

### 4.2 Experiments

<!-- One subsection per experiment: question, data, procedure, expected
result, pass/fail criterion. -->

## 5. Limitations

<!-- Known failure modes, assumptions, and where the metrics should not be
trusted. -->

## 6. Related tools and how TissueQC differs

<!-- For each: what it does, its input type, what it measures, and what
TissueQC adds or does differently. Cite each tool. -->

### 6.1 CyLinter

### 6.2 HistoQC

### 6.3 TissUUmaps StainV&QC

### 6.4 PathProfiler

### 6.5 Summary table

| Tool | Modality | Level (pixel / cell / slide) | Main QC outputs | Key difference from TissueQC |
|---|---|---|---|---|
| CyLinter |  |  |  |  |
| HistoQC |  |  |  |  |
| TissUUmaps StainV&QC |  |  |  |  |
| PathProfiler |  |  |  |  |

## 7. Open design decisions

<!-- Decisions not yet made. Seeded from the v0.1 code: -->

- [ ] Per-channel vs. consensus (e.g. nuclear-channel) tissue mask
- [ ] Which pixels of a control image define background (whole field vs. its own mask)
- [ ] Tile size in pixels vs. microns (requires pixel size from OME metadata)
- [ ] Mean vs. median as the signal statistic
- [ ] Default saturation value when detector depth < container depth

## 8. Changelog

| Version | Date | Change |
|---|---|---|
| 0.1.0.dev0 | 2026-11-13 | Scaffold and draft metrics |
