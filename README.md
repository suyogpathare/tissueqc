# TissueQC

Quantitative quality control for multiplex fluorescence tissue images.

> **Status: v0.1 pre-alpha.** The metrics below are first drafts. Their
> definitions and validation are being written up in
> [`docs/design.md`](docs/design.md); do not use the numbers for
> decisions yet.

Scientific design, metric definitions and validation by Suyog Pathare.

## What it measures (v0.1, per channel)

| Metric | One-line definition | Where |
|---|---|---|
| Tissue mask | `pixel > t`, with `t` from Otsu or set by hand | `src/tissueqc/metrics/mask.py` |
| Saturation fraction | share of pixels at or above the saturation value | `src/tissueqc/metrics/saturation.py` |
| Signal-to-background (descriptive) | mean(tissue) / median(non-tissue), or / median(control image) | `src/tissueqc/metrics/sbr.py` |
| Tile uniformity CV | CV of per-tile tissue means, tissue tiles only, with valid-tile count | `src/tissueqc/metrics/uniformity.py` |
| Reproducibility manifest | SHA-256, dimensions, bit depth, software versions, parameters, timestamp | `src/tissueqc/manifest.py` |

Each function's docstring gives its formula, inputs and known limitations.
When a metric is undefined (no tissue, zero background, too few tiles) it is
reported as `null` with a `status` explaining why — never as 0 or infinity.

## Install (development)

```bash
uv venv --python 3.12 .venv
uv pip install -e ".[dev]"
```

macOS note: if `tissueqc` later fails with `No module named 'tissueqc'`,
macOS has marked the install's `.pth` file hidden and Python 3.12 skips
hidden `.pth` files. Fix with `chflags -R nohidden .venv`.

## Use

```bash
.venv/bin/tissueqc image.ome.tif -o image.qc.json
```

Useful options: `--threshold 0=500` (manual mask threshold for channel 0;
repeatable), `--saturation-value 4095` (for 12-bit data stored as 16-bit),
`--tile-size 256`, `--background-image control.tif`,
`--channel-names DAPI,CD3,CD8`. Run `tissueqc --help` for all of them.

## Tests

```bash
.venv/bin/pytest
```

Tests use synthetic images from `src/tissueqc/synthetic.py` whose correct
answers can be worked out by hand, plus edge cases: blank, fully saturated,
zero background, no tissue, single- and multi-channel, 8- and 16-bit.

## Data policy

Only publicly released data is used for development and validation (for
example, 10x Genomics public Xenium datasets and the Image Data Resource,
IDR), cited with their source and license. No proprietary or
employer-internal data. Image files are git-ignored and never committed.

## License

MIT — see [LICENSE](LICENSE).
