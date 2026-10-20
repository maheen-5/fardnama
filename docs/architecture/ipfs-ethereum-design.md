# ADR-001: Private IPFS storage and Ethereum EvidenceRegistry anchoring

| Field | Value |
|---|---|
| Status | **Proposed — design only (Mid-1).** Implementation is scheduled for Final-1. |
| Owner | Maheen Ahmad (23I-2086) |
| Reviewers | Muhammad Noor Ul Azeem (23I-2118), Zainab Waqas (23I-2097); Supervisor: Ms. Sadia Saad; Co-supervisor: Mr. Mehmood ul Hassan |
| Related | FYP-1 Mid Report §5.2, §5.3, §5.4, §6.7, §8.10; FR3, FR4, FR15–FR17; NFR3, NFR8 |
| Diagrams | `docs/architecture/diagrams/` (Mermaid sources `.mmd` + rendered `.png`) |

---

## 1. Purpose and scope

This record fixes the Mid-1 design for:

- storing encrypted evidence on a **private IPFS** network;
- recording every processing step in a **hash-chained custody log**;
- building a **per-case Merkle tree** over the custody log;
- **anchoring** each case root through the **EvidenceRegistry** Solidity contract on a local Ethereum node.

**In scope:** data placement, hashing and encoding rules, Merkle construction and proofs, IPFS configuration assumptions, encryption and key-management assumptions, the contract interface and access control, deletion and retention behaviour.

**Out of scope at Mid-1:** working code for any of the above (Final-1), classification, RAG, report generation (FYP-2), and the quarterly cross-case checkpoint (proposed future work only, see §11).

## 2. Problem being solved

A victim's evidence must be provably unaltered from the moment it is uploaded. That proof must not depend only on FardNama's own database, because anyone with database access could edit both the evidence record and its stored hash. At the same time the evidence must stay **confidential**: victims are vulnerable people and the evidence often contains private messages and images.

The design therefore needs three separate guarantees. No single component provides all three:

| Property | Provided by |
|---|---|
| **Confidentiality** | AES-256-GCM encryption with a per-case key *before* anything leaves the backend; private IPFS swarm; access-controlled API. |
| **Availability** | Pinning on project-managed IPFS node(s), plus backups of the IPFS datastore and PostgreSQL. |
| **Integrity / tamper-evidence** | SHA-256 hashes, hash-chained custody events, per-case Merkle root, and an append-only on-chain anchor history that the database cannot rewrite. |

## 3. Architecture and data-flow diagrams

| Figure | File | Shows |
|---|---|---|
| A | `diagrams/fig-a-integrity-components.png` | Components of the integrity subsystem and what data flows between them. |
| B | `diagrams/fig-b-anchor-sequence.png` | Sequence: upload → hash → encrypt → IPFS → custody events → Merkle root → `anchor()`. |
| C | `diagrams/fig-c-verify-sequence.png` | Sequence: retrieval and independent verification with `verify()`. |
| D | `diagrams/fig-d-anchor-history.png` | How successive roots for one case are appended, never overwritten. |
| 5.3 (updated) | `diagrams/fig-5-3-component-updated.png` | Report Figure 5.3 with corrected storage and blockchain edges plus a key store. |
| 5.4 (updated) | `diagrams/fig-5-4-class-updated.png` | Report Figure 5.4 with the anchor-history fields on `ChainAnchor`. |
| 5.5 (updated) | `diagrams/fig-5-5-er-updated.png` | Report Figure 5.5 with the anchor-history columns on `CHAIN_ANCHOR`. |

Flow summary (Figure B):

1. The Flutter app sends the file and `case_id` over HTTPS. The backend checks consent.
2. The backend computes `sha256_original` on the raw bytes **before any processing**, derives the working copy and computes `sha256_copy`.
3. Case Crypto encrypts the original, the copy and (later) the OCR text with the case's data key.
4. The Storage client adds each ciphertext to the private IPFS node, pins it and receives the CIDs.
5. The Evidence row (hashes, CIDs, metadata; no content) is written to PostgreSQL.
6. OCR and forensics run on the working copy. Each stage's output hash becomes a custody event.
7. The Integrity Ledger appends custody events, recomputes the case Merkle root and asks the Blockchain Gateway to `anchor(caseCommitment, caseRoot)`.
8. The transaction hash, block number and anchor index are stored in `CHAIN_ANCHOR` and returned in the upload receipt.

