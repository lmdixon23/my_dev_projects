# AI Playgrounds — Interactive Visualizations for Intro-to-AI

Twelve single-file HTML+JavaScript applets that let students *drag a slider and
watch a core AI idea play out*. No build step, no install, no backend — each
applet is one HTML file you can open locally or host on GitHub Pages.

The applets were authored as a companion to the
**Introduction to Artificial Intelligence** course (Mixed High School, 2025–2026,
Haidian Kaiwen Academy) and map 1-to-1 to the curriculum's most
visually-rich units, with extra depth on the under-served Russell & Norvig topics
(logical agents, knowledge bases, Bayesian networks, local search). They're free for any classroom to use.

> **Live demo:** https://lmdixon23.github.io/my_dev_projects/

## The twelve applets

| Unit | Concept | Applet | "Aha" moment |
|---|---|---|---|
| U2 | Problem representation & search | [Pathfinding](playgrounds/search-pathfinding/) | Why A* explores fewer nodes than BFS |
| U2 | Logical agent (AIMA Ch 7) | [Wumpus World](playgrounds/wumpus-world/) | The difference between "I haven't seen it" and "I've proved it's not there" |
| U2 | Logic & knowledge bases | [CNF & SAT Builder](playgrounds/cnf-sat/) | Why every SAT solver in the world wants CNF as input |
| U3 | Probability & Naïve Bayes | [Bayes classifier](playgrounds/bayes-classifier/) | Why a 99%-accurate test for a rare disease still misleads |
| U3 | Bayesian networks (AIMA Ch 14) | [Bayes network](playgrounds/bayes-network/) | Why learning of an earthquake LOWERS your belief in a burglary |
| U4 | KNN classifier | [K-Nearest Neighbors](playgrounds/knn-classifier/) | What `k` does to a decision boundary |
| U5 | Evaluation, leakage, regularization | [Overfitting](playgrounds/overfitting/) | Why a perfect training fit can fail on test data |
| U5 | Local search (AIMA Ch 4) | [Hill climbing & SA](playgrounds/hill-climbing/) | Why sometimes you have to take a worse step |
| U6 | Neural network fundamentals | [Tiny neural net](playgrounds/neural-network/) | How layers + non-linearity carve up space |
| U7 | Unsupervised learning | [K-means clustering](playgrounds/kmeans/) | What "iterating to convergence" looks like |
| U8 | Vision with CNNs | [Convolution playground](playgrounds/convolution/) | Why a 3×3 matrix can detect edges |
| U10 | Reinforcement learning | [Q-learning gridworld](playgrounds/q-learning-gridworld/) | How a value function emerges from random walking |

## Design principles

Every applet follows the same template so students who use one know how to use them all:

1. **One screen, no menus.** Sliders / buttons on one side, live visualization on the other.
2. **Default state already shows the punchline.** Open the page → the visualization is already mid-demo. No setup before learning begins.
3. **Tooltips on every control.** Hovering a slider explains what it does and which units cover it.
4. **Reset is one click.** Students can experiment without fear.
5. **No build step.** Every applet is a single `index.html` with inline `<script>` and `<style>`. Open in a browser, done.
6. **Mostly offline.** Eleven of the twelve applets are fully self-contained and work with no network. The one exception is the Bayesian-network applet, which loads D3 from cdnjs at runtime (`bayes-network/index.html`) and will not render its graph if that CDN is blocked — inlining D3 or adding a `typeof d3` guard is tracked in Future Enhancements.

## Deploying

### Option A — GitHub Pages (how the live demo runs)

