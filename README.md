# Flanker Conditions Generator

A Python script that auto-generates the PsychoPy conditions files for a four-block Flanker task, replacing manual spreadsheet setup. I wrote it as a research assistant in the Jonides Lab (University of Michigan).

**No participant data is included in this repository.** The files in `example_output/` are synthetic trial lists generated with `--seed 42`.

## What it does

The script writes one `.xlsx` conditions file per block, 124 trials each:

| Block | Arrow colors | Array position |
|---|---|---|
| A – Normal | white | screen center |
| B – Color | random vivid color per arrow | screen center |
| C – Position | white | randomized, upper or lower half |
| D – Interaction | random vivid color per arrow | randomized, upper or lower half |

Within every block:

- **Congruency × target direction is fully balanced**: 4 cells (congruent/incongruent × left/right) of 31 trials each, shuffled.
- **Position blocks** have exactly 62 upper-half and 62 lower-half trials, with horizontal jitter.
- **Colors** are sampled in HSV space with saturation and value ≥ 0.7, so stimuli stay vivid and never fall near black or white.
- **Fixation duration** is jittered uniformly between 0.5 and 1.0 seconds.
- **Response keys** are mapped automatically (`z` = left, `m` = right).

## Reproducibility

A single seeded random generator drives every random choice, so the same seed always produces the same files.

- `--seed 42` sets the seed explicitly.
- `--subject 001` uses the participant ID as the seed (non-numeric IDs are hashed) and tags the filenames, giving each participant a unique but reproducible trial order.
- With neither flag, output is fully random.

After writing each file, the script prints a sanity check of trial counts (congruency, direction, up/down), so an unbalanced file is caught before data collection.

## Usage

```bash
pip install -r requirements.txt
python generate_flanker_conditions.py --seed 42 --outdir example_output
python generate_flanker_conditions.py --subject 001 --outdir conditions
```

## Output columns

| Column | Description |
|---|---|
| `trialNum` | 1–124 |
| `congruency` | `congruent` or `incongruent` |
| `targetDir` | `left` or `right` (direction of the center arrow) |
| `correctAns` | `z` for left, `m` for right |
| `arrow1`–`arrow5` | the five arrow characters in the array |
| `color1`–`color5` | per-arrow hex color (`#FFFFFF` in Normal and Position blocks) |
| `arrayX`, `arrayY` | array center in PsychoPy height units (0 in Normal and Color blocks) |
| `fixDur` | fixation duration in seconds |

Example rows from Block D (`--seed 42`):

| trialNum | congruency | targetDir | correctAns | arrows | arrayX | arrayY | fixDur |
|---:|---|---|---|---|---:|---:|---:|
| 1 | incongruent | left | z | `> > < > >` | 0.0357 | -0.1534 | 0.780 |
| 2 | congruent | right | m | `> > > > >` | 0.0525 | -0.3321 | 0.790 |
| 3 | incongruent | right | m | `< < > < <` | -0.1763 | -0.1601 | 0.931 |

## Design note

Up/down position is balanced within each block (62/62) but is not crossed with the congruency × direction cells, because 31 trials per cell cannot be split evenly in half. A fully crossed design would need 32 trials per cell (128 per block); changing the per-cell count is the only edit required.