## 4. Storage responsibilities

| Component | Data stored | Data that must **not** be stored there |
|---|---|---|
| Flutter app | User interactions and upload requests; the session token while logged in | Long-lived encryption keys embedded in the app; cached plaintext evidence after upload |
| FastAPI backend | Validation and processing logic; plaintext only transiently in memory/tmpfs while a request runs | Unencrypted evidence or OCR text in logs, error messages or temp files left on disk |
| PostgreSQL | Case metadata, `case_salt`, `case_commitment`, SHA-256 hashes, CIDs, custody events, Merkle roots, anchor records (tx hash, block, index), audit log | Raw evidence or plaintext OCR text (designed IPFS-only evidence-storage model); unwrapped keys |
| Key store (separate table/schema) | Per-case data keys **wrapped** by the master key | Unwrapped keys; the master key itself |
| Master key (KEK) | Docker secret file on the VM (`/run/secrets/fardnama_kek`) | Git repository, `.env` files, PostgreSQL, IPFS, CI logs |
| Private IPFS | Encrypted evidence bytes (original, working copy, OCR text) | Plaintext evidence; keys; anything readable without the case key |
| Redis | Short-lived job state and cache entries | Evidence bytes, OCR text or keys |
| Ethereum contract | Case commitment, Merkle root, anchor index, block timestamp | Evidence files, OCR text, victim identity, readable case IDs or case details |
| Backups | Encrypted IPFS datastore snapshot; PostgreSQL dump | Unencrypted copies of anything above |

**Is the custody ledger persisted in PostgreSQL?** Yes. `CUSTODY_EVENT` is the system of record for custody entries. `CASE_MERKLE_TREE` caches the latest root and `CHAIN_ANCHOR` mirrors the on-chain anchor history. PostgreSQL is used because it is queryable. It is **not trusted on its own**: an attacker with write access could rewrite rows *and* recompute the cached root. That is why the on-chain root exists. It is a separate integrity reference that the database cannot edit. It is not a second place where evidence is stored.

**How entries are verified against the commitments** (a periodic audit job and on every retrieval):

1. For each evidence item, recompute every `entry_hash` from its fields and check that each `prev_entry_hash` equals the previous entry (§5).
2. Where the bytes are available, fetch them from IPFS, decrypt them, and check that their SHA-256 equals `output_hash` for the INGEST/COPY/OCR stages.
3. Rebuild the case's leaves in `case_seq` order and recompute the root (§6).
4. Compare the root with `CASE_MERKLE_TREE.case_root` and with the latest `CHAIN_ANCHOR.case_root`.
5. Call `EvidenceRegistry.verify(caseCommitment, root)` and `latest(caseCommitment)` on the chain.
6. Any mismatch raises a tamper alert and writes an `AUDIT_LOG_ENTRY`.

## 5. Hashing and custody-event scheme

Notation: `H` = SHA-256 (32-byte output); `‖` = byte concatenation.

**Per-case values**

- `case_salt` = 32 random bytes from a CSPRNG, generated when the case is created.
- `caseCommitment` = `H(case_id_bytes ‖ case_salt)`, where `case_id_bytes` is the 16-byte UUID. This is the only case identifier that ever appears on-chain.

**Evidence hashes**

- `sha256_original` = `H(raw uploaded bytes)`, computed before any other processing.
- `sha256_copy` = `H(working-copy bytes)`. The original is never analysed or modified.

**Custody chain (one chain per evidence item)**

```
entry_0 = H(0x00…00 (32 bytes) ‖ enc(INGEST) ‖ sha256_original ‖ ts_0)
entry_n = H(entry_{n-1} ‖ enc(stage_n) ‖ output_hash_n ‖ ts_n)
```