These applets live in [`my_dev_projects/ai_playgrounds`](https://github.com/lmdixon23/my_dev_projects/tree/main/ai_playgrounds). A small workflow (`.github/workflows/pages.yml`) publishes this directory to GitHub Pages on every push to `main` that touches it — that's what serves the live demo linked above.

To host your own copy, drop this folder into any repository and either point Pages at it (Settings → Pages) or reuse the same Actions workflow.

### Option B — open locally

Double-click `index.html`. Everything works from a `file://` URL.

### Option C — embed individual applets

Each applet is fully self-contained. Paste any `playgrounds/*/index.html` into a
school LMS as an HTML widget and it runs in isolation, with no dependency on the
landing page or sibling applets.

## Educational notes

Each applet has a **For teachers** section at the bottom of its page covering:

- Curriculum unit number and learning objectives addressed
- A 3-question pre-discussion prompt to use before students touch the applet
- A 3-question post-exploration prompt to use after
- Common misconceptions the applet was designed to defeat

## Pedagogy: why these twelve?

The 12-unit IAI curriculum has units that are inherently visual (search trees,
decision boundaries, clusters, value functions) and units that are
discussion-driven (ethics, society). Interactive applets pay off most where:

1. The concept involves **continuous parameters** a slider can sweep (k in KNN, polynomial degree, learning rate).
2. The concept involves a **dynamic process** a play button can animate (search expansion, k-means iterations, Q-learning convergence).
3. The concept produces an **immediate visual contradiction** to a naive expectation (overfitting curve looking great in-sample, terrible out-of-sample).

Units 1, 9, 11, and 12 fail one or more of those criteria, so they get
discussion guides instead of applets (those guides live in the IAI course repo,
not here). U2 gets **three applets**, and U3 and U5 get **two each**, because
Russell & Norvig–style content (logical agents, knowledge bases, Bayesian
networks, local search) is under-served by existing interactive tools on the web.

## License

MIT — see `LICENSE`. Free to use, fork, modify, deploy, and remix for any classroom.

## Contact

Built by Logan Dixon for the 2025–2026 Intro to AI course at Haidian Kaiwen Academy.
File issues at <https://github.com/lmdixon23/my_dev_projects/issues>.

## Scope

- **Educational accuracy ≠ research accuracy.** These are intuition-builders, not
  reference implementations. For example, the CNN applet uses hand-picked filters
  rather than learned ones, and the convolution demo has no backprop through the
  kernels — it shows what convolution *does*, not how a network learns it. Each
  applet has a "What this simplifies" note at the bottom.
- **Browser-only compute.** All applets run in pure JavaScript with no GPU
  acceleration. Anything heavier than ~10⁴ operations per frame will stutter on
  Chromebooks.
- **Bilingual UI is complete.** All twelve applets ship a full English/中文 `STRINGS` table and a language toggle. (An earlier draft of this section wrongly called this partial; every applet has a parallel `zh:` block.)

## Future Enhancements

Framed as teaching extensions: each item exposes a variable the current applet holds fixed. These are deliberately scoped to gaps that are *not* already built — the applets already ship rich control sets (e.g. the search demo covers BFS / DFS / A\* / Dijkstra / bidirectional / IDA\* with four heuristics and weighted terrain; the neural-net already has activation/optimizer selectors **and** per-neuron activation heatmaps; k-means already has k-means++/inertia/silhouette).

- **CNF & SAT — CDCL trace mode.** The applet already animates DPLL with unit propagation; the page text notes real solvers add conflict-driven clause learning and watched literals. A CDCL view would show *why* modern solvers outrun plain DPLL. (Verified absent from the code.)
- **Convolution — one learned kernel.** Add a "learn this filter" mode that runs gradient descent on a single 3×3 kernel toward a target feature map, turning the hand-picked-filter demo into a one-step CNN-training demo (and closing the simplification flagged in Scope). (Verified absent.)
- **k-Nearest Neighbors — regression mode.** A toggle to predict a continuous value (mean of the k neighbors) alongside classification, so students see kNN is not inherently a classifier. (Verified absent.)
- **Pathfinding — side-by-side race.** Run two algorithms on the same maze with live nodes-expanded counters, making "A\* explores fewer nodes than BFS" a measured result rather than a sequential impression. (The existing bidirectional mode runs two frontiers of *one* algorithm, not two algorithms.)
- **Hill climbing & SA — success-rate benchmark.** Run N random restarts per algorithm on the same problem and tabulate success rate and mean cost, turning the eight-algorithm menu into a comparison rather than a sequence of anecdotes. (Verified absent.)
- **Bayes-network — remove the D3 CDN dependency.** Inline D3 or add a `typeof d3` guard so the one non-offline applet matches the others' offline guarantee.
