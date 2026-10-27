# ChestMNIST label-blind patient split design

## Objective

Create one immutable scientific-role allocation before any ChestMNIST label vector or pixel is opened. The allocation
must use only the NIH-published patient-disjoint development population and must leave the complete NIH test population
untouched.

## Binding policy

- Input population: exactly 86,524 official NIH train/validation images from exactly 28,008 patients.
- Excluded population: exactly 25,596 official NIH test images from exactly 2,797 disjoint patients.
- Adaptive development: exactly 2,801 patients.
- Training: the remaining 25,207 patients.
- Ranking: SHA-256 over a fixed domain, fixed namespace, and eight-digit patient ID; lowest 2,801 hashes enter adaptive
  development. Patient ID breaks the cryptographically negligible hash-tie case.
- The CLI exposes no seed, ratio, count, label, or class-balancing option.

The output remains a non-admission artifact. It does not open labels or pixels, approve rights, authorize model use, or
turn absent report-mined labels into verified negatives.

## Verification

Tests require exact population counts, patient disjointness, deterministic byte identity, exact role counts, a sealed
receipt bound to both NIH lists and the role CSV, one-time output publication, and rejection of changed or overlapping
populations.