- `enc(stage)` = 1-byte length followed by the ASCII stage name, so field boundaries cannot be shifted. Stages: `INGEST`, `COPY`, `STORE`, `OCR`, `FORENSICS`, and later `CLASSIFY`.
- `output_hash` is always 32 bytes: the SHA-256 of the stage output. For STORE this is `H(cid_original ‖ cid_copy)` as UTF-8. For FORENSICS it is the hash of the canonical JSON forensics report.
- `ts` = 8-byte big-endian Unix time in milliseconds, UTC.
- Each event also receives `case_seq`, a strictly increasing integer per case that fixes its leaf position.
- Changing any field of any entry changes that entry's hash and every later hash in the chain.

## 6. Per-case Merkle tree and proof verification

**Leaves:** one leaf per custody event, ordered by `case_seq`:

```
leaf_i = H(0x00 ‖ case_salt ‖ entry_i)          (leaf hash)
node   = H(0x01 ‖ left ‖ right)                 (internal node)
```

The report currently writes `L = H(case_salt ‖ entry)`. The `0x00`/`0x01` prefixes are a refinement that stops a leaf and an internal node from ever being confused. Both inputs would otherwise be exactly 64 bytes. This is listed for approval in §12.

**Construction rules**

- Pair nodes from left to right at each level.
- An **unpaired last node is promoted unchanged** to the next level. It is not duplicated, which avoids the known duplicate-leaf ambiguity.
- One leaf: the root is the leaf. Zero leaves: there is no root and nothing is anchored.
- Cost is O(n) to build and O(log n) for a proof. `n` is the number of events in one case only.

**Proof:** an ordered list of `(sibling_hash, side)` pairs from leaf to root. **Verification** recomputes the root from the leaf and the siblings, then checks that it equals an anchored root via `verify()`.

**Selective disclosure:** to prove one item, the victim shares the item, its custody entry fields, the leaf salt input, the proof, the `caseCommitment`, the root and the transaction hash. The verifier learns nothing about the other leaves except opaque sibling hashes. Leaves in other cases use different salts, so they cannot be linked.

**Roots over time:** the leaf list only grows, so each new root covers all earlier leaves. The **earliest** anchor whose tree contains a leaf proves that the item existed at that anchor's block time. The **latest** anchor shows the case's current state.

## 7. Private IPFS configuration assumptions

- **Node:** one Kubo node in Docker on the Oracle VM, with the image tag pinned in `docker-compose.yml`.
- **Private swarm:** a generated `swarm.key` and `LIBP2P_FORCE_PNET=1`. The node refuses peers without the key.
- **No public discovery:** bootstrap list removed (`ipfs bootstrap rm --all`), `Routing.Type = none`, MDNS disabled. Content is never announced to the public DHT.
- **API and gateway:** the RPC API (port 5001) is reachable only on the internal Docker network and is never published to the internet. No public HTTP gateway.
- **Adding content:** `ipfs add --cid-version=1 --raw-leaves --pin=true` on ciphertext only.
- **CID ≠ SHA-256:** a chunked file's CID is not its plain SHA-256, so both are stored. On retrieval, IPFS checks the CID, the GCM tag checks the ciphertext, and the decrypted bytes are checked against the stored SHA-256.
- **Availability:** pinning keeps content only while the pin and the node's disk exist; it does not guarantee permanent retention. Mid-1 assumes one node, so a scheduled snapshot of the IPFS datastore volume (ciphertext only) is stored separately and restores are tested. A second node or IPFS Cluster replication is deferred.
- **What the private swarm does *not* do:** it limits which nodes can join, but it is not encryption and not authorization. Anyone with access to the node or its disk could read blocks. Confidentiality therefore comes from encryption (§8).

## 8. Encryption and key-management assumptions

