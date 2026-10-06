# Organizer questions — draft, not sent

Prepared October 3, 2026, America/Chicago. This task has not contacted organizers or accepted dataset terms. Reference documents: [challenge brief](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf) and [public dataset card](https://huggingface.co/datasets/mmbu/mmbu-public). Snapshot hashes and unresolved positions are recorded in `configs/protocol-register.json`.

Hello MMBU organizers,

We are preparing our Medical Domain Adaptation entry. Could you confirm the authoritative harness commit and prompt/schema version, and clarify these points?

1. Which task-output format and malformed-output policy govern final scoring where the brief and public card differ? Please provide representative valid and invalid outputs.
2. How are multi-label segmentation-derived answers graded? How should counting and region tasks be routed and aggregated?
3. Please provide the context-pass implementation: requested-field selection, annotation masking, unknown/missing values and examples with zero annotated fields. Is its state fully independent of the task pass?
4. For detection, which displayed image dimensions determine pixel coordinates after resizing, and how are multiple or absent targets matched? Please confirm the maximum-pairwise-IoU rule and supply fixtures.
5. Which public-development uses are allowed: local scoring, checkpoint selection, hyperparameter selection and error analysis? We will keep official examples and derivatives out of training unless you explicitly authorize otherwise. Does the technical split named `train` have any bearing on permitted use?
6. May independent training splits of MMBU-contributing datasets be used, and is there an approved exclusion/disclosure procedure that does not reveal hidden examples?
7. Please confirm runtime hardware/memory, image-resolution and token limits, generation/thinking settings, precision, dependencies, and requirements for declared base versus submitted checkpoint. How should an already medically adapted initialization or changed vision components be disclosed?
8. Are externally generated training rationales/questions permitted with disclosure? Please also confirm the submission route, final cutoff, public checkpoint requirements and any updates to the published evaluation rules.

Thank you.

The corresponding pending decisions are PROTO-01 through PROTO-06 and the runtime items in the register. An answer should be archived with date and source, then linked to the exact contract revision it resolves. Silence is not approval; no document silently overrides another.
