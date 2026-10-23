# Provisional source–factor incidence audit

**Date:** October 17, 2026  
**Evidence class:** public-metadata stress test only  
**Decision:** the currently prioritized sources cannot identify the full MOSAIC mechanism, even under optimistic candidate capabilities

## Scope and non-claims

This audit asks whether the proposed source portfolio could, in principle, separate MOSAIC's claimed modality,
specimen/scale, and task-geometry factors. It does not admit a dataset, inspect an archive, assign a training split, or
open an MMBU example. Candidate capabilities below are taken from the primary-source metadata summarized in the
[source portfolio](DATA_SOURCE_PORTFOLIO.md) and [metadata receipt](DATA_SOURCE_METADATA_RECEIPT.md). An optimistic
capability is not an approved task atom.

The result is deliberately harsher than asking whether a one-hot matrix can be made full rank. A source can make the
arithmetic rank look adequate while still letting the model recognize the dataset rather than the intended semantic
factor.

## Family-collapsing rules

1. `MedMNIST+` is a wrapper, not a source family. Each selected subset must resolve to its upstream dataset, grouping
   unit, and lineage before it contributes a row.
2. BBBC038 and BBBC039 are one conservative family until their overlap and upstream contributors are reconciled.
3. ROCOv2 and PMC-VQA are one conservative PMC-literature family where their PMCIDs overlap.
4. Multiple task views derived from one image, mask, or report remain one independent unit and one source family.
5. A mask-derived box adds a task view, not a new annotation authority or independent source.
6. A generic object label such as `nucleus` is not semantic region-conditioned medical recognition.

## Optimistic structural scaffold

The table intentionally grants every capability that the current metadata makes plausible. `Candidate` means the atom
still requires admission; `conditional` also depends on access, rights, or an unresolved join.

| Conservative family | Modality | Specimen/scale | Global recognition | Region-conditioned recognition | Coordinate localization | Structural limitation |
|---|---|---|---:|---:|---:|---|
| BUS-BRA | ultrasound | breast / tissue | Candidate | Candidate | Candidate | Modality and anatomy are identical to BUS-UCLM; task views share records |
| BUS-UCLM | ultrasound | breast / tissue | Candidate | Candidate | Candidate | Adds independent-family replication, not a modality–anatomy crossing |
| BUSI-WHU | ultrasound | breast / tissue | Candidate | Unknown | Conditional | Same structural cell; image–mask–patient join unresolved |
| selected MedMNIST upstream families | mixed, subset-specific | mixed, subset-specific | Candidate | No | No | Breadth exists only on the global-task face; wrapper membership is not independence |
| BBBC038/039 | fluorescence microscopy | nuclei / cellular | No meaningful semantic class | No | Candidate | Microscopy, cellular scale, BBBC family, and spatial task remain coupled |
| VinDr-CXR | radiography | chest / organ | Conditional | Conditional | Conditional | Credentialed source; one family carries most radiography spatial support |
| ROCOv2/PMC-VQA | mixed literature figures | mixed / often unresolved | Conditional | Unknown | No authoritative spatial atom | Item rights and semantic taxonomy are unresolved; mixed figures do not create clean factor levels |

## Rank stress test

Before real intake, an optimistic categorical scaffold was constructed using:

- BUS-BRA and BUS-UCLM at ultrasound × breast for all three candidate task geometries;
- one hypothetical admitted MedMNIST upstream microscopy family at microscopy × cellular × global;
- one hypothetical admitted MedMNIST upstream radiography family at radiography × chest × global;
- BBBC at microscopy × cellular × localization; and
- VinDr-CXR at radiography × chest for all three conditional task geometries.

With an intercept and reference-coded main effects for three modality levels, three specimen levels, and three task
levels, the matrix has **7 columns but rank 5**. The two missing degrees of freedom arise because modality and
specimen are perfectly paired in this scaffold: ultrasound↔breast, microscopy↔cellular, and radiography↔chest.

Adding reference-coded source-family effects makes the optimistic matrix **12 columns with rank 8**. This second result
is illustrative rather than a G-1 measurement, because the real upstream MedMNIST families and task atoms are not yet
frozen. It shows why the original three-axis rank check was too weak: source identity can absorb the apparent factor
effect.

Neither result can improve by adding more images to the same cells. It changes only when independently grouped sources
create genuine crossovers.

## Alias findings

| Finding | Severity | Consequence |
|---|---|---|
| Modality and specimen/scale are one-to-one in the cleanest proposed cells | Fatal for a three-factor mechanism claim | A learned “modality” residual cannot be distinguished from anatomy/scale |
| Global-task breadth and spatial-task breadth come from different source families | Fatal for task-factor attribution | A spatial residual can be a BBBC/VinDr/BUS source detector |
| BUS-BRA and BUS-UCLM repeat one joint cell | Useful but insufficient | They test replication and source robustness, not compositional factor reuse |
| MedMNIST subsets can be miscounted as independent sources | High | Wrapper-level splitting would manufacture support and leak upstream lineage |
| Derived views share one annotation and independent unit | High | Counting them as separate evidence exaggerates cell size and task independence |
| A single confirmation family is not enough if training factors are already aliased | High | Confirmation can reveal failure but cannot identify which claimed factor failed |

## Minimum acquisition frontier

MOSAIC's broad three-axis claim should remain blocked until the admitted table contains, at minimum:

1. one modality observed across at least two distinct specimen/scale levels in at least two independent families;
2. one specimen/scale level observed in at least two modalities in at least two independent families;
3. each claimed task geometry observed in at least two modalities and two independent families;
4. at least one non-global task cell outside ultrasound/breast and one global semantic cell outside its spatial source
   family;
5. at least two independent source families supporting every factor level used in a held-out combination;
6. a connected factor-support graph after any single development source family is removed; and
7. full column rank for the preregistered factor model **after source-family fixed effects are included**, not merely
   for the three semantic axes alone.

Useful target cells are therefore crossover cells, not more same-cell volume. Examples include the same anatomy under
two imaging modalities, one modality spanning different anatomies, and semantic global plus spatial supervision in
independent microscopy and radiology families. These are acquisition targets, not permission to relabel a convenient
dataset after inspection.

## Claim ladder

| Highest support achieved | Permitted claim |
|---|---|
| Same source, multiple derived task views | Multi-task engineering only |
| Same joint factor cell, multiple independent sources | Source-robust replication |
| Full semantic-axis rank but source-adjusted rank deficient | Predictive factor labels; no mechanism attribution |
| Source-adjusted rank and leave-one-family-out support pass | Eligible to test compositional factor reuse |
| Held-out combinations beat B2/B4 and adverse controls on untouched families | Evidence for the preregistered MOSAIC mechanism |

## Gate disposition

MOSAIC G-1 is now **provisionally failed at the portfolio-structure level**, not merely `not evaluated`. The exact
admitted-data gate remains `not evaluated` because there are zero admitted sources, but the current optimistic scaffold
already contains a fatal modality–specimen alias. The correct next move is one of:

- acquire admissible crossover sources that satisfy the minimum frontier;
- narrow MOSAIC to a two-axis or source-robust multi-task hypothesis before results are opened; or
- retain MOSAIC as an engineering ablation and keep B2 as the competition lane.

No score rises from this audit. It prevents an invalid experiment from consuming GPU time and makes the next data
search falsifiable.