- **Data key (DEK):** one random 256-bit key per case. Never shared between cases.
- **Cipher:** AES-256-GCM with a fresh random 96-bit nonce for every encryption; a nonce is never reused under the same key.
- **Associated data (AAD):** `caseCommitment ‖ evidence_id ‖ object_type` (`original` / `copy` / `ocr_text`). A ciphertext moved into another case or slot fails to decrypt.
- **Blob format on IPFS:** `version (1 byte) ‖ nonce (12) ‖ ciphertext ‖ tag (16)`.
- **Key wrapping:** the DEK is wrapped with AES-256-GCM under a master key (KEK). The wrapped DEK is stored in a separate key table, and `CASE.wrapped_key_ref` points to it.
- **Master key (KEK):** supplied to the backend as a Docker secret file. It is never committed, never in the database and never in IPFS. Moving it to a managed KMS or Vault is deferred.
- **Where encryption happens:** on the server. The backend sees plaintext briefly because OCR and forensics need it, so this is **not** end-to-end encryption. Plaintext is processed in memory or tmpfs and is never logged.
- **Flutter app:** holds no long-lived keys.
- **OCR text:** treated as evidence content. It is encrypted and stored on IPFS (`cid_extracted_text`) instead of a plaintext database column (see §12).

## 9. Smart-contract interface and access control

