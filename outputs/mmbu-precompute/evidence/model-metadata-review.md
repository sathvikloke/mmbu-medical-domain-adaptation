# Independent model metadata and archive review

Verdict: **PASS** for the saved metadata/configuration and historical archive evidence. No consequential mismatch found. This reviewer did not author the model preflight, registry, retrieval receipts, or model-preflight prose; this review changed only this report.

The three API SHA-256 values match the registry, API revision hashes match both registry and preflight, and reported parameter totals equal the sum of reported dtype counts. I independently recomputed BF16 × 2 bytes plus F32 × 4 bytes, divided by 2^30, and checked all three displayed GiB values. The architecture, model type, stored Transformers version, and processor type agree with the pinned local config files.

There are exactly eight saved successful config files and one recorded failed request. Every successful file matches its retrieval byte count and SHA-256; every retrieval URL, including the failed request URL, pins the registered model revision. The only failure is the Qwen3.5 generation_config.json HTTP 404, and no substitute local generation config exists. This is verification of the saved receipt, not an independent network replay of that historical response.

The documentation distinguishes Hugging Face-reported checkpoint metadata from independently enumerated parameters and runtime memory. It makes no active-parameter, GPU-fit, training-memory, native-loader, or export-verification claim. `transformers_version` is explicitly serialization provenance, not a verified dependency minimum. The current working model order is labeled provisional. Qwen3.5 has 24 linear and 8 full attention layers in a repeated three-linear/one-full pattern; its empty deep-stack index list differs from Qwen3-VL's [8,16,24]. The document's broad alternating/interleaved-attention wording is supported by that pattern, and does not specify a one-to-one cadence.

The original mmbu-precompute.zip remains byte-for-byte consistent with the older MMBU-precompute-verification.json: matching recorded size and SHA-256, with a successful ZIP CRC test. Its older 114-test receipt describes that historical package; it is not evidence for newly added batch-2 files.

Limits: no checkpoint tensors were downloaded or independently counted here. Saved config/API consistency cannot establish runtime compatibility, active counts, actual allocation, performance, or official eligibility. Retrieval authenticity is bounded by the saved URLs and receipts; no network fetch was made.

The checks ran with a standard-library Python script from the package root and exited 0. The script recomputed raw hashes, byte counts and dtype arithmetic directly, parsed all saved JSON, compared URL revision paths, examined attention/vision fields, and checked the historical ZIP without extraction. Detailed receipt follows.

