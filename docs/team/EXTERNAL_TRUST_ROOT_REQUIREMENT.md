# External trust-root requirement

**Current state:** executable primitive implemented; production binding and external material remain blocked

This contract defines the missing authority boundary for Stage A and BUSI-WHU. It does not supply a signer, public key,
signature, approval, or identity; repository records are not a trust anchor. An actor who can manufacture a credential,
registry, authorization, or attestation can also manufacture its content digest. Hash chaining establishes internal byte
integrity only.

## Executable primitive and remaining boundary

`mmbu_phase1.external_trust.verify_external_authority` now implements the cryptographic core without a repository
default: exact canonical policy and revocation records, independently supplied SHA-256 pins for policy/key/revocation
and verifier bytes, Ed25519 detached-signature verification through that pinned verifier, namespace/principal/role and
signing-time binding, active-revocation checks, verifier stability revalidation, and a private immutable capability.
Negative tests reject key replacement, namespace replay, and revoked keys.

This primitive is not yet wired into Stage A, BUSI-WHU opening/review, source admission, or confirmation. No real
policy, key, pin, signature, time authority, or revocation feed has been supplied. Therefore existing repository
records still grant no external authority, and no protected opening or decision-bearing action is enabled by this
implementation alone.

## Required external inputs

Before any future protected biomedical opening or decision-bearing admission, the execution controller must supply all
of the following through a channel outside the repository and outside the record array being validated:

1. An out-of-band pinned public-key fingerprint and the exact public verification key whose fingerprint matches it.
2. A unique signer principal and role, selected before the protected subject exists.
3. A detached signature over the exact canonical subject bytes and a fixed namespace separating acquisition,
   protected opening, completed review, source admission, and confirmation authorization.
4. A trusted-time statement or independently verifiable signing timestamp that precedes the protected action and is
   within the signer's credential validity interval.
5. A revocation snapshot, obtained independently of the repository, proving the key and credential were active at the
   signing time.

The public key, principal, role, namespace, time source, and revocation source must be bound by one externally
administered policy. Supplying a new key beside its own signature is self-authorization and must reject.

## Signed subjects

The minimum signed subjects are:

- **Stage A:** the exact acquisition/opening authorization, source identities and versions, artifact URLs and hashes,
  permitted structural reads, attempt ceiling, destination root, and explicit prohibitions.
- **BUSI-WHU opening:** the sealed opening authorization digest plus its complete artifact, credential, inventory,
  selection, fingerprint, lock, and output-root bindings.
- **Completed review:** the immutable base-report digest, every participant role and identity, all source-assessment
  digests, the disposition, limitations, and authentication cutoff time.
- **Source admission and confirmation:** the exact admitted-source portfolio, split roles, candidate revisions,
  endpoints, thresholds, seeds, attempt policy, and confirmation-opening boundary.

A signature for one namespace or subject cannot authorize another. Any changed byte requires a new externally signed
subject; predecessor signatures remain immutable evidence and cannot be rewritten.

## Verification order

The production verifier must, before protected access:

1. Load the public-key policy from its independently provisioned location and compare its fingerprint with the
   out-of-band pin.
2. Recompute the canonical subject bytes from the closed record rather than trusting a supplied subject digest.
3. Verify the detached signature, signer principal, role, namespace, and timestamp with a reviewed cryptographic
   verifier.
4. Resolve the independent revocation snapshot and reject unknown, expired, revoked, duplicated, or ambiguous keys.
5. Bind the verified signature evidence into the one-shot capability and reverify it at every later decision boundary.
6. Persist the verifier identity, version, policy fingerprint, key fingerprint, subject digest, signature digest,
   verification time, and outcome without storing private key material.

There is no fallback to caller-provided names, digest-shaped strings, a repository-local key created in the same run,
manual prose, or an unsigned `approved` field. Missing verification tools, policy, pin, key, signature, trusted time, or
revocation state must fail before payload access and consume no authority.

## Required negative tests before implementation can be enabled

- attacker generates a new key and signs a self-created authorization;
- valid signature is replayed under a different namespace, role, source, or subject;
- record digest is correct but canonical subject bytes differ;
- signature, policy, key, or revocation snapshot is replaced after validation;
- signer is expired or revoked at signing time, or timestamp is absent/future/backdated;
- one person occupies incompatible independent roles;
- Stage A statement text is copied into a different packet;
- BUSI-WHU review is internally consistent but lacks external signature evidence;
- confirmation reconstructs the record chain but not the external verification chain;
- verifier executable or policy bytes differ from their independently pinned identity.

## Promotion boundary

Until real external keys, roles, policies, signatures, timestamps, and revocation evidence are independently provided
and the verified capability is bound and reverified at every production decision boundary, all existing Stage A and
BUSI-WHU identity claims remain self-authenticated repository evidence. They may support engineering traceability but
cannot grant biomedical payload opening, source admission, model use, training, checkpoint promotion, release, upload,
or submission authority.