Contract: **EvidenceRegistry**, written in Solidity and tested with Hardhat. Interface (design, not final code):

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IEvidenceRegistry {
    struct Anchor { bytes32 root; uint64 timestamp; uint64 blockNumber; }

    event RootAnchored(
        bytes32 indexed caseCommitment,
        bytes32 indexed caseRoot,
        uint256 index,          // position in this case's history (0, 1, 2, …)
        uint64  timestamp       // block.timestamp
    );

    error NotRegistrar();
    error ZeroValue();
    error RootAlreadyAnchored(uint256 index);

    /// Registrar only. Appends caseRoot to the case's history; never overwrites.
    function anchor(bytes32 caseCommitment, bytes32 caseRoot) external returns (uint256 index);

    /// True if caseRoot was EVER anchored for caseCommitment; also returns where and when.
    function verify(bytes32 caseCommitment, bytes32 caseRoot)
        external view returns (bool anchored, uint256 index, uint64 timestamp);

    function latest(bytes32 caseCommitment)
        external view returns (bytes32 root, uint256 index, uint64 timestamp);

    function anchorCount(bytes32 caseCommitment) external view returns (uint256);
    function anchorAt(bytes32 caseCommitment, uint256 index) external view returns (Anchor memory);
    function registrar() external view returns (address);
}
```

**Storage model for successive roots:**

- `mapping(bytes32 => Anchor[]) history`: one append-only array per case commitment. `anchor()` only ever calls `push`.
- `mapping(bytes32 => mapping(bytes32 => uint256)) rootIndexPlusOne`: O(1) lookup for `verify()`, where 0 means never anchored.
- Every anchor also emits `RootAnchored`. The event log is a second, independent history that the contract cannot edit.

**Rules:**

1. Only the `registrar` address set in the constructor may call `anchor()`. Any other caller reverts with `NotRegistrar`.
2. `caseCommitment` and `caseRoot` must be non-zero.
3. Re-anchoring a root that is already in that case's history reverts. This keeps the history free of duplicates and makes indices meaningful.
4. **No function updates, replaces, or deletes an anchor.** There is no `owner`, no `selfdestruct`, and no upgradeable proxy.
5. Only 32-byte values are stored: no evidence, OCR text, identity or readable case data.

**Verification behaviour:** `verify(c, R)` answers "was R anchored for c, and when?" It returns true for historical roots as well as the latest one. To check the current state, a verifier compares against `latest(c)`. A Merkle proof is valid against any anchored root whose tree already contained that leaf.

**Anchoring cadence:** the root is recomputed after every stage. The proposed design anchors once at the end of each completed pipeline run (one transaction per upload, and one per later FYP-2 stage run). This matches report Figure 4.2. Report §6.7 currently says "anchored after each stage"; one of the two must be aligned (see §12). The contract supports either choice without changes.

**Planned Hardhat tests (Final-1):** `test_registry_only_registrar_can_anchor`, `test_registry_has_no_overwrite`, `test_registry_appends_successive_roots`, `test_registry_rejects_duplicate_root`, `test_registry_verify_historical_root`, `test_registry_emits_RootAnchored`.

## 10. Privacy, deletion and retention

**On-chain privacy:** only `caseCommitment` and roots are public. Every case is anchored from the same registrar address, so there is no per-victim address. Anchor timing still reveals when *some* case was active; this is accepted at Mid-1.

**Retention:** evidence is kept until the victim deletes the case. There is no automatic expiry at Mid-1 (see §12).

**Deletion by crypto-shredding:**

1. Mark the case deleted and write an audit entry.
2. Destroy the wrapped DEK and `case_salt`.
3. Unpin all of the case's CIDs and run `ipfs repo gc`.
4. Delete the case's hashes, CIDs and custody rows from PostgreSQL.
5. The on-chain commitment and roots remain because they cannot be erased. Without the salt they cannot be linked back to the case.

**Limitations of deletion (stated honestly):**

- Copies the victim previously exported, downloaded or sent to anyone (reports, screenshots, shared proofs) are **not** erased.
- Key destruction must also cover **backups**. Database backups contain the wrapped key until they age out, so the case is fully shredded only after the backup-retention window ends (or when backups are re-keyed).
- Unpinning and garbage collection remove blocks from FardNama's own node(s). They cannot reach a copy if a node or disk had been copied earlier.
- On-chain data is permanent by design. Only opaque 32-byte values are kept there for this reason.

## 11. Limitations and deferred implementation work

- **Design only at Mid-1.** Encryption, IPFS storage, the custody chain, anchoring and selective disclosure are implemented in Final-1.
- **The local chain is operator-controlled (risk R2).** Whoever controls the node and registrar key could deploy a fresh chain or append a misleading *new* root. Earlier anchors in the history would still remain. A public testnet (e.g. Sepolia) or external publication of roots removes this trust assumption (deferred).
- **One IPFS node:** no replication yet.
- **Server-side encryption:** not end-to-end.
- **Key management:** KEK as a Docker secret is a Mid-1 assumption. Rotation and KMS/Vault are deferred.
- **Registrar key rotation:** not supported by the immutable-registrar design (redeploy required).
- **Consistency proofs between successive roots:** like RFC 6962, these are deferred. A full rebuild from PostgreSQL is used instead.
- **What hashes prove:** that content was not changed after a given time. They do not prove that the content is true.
- **Quarterly cross-case checkpoint — PROPOSED, NOT IMPLEMENTED.** It would combine the latest root of every case into a super-root each quarter. It is separate from, and must not be confused with, the per-case anchoring described above. No contract function, table or job for it is part of the current design.

## 12. Decisions that need team or supervisor approval

| # | Decision | Recommended option | Impact on report |
|---|---|---|---|
| D1 | Anchoring cadence | Recompute after each stage; anchor once per completed pipeline run | Edit §6.7 sentence "After each stage the case root is recomputed and anchored" |
| D2 | Domain-separated hashing (`0x00` leaf, `0x01` node) | Adopt | Update leaf formula in §6.7 |
| D3 | Salt used in leaves | Keep `case_salt` (simple), or per-leaf salt `HMAC(case_salt, case_seq)` so one disclosure does not reveal the case salt | §6.7 selective disclosure text |
| D4 | OCR text storage | Encrypt and store on IPFS (`cid_extracted_text`) instead of a plaintext `extracted_text` column | Class and ER diagrams (updated versions provided) |
| D5 | Duplicate root for the same case | Reject (`RootAlreadyAnchored`) | §5.3 interface table |
| D6 | Registrar | Immutable address set at deployment | §6.7 |
| D7 | KEK location for Final-1 | Docker secret; KMS/Vault later | §8.10 |
| D8 | Deletion scope | Shred keys and salt, unpin, delete hashes/CIDs/custody rows; keep only a "case deleted at t" audit line | §8.10 privacy measures |
| D9 | Backup retention window | Short and documented (e.g. 30 days) so that shredding completes within a known time | New sentence in §8.10 |
| D10 | Public testnet deployment | Plan for Final-2 as R2 mitigation | §8.9 risk register |
| D11 | Quarterly checkpoint | Keep as proposed future work only | Already marked "proposed" |