```json
{
  "verdict": "PASS",
  "recorded_at_utc": "2026-10-04T05:16:16.705341+00:00",
  "scope": "Local saved metadata/config/archive verification only; no network, no checkpoint tensors, no runtime inference",
  "models": [
    {
      "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
      "revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
      "api_sha256": "cb108c6563113bd4644d14fac967427fb6d1921ff5ad2085ec47f25e307a9573",
      "total_parameters": 8292166656,
      "dtype_counts": {
        "BF16": 8292166656
      },
      "recomputed_tensor_bytes": 16584333312,
      "recomputed_tensor_gib_exact_decimal": "15.4453639984130859375",
      "display_gib": "15.45",
      "architecture": [
        "Qwen2_5_VLForConditionalGeneration"
      ],
      "image_processor_type": "Qwen2VLImageProcessor"
    },
    {
      "model_id": "Qwen/Qwen3.5-9B",
      "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
      "api_sha256": "b590b5d527c9c6625b892e2a28cd903b77766fe635226a0d89ef9d800b93cdc0",
      "total_parameters": 9653104368,
      "dtype_counts": {
        "BF16": 9653100528,
        "F32": 3840
      },
      "recomputed_tensor_bytes": 19306216416,
      "recomputed_tensor_gib_exact_decimal": "17.9803151786327362060546875",
      "display_gib": "17.98",
      "architecture": [
        "Qwen3_5ForConditionalGeneration"
      ],
      "image_processor_type": "Qwen2VLImageProcessorFast"
    },
    {
      "model_id": "Qwen/Qwen3-VL-8B-Instruct",
      "revision": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
      "api_sha256": "0c3a6afc5c7e9d926890d085e8ab596bb0c9b4acfb33ce877ee5780aa593bc80",
      "total_parameters": 8767123696,
      "dtype_counts": {
        "BF16": 8767123696
      },
      "recomputed_tensor_bytes": 17534247392,
      "recomputed_tensor_gib_exact_decimal": "16.3300404250621795654296875",
      "display_gib": "16.33",
      "architecture": [
        "Qwen3VLForConditionalGeneration"
      ],
      "image_processor_type": "Qwen2VLImageProcessorFast"
    }
  ],
  "retrieval_summary": {
    "successful_files": 8,
    "expected_404": {
      "model_id": "Qwen/Qwen3.5-9B",
      "url": "https://huggingface.co/Qwen/Qwen3.5-9B/resolve/c202236235762e1c871ad0ccb60c8ee5ba337b9a/generation_config.json",
      "ok": false,
      "error": "HTTP Error 404: Not Found"
    },
    "successful_file_checks": [
      {
        "file": "evidence/model-configs/Qwen2.5-VL-7B-Instruct--config.json",
        "bytes": 1374,
        "sha256": "77d9ec7321cc572e3579e2c84799c9cadaded63c49ce93b101733349fc330c43",
        "url_pins_registry_revision": true
      },
      {
        "file": "evidence/model-configs/Qwen2.5-VL-7B-Instruct--preprocessor_config.json",
        "bytes": 350,
        "sha256": "f2058c716eef96ccaed1cc1e2d0c08306b62586d535b28d9d08e691b2fab7ca0",
        "url_pins_registry_revision": true
      },
      {
        "file": "evidence/model-configs/Qwen2.5-VL-7B-Instruct--generation_config.json",
        "bytes": 216,
        "sha256": "0a3aea82869fe29f20dc95ccf3e2bcff380eca1f5ad6447a4a4b37110b08e43e",
        "url_pins_registry_revision": true
      },
      {
        "file": "evidence/model-configs/Qwen3.5-9B--config.json",
        "bytes": 3126,
        "sha256": "d0883072e01861ed0b2d47be3c16c36a8e81c224c7ffaa310c6558fb3f932b05",
        "url_pins_registry_revision": true
      },
      {
        "file": "evidence/model-configs/Qwen3.5-9B--preprocessor_config.json",
        "bytes": 390,
        "sha256": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
        "url_pins_registry_revision": true
      },
      {
        "file": "evidence/model-configs/Qwen3-VL-8B-Instruct--config.json",
        "bytes": 1474,
        "sha256": "5cd452860dc1e9c29dd71cc3cef7f39b338b7a40793f7a260655c2d3568f3661",
        "url_pins_registry_revision": true
      },
      {
        "file": "evidence/model-configs/Qwen3-VL-8B-Instruct--preprocessor_config.json",
        "bytes": 390,
        "sha256": "27225450ac9c6529872ee1924fcb0962ff5634834f817040f444118116f4e516",
        "url_pins_registry_revision": true
      },
      {
        "file": "evidence/model-configs/Qwen3-VL-8B-Instruct--generation_config.json",
        "bytes": 269,
        "sha256": "8469742d1fce0de951c8909b26a2c0c0d8490837ce476efb114da9e0cefc4d44",
        "url_pins_registry_revision": true
      }
    ]
  },
  "config_structure_checks": {
    "qwen35_attention_counts": {
      "linear_attention": 24,
      "full_attention": 8
    },
    "qwen35_attention_pattern": "three linear then one full, repeated eight times",
    "qwen35_deepstack_indexes": [],
    "qwen3vl_deepstack_indexes": [
      8,
      16,
      24
    ]
  },
  "historical_archive": {
    "path": "/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute.zip",
    "bytes": 146013,
    "sha256": "85dd05407f1a64da7e7cb09aea8a032bcd9dfa4f2e6764f217b9fc4b58363f51",
    "matches_saved_receipt": true,
    "zip_crc_check": "PASS",
    "members": 67
  },
  "reviewed_artifact_sha256": {
    "configs/model-registry.json": "bf72bacd517bd614a2af07d8576a4e7d95cbf38acf930096d75edb5e16e43c91",
    "evidence/model-metadata-preflight.json": "392dadb33b3a0204edf5aef298d35fe9e148e5397018bf276242aa331984c520",
    "evidence/model-configs/retrieval.json": "cb1905f35e60cfa94e1fbb8b8880f748e1bb2b86e0080a301f3cf3be20ee5b69",
    "docs/model-preflight.md": "00cad2dd0736038f3e9df1b9adab2ead629a68dd5eb969e7d92f8f0a44993def"
  }
}
```
