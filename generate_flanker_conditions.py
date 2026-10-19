"""
generate_flanker_conditions.py

Generates 4 PsychoPy conditions files for the Flanker task:
    flanker_cond_blockA_normal.xlsx
    flanker_cond_blockB_color.xlsx
    flanker_cond_blockC_position.xlsx
    flanker_cond_blockD_interaction.xlsx

Each file has 124 rows = 124 trials, with the following columns:
    trialNum     1..124
    congruency   'congruent' or 'incongruent'
    targetDir    'left' or 'right'
    correctAns   'z' (for left) or 'm' (for right)
    arrow1..5    the 5 arrow characters that make up the array
    color1..5    per-arrow color, hex string (e.g. '#FF8800')
                 white ('#FFFFFF') in Normal and Position blocks
    arrayX       x-coordinate of the array center (PsychoPy height units)
    arrayY       y-coordinate of the array center (PsychoPy height units)
                 0 in Normal and Color blocks
    fixDur       fixation duration in seconds (jittered 0.5 to 1.0)

Trial counts within each block:
    62 congruent + 62 incongruent
    31 left + 31 right within each congruency level (4 cells of 31)
    In Position and Interaction blocks: 62 trials up + 62 down

USAGE
-----
The simplest way: open a Command Prompt, cd into the folder containing
this script, and run:

    python generate_flanker_conditions.py

Optional flags:
    --subject 001       tag filenames with subject ID and use it as seed
    --seed 42           set the random seed explicitly (reproducible output)
    --outdir conditions write files into a subfolder called 'conditions'
"""

import argparse
import colorsys
import hashlib
import random
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Constants you can tweak
# ---------------------------------------------------------------------------
N_TRIALS = 124
N_ARROWS = 5
CENTER_IDX = 2  # 0-indexed center of the 5-arrow array

# Position ranges (PsychoPy 'height' units, where +0.5 = top, -0.5 = bottom)
X_RANGE = (-0.25, 0.25)
Y_UP_RANGE = (0.15, 0.35)
Y_DOWN_RANGE = (-0.35, -0.15)

# Color sampling in HSV space (high S and V means vivid, not black, not white)
SAT_RANGE = (0.7, 1.0)
VAL_RANGE = (0.7, 1.0)

# Fixation jitter range, in seconds
FIX_DUR_RANGE = (0.5, 1.0)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def make_arrow_array(target_dir, congruency):
    """Return a list of 5 single-character strings (e.g. ['<','<','>','<','<'])."""
    center = '<' if target_dir == 'left' else '>'
    if congruency == 'congruent':
        flanker = center
    else:
        flanker = '>' if center == '<' else '<'
    arrows = [flanker] * N_ARROWS
    arrows[CENTER_IDX] = center
    return arrows


def random_color_hex(rng):
    """Sample a vivid random color in HSV, return as a hex string like '#A38C12'.
    
    Black and white are excluded by the HSV ranges (S and V both above 0.7).
    """
    h = rng.random()                     # hue: 0.0 to 1.0
    s = rng.uniform(*SAT_RANGE)          # saturation
    v = rng.uniform(*VAL_RANGE)          # value (brightness)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return '#{:02X}{:02X}{:02X}'.format(int(r * 255), int(g * 255), int(b * 255))


def build_trial_list(rng):
    """Build a list of 124 (congruency, target_dir) tuples, balanced and shuffled.
    
    Returns 4 cells x 31 trials each:
      congruent-left, congruent-right, incongruent-left, incongruent-right
    """
    trials = []
    for cong in ('congruent', 'incongruent'):
        for direction in ('left', 'right'):
            trials.extend([(cong, direction)] * 31)
    rng.shuffle(trials)
    return trials


def assign_positions(rng):
    """Return 124 (x, y) tuples: 62 up + 62 down, x jittered, then shuffled."""
    positions = []
    for _ in range(62):
        positions.append((rng.uniform(*X_RANGE), rng.uniform(*Y_UP_RANGE)))
    for _ in range(62):
        positions.append((rng.uniform(*X_RANGE), rng.uniform(*Y_DOWN_RANGE)))
    rng.shuffle(positions)
    return positions


def build_block(block_kind, rng):
    """Build a list of 124 row dicts (each = one trial) for one block.
    
    block_kind: one of 'normal', 'color', 'position', 'interaction'
    """
    trials = build_trial_list(rng)
    
    needs_color = block_kind in ('color', 'interaction')
    needs_position = block_kind in ('position', 'interaction')
    
    if needs_position:
        positions = assign_positions(rng)
    else:
        positions = [(0.0, 0.0)] * N_TRIALS
    
    rows = []
    for i, (cong, direction) in enumerate(trials):
        arrows = make_arrow_array(direction, cong)
        if needs_color:
            colors = [random_color_hex(rng) for _ in range(N_ARROWS)]
        else:
            colors = ['#FFFFFF'] * N_ARROWS
        x, y = positions[i]
        fix_dur = rng.uniform(*FIX_DUR_RANGE)
        
        row = {
            'trialNum': i + 1,
            'congruency': cong,
            'targetDir': direction,
            'correctAns': 'z' if direction == 'left' else 'm',
        }
        for j in range(N_ARROWS):
            row[f'arrow{j + 1}'] = arrows[j]
        for j in range(N_ARROWS):
            row[f'color{j + 1}'] = colors[j]
        row['arrayX'] = round(x, 4)
        row['arrayY'] = round(y, 4)
        row['fixDur'] = round(fix_dur, 3)
        rows.append(row)
    
    return rows


def pick_seed(args):
    """Decide what random seed to use based on command-line arguments."""
    if args.seed is not None:
        return args.seed
    if args.subject is not None:
        # Convert subject ID to a stable integer seed
        try:
            return int(args.subject)
        except ValueError:
            # Non-numeric subject ID: hash it
            return int(hashlib.md5(args.subject.encode()).hexdigest(), 16) % (2**31)
    return None  # truly random


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='Generate Flanker conditions .xlsx files.')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility. Omit for fully random.')
    parser.add_argument('--subject', type=str, default=None,
                        help='Subject ID. Used as seed and appended to filenames.')
    parser.add_argument('--outdir', type=str, default='.',
                        help='Output directory (default: current folder).')
    args = parser.parse_args()
    
    seed = pick_seed(args)
    rng = random.Random(seed)
    
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    subj_tag = f'_subj{args.subject}' if args.subject else ''
    
    blocks = [
        ('A_normal', 'normal'),
        ('B_color', 'color'),
        ('C_position', 'position'),
        ('D_interaction', 'interaction'),
    ]
    
    print(f'Random seed: {seed}')
    print(f'Output directory: {outdir.resolve()}')
    print()
    
    for label, kind in blocks:
        rows = build_block(kind, rng)
        df = pd.DataFrame(rows)
        filename = f'flanker_cond_block{label}{subj_tag}.xlsx'
        path = outdir / filename
        df.to_excel(path, index=False)
        
        # Sanity-check printout
        n_cong = sum(1 for r in rows if r['congruency'] == 'congruent')
        n_left = sum(1 for r in rows if r['targetDir'] == 'left')
        n_up = sum(1 for r in rows if r['arrayY'] > 0)
        n_down = sum(1 for r in rows if r['arrayY'] < 0)
        print(f'  {filename}')
        print(f'    {len(df)} trials | '
              f'congruent={n_cong}, incongruent={len(df) - n_cong} | '
              f'left={n_left}, right={len(df) - n_left} | '
              f'up={n_up}, down={n_down}')
    
    print()
    print('Done.')


if __name__ == '__main__':
    main()
