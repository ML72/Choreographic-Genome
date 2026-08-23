# The Choreographic Genome: Amplifying the Silent Structure of Text into Dance

This codebase implements the choreographic genome: an instrument that maps the raw UTF-8 bytes of a text onto a learned vocabulary of 256 motion regions, quantized from the AIST++ dance dataset, and realizes the resulting sequence as full-body movement through motion matching. It amplifies how a text is built rather than what it means.

## Setup

Follow these steps to set up the environment and prepare the data:

1. **Set up the Python Environment:**
   Set up your environment with Python 3.12. If you are using Conda, it's recommended to create a new environment:
   ```bash
   conda create -n dance_identity python=3.12
   conda activate dance_identity
   ```

2. **Install Dependencies:**
   Install all required packages from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare the Data and Models:**
   - Ensure your AIST++ dataset is located inside the `data/motions/` folder. This step should already be done, just confirm that `data/motions/` is populated.
   - Download the SMPL models (Male, Female, and Neutral) from the [official SMPL website](https://smpl.is.tue.mpg.de/) and place them inside the `models/smpl/` folder. Ensure the following 6 files are present in the directory so the scripts can properly load all genders and metadata:
     - `SMPL_FEMALE.npz`
     - `SMPL_FEMALE.pkl`
     - `SMPL_MALE.npz`
     - `SMPL_MALE.pkl`
     - `SMPL_NEUTRAL.npz`
     - `SMPL_NEUTRAL.pkl`

4. **Create the Motion Index:**
   Create the index of moves by running:
   ```bash
   python create_index.py
   ```

5. **Create the Motion Codebook:**
   Create the discretized feature codebook by running:
   ```bash
   python create_codebook.py
   ```

   Region ids are assigned by ranking the K-Means centroids along the first principal component, so that nearby byte values name kinematically nearby gestures (see [Indexing and Codebook Creation](#indexing-and-codebook-creation)). Pass `--region_order raw` to keep the arbitrary K-Means labels instead.

   To build a vocabulary from only part of the corpus, pass `--file_prefix`. AIST++ encodes genre in the file name, so this quantizes a genre-specific instrument (frames outside the subset are left unassigned and are invisible to the engine):
   ```bash
   python create_codebook.py --file_prefix gJB --output_path data/index/codebook_gJB.npz
   ```

6. **Create the Plausibilities Graph:**
   Create the graph of transition plausibilities by running:
   ```bash
   python create_plausibilities.py
   ```

   An alternate codebook needs its own graph; point the script at both paths:
   ```bash
   python create_plausibilities.py --input_codebook data/index/codebook_gJB.npz --output_path data/index/plausibility_graph_gJB.pkl
   ```

## Generating Dance Routines

Once your setup is complete and the index is created, you can generate new dance samples in three modes:

**Mode A (Autonomous Exploration):**
Generate a random sequence of a given length:
```bash
python generate_sample.py --num_frames 1000
```

**Mode B (Guided Generation):**
Guide generation through specific codebook regions using a DNA sequence (a comma-separated string of region IDs):
```bash
python generate_sample.py --input_dna "114, 12, 125, 140, 57"
```

**Mode C (Text Guided Generation):**
Guide generation using a string of text. The text is trimmed and converted into bytes, which directly map to codebook regions:
```bash
python generate_sample.py --input_text "I love dance"
```

All modes support an optional `--gender` argument (`neutral`, `male`, or `female`) to change the body model used during rendering. For example:
```bash
python generate_sample.py --input_text "I love dance" --gender female
```

Each run is saved to `results/samples/<run_name>/` and produces three files:
- `dance_moves.pkl`, the generated pose sequence
- `dance_visualization.mp4`, a rendered video
- `run_data.json`, a log of the exact regions executed and any bridges inserted

To inspect the vocabulary itself rather than a generated dance, `python debug_codebook.py` renders sample frames from a handful of codebook regions to `results/codebook/`, which is a quick way to see what a region actually looks like.

## Evaluating Pipeline Metrics

`run_analysis.py` reproduces every figure and every reported number for this project.

```bash
# Run all analysis regimes (this may take a while depending on hardware)
python run_analysis.py

# Run a specific subset for debugging/iteration
# There are 7 parts total, split by data collection needs
python run_analysis.py --part 1
```

The script is organized into seven parts. Passing `--part N` runs only that part; omitting `--part` runs all seven in order. Metrics are written as text logs under `results/metrics/` and charts are exported to `results/plots/`.

One caveat on exact reproduction: the codebook and plausibility graph behind the reported numbers were re-indexed retroactively, when the region ordering was introduced, rather than rebuilt from scratch. Building them fresh draws a slightly different sample of the same estimator, so a clean run should land on very similar results, differing only in the last decimal places.

1. **Stylistic & Art-Side Evaluation**: stylistic uniqueness across the autonomous and text-guided modes: choreographic n-gram novelty, sequence edit distance, and kinetic signatures. Writes `results/metrics/part_1.txt` and `results/plots/plot_1` through `plot_3`.
2. **Structural Graph Traversability**: plausibility-graph density plus Dijkstra pathfinding reachability and bridge statistics. Writes `results/metrics/part_2.txt` and `results/plots/plot_4_bridge_density.png`.
3. **System Polish & Quality Assurance**: physical-correctness metrics (floor penetration, foot skating, jerk) comparing the original dataset against the autonomous mode with and without physics. Writes `results/metrics/part_3.txt`.
4. **Artistic Case Studies**: maps a small, deliberately heterogeneous corpus of texts through the byte->codebook->choreography pipeline, visualizes the "choreographic genome" each text produces, and measures how many motion regions the body traverses per source character. Because the engine starts from a randomly chosen frame, that count varies slightly between runs, so each text is generated `CASE_REPEATS` times (40 by default) and the reported amplification is the mean; set it to 1 for a quick look. The graph's prediction of how many bridges each byte pair would need is logged alongside as a diagnostic and normally exceeds what the engine actually inserts, since the engine searches every frame of a region before falling back to the graph. Writes `results/metrics/case_studies.txt` (+ `.json`), `results/plots/plot_5_choreographic_genome.png`, and `plot_6_amplification.png`.
5. **Rendered Choreography Montages**: renders the physicalized choreography for the same corpus: a wide "seven texts, seven bodies" teaser, a time-sampled montage of a contrasting trio (a sonnet, an error log, an Indigenous script), and chronophotographic long-exposure trails comparing three texts. Uses pyrender, so it takes a few minutes. Writes `results/plots/plot_7_dance_montage.png`, `plot_8_teaser.png`, `plot_9_trail.png`.
6. **Instrument Ablations**: asks how much of the result is owed to choices the instrument makes rather than to the text. Scores four ways of assigning byte values to regions (arbitrary K-Means labels, the PC1 ranking that is used, a spectral layout, and a greedy nearest-neighbor walk); sweeps the number of regions to see how well 256 partitions the motion space; and measures genome distinctness over the whole held-out text corpus rather than the seven case studies. Writes `results/metrics/ablations.txt` (+ `.json`) and `results/plots/plot_10_ablations.png`.
7. **Vocabulary Ablation**: holds the byte->region operator fixed and swaps the movement vocabulary, dancing the same texts with a codebook quantized from a single AIST++ genre. Requires the alternate codebook and graph from the setup steps above; skips itself with instructions if they are missing. Writes `results/metrics/vocabulary_ablation.txt` (+ `.json`) and `results/plots/plot_11_vocabulary.png`.

The curated case-study corpus and the byte->region mapping used by Parts 4 through 7 live in `run_analysis.py` (`CASE_STUDIES` for Part 4, `CORPUS` for Parts 5 and 7); edit those to amplify your own texts. Part 7's `VOCABULARIES` list controls which codebooks are compared. Parts 1 and 6 additionally read the held-out text corpus in `data/eval_text/` (15 files of lyrics, poems, and quotes, 570 non-empty lines), which is what the novelty and genome-distinctness numbers are measured over.

Note that evaluation can be slow. Parts 1-3 collect large motion datasets and take roughly an hour on a consumer-level CPU. Part 4 takes about fifteen minutes because it repeats each text (see `CASE_REPEATS`), and Parts 5 through 7 run in a few minutes each.

## Webapp

This repository contains code for a website about this project. All website code is in the `webapp` folder. To interact with the website code, switch into the `webapp` directory:

```bash
cd webapp
```

Read `webapp/README.md` for instructions on how to set up and run the website locally.

The figures on the site are copies of the generated plots, so refresh them after re-running the analysis:

```bash
cp results/plots/plot_{5,6,8,9,11}_*.png results/plots/plot_7_dance_montage.png webapp/public/
```

## How This Works

### Indexing and Codebook Creation

To build the searchable database of motions, the system first creates a unified index mapping all valid frames (`create_index.py`). Then, it processes these frames into abstract stylistic tokens (`create_codebook.py`):
1. **Feature Extraction:** It reconstructs 3D representations using the SMPL body model and extracts local behavior features (joint poses, root and joint velocities, and binary foot contacts) while stripping world-space placement and heading, so that global position does not skew kinematic comparisons. This yields 278 features per frame.
2. **Temporal Windowing:** A sliding window captures chunks of movement (default 20 frames) representing the "stylistic future" of each frame, giving a 5560-dimensional motion signature.
3. **Dimensionality Reduction and Quantization:** The high-dimensional temporal features are compressed into a 64D space using PCA, and subsequently assigned discrete region values (0 to 255) using K-Means clustering.
4. **Region ordering:** K-Means returns clusters in an arbitrary order, so on its own region 65 bears no kinematic relation to region 66. Since the text-guided mode maps byte value `b` straight onto region `b`, that arbitrariness would silently decide the character of every generated dance: the fact that ASCII lays the lowercase alphabet out contiguously, or that UTF-8 keeps its continuation bytes in `0x80`-`0xBF`, would say nothing at all about the resulting movement. The centroids are therefore ranked along the first principal component (axis 0 of the PCA basis they live in) and relabelled by that rank, so region id is a position on a real kinematic axis. This is a pure permutation: it re-indexes the vocabulary without changing the clustering. Measured as the rank correlation between the distance separating two byte values and the distance separating the gestures they name, arbitrary labels score -0.01 and the PC1 ranking scores +0.41.

**Output:**
- The combined motion index is saved to `data/index/motion_index.npz`, containing the concatenated SMPL `poses` and `trans` for all dataset frames, along with `file_indices` and `frame_indices` to map each frame back to its original source file and local frame number.
- The codebook is saved to `data/index/codebook.npz`. Every valid frame receives an integer token `0-255` reflecting its motion behavior cluster. The file also records `region_order` (the permutation from region id back to the original K-Means label) and `ordering` (`pc1` or `raw`), so the labeling is reproducible and reversible. The final `W-1` (default 19) frames of any isolated clip are marked with a token of `-1`, signifying that they lack sufficient future frames to construct a full behavioral window. The downstream engine ignores these `-1` frames as selectable transitional targets.

### Plausibility Graph Construction

The plausibility graph is generated using `create_plausibilities.py`. This graph encodes the physical plausibility of transitions between codebook regions. Each node represents a codebook region, and edges are weighted by the cost of transitioning between regions based on motion continuity metrics. This graph is critical for ensuring smooth transitions during guided generation (Modes B and C) and is saved as `data/index/plausibility_graph.pkl`. Building it compares every ordered pair of regions, so it takes roughly 15 minutes on a consumer CPU.

### Sample Generation

The sample generation step (`generate_sample.py`) operates in three modes using motion matching and an offline plausibility graph:

* **Mode A (Autonomous Exploration):** The engine starts at a random valid frame and plays the motion. To maintain temporal consistency, it locks playback for a minimum of 30 frames. After this period, it searches the entire database to find the lowest-cost transition to a new sequence, continuously creating a novel, unbounded dance routine.
* **Mode B (Guided Generation):** The engine follows a user-provided "DNA" target sequence, represented as a list of codebook regions. It seamlessly transitions to the requested regions. If a direct transition to the next requested region is physically implausible within the search window, the system performs a safe jump and uses Dijkstra's algorithm on the precomputed plausibility graph (`create_plausibilities.py`) to inject bridge regions, dynamically routing the choreography back to the user's intended DNA sequence.
* **Mode C (Text Guided Generation):** The engine follows a target sequence generated by trimming the provided text and converting it into a string of bytes. Each byte perfectly maps to a 0-255 codebook region, providing a new way to interactively guide choreography through words.

In all modes, the final output includes a 3D rendered video, raw pose data, and a `run_data.json` file logging the exact sequence of regions executed.

`generate_motion()` accepts a few arguments that matter for batch callers:

* `codebook_path` / `graph_path` select an alternate vocabulary (see the genre-restricted build above); everything else is unchanged.
* `save_outputs=False` skips the per-run `.pkl` and `.json` artifacts, which dominates runtime when generating hundreds of samples.
* The motion index and its derived motion-matching features are loaded once per process by `load_engine()` and memoized per artifact path, so repeated calls in one process do not reload the multi-GB index. The returned arrays are shared and must be treated as read-only.

### Motion Smoothing and Physics

Motion matching alone leaves a visible seam at every jump, so each generated sequence is post-processed (`util/motion.py`):

1. **Transition blending:** Across each jump, the outgoing and incoming poses are cross-faded with quaternion SLERP under Ken Perlin's smootherstep easing, which is C2 continuous and so introduces no velocity or acceleration discontinuity.
2. **Filtering:** A Savitzky-Golay filter (window 31, order 3) runs over the pose and translation tracks, removing residual high-frequency jitter without flattening the choreography.
3. **Contact correction:** `physics_contact_fix` treats low-velocity foot frames as ground contacts and applies a smoothly interpolated height and horizontal correction, so planted feet stay planted.

Part 3 of `run_analysis.py` measures what this buys: foot skating drops from 0.121 to 0.010 and mean jerk from 1.2e-2 to 8.9e-4.
