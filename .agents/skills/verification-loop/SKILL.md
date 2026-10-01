---
name: verification-loop
description: Use after meaningful code or configuration changes and before claiming completion. Verify only with checks that actually exist and are relevant to the project.
metadata:
  origin: adapted-from-ECC
---

# Verification Loop

## Core Rule
Never report work as complete based only on code generation.

Never say a build, test, lint, type check, hardware test, benchmark, or deployment passed unless it was actually executed and the result was observed.

Keep these states distinct:
- IMPLEMENTED
- STATICALLY CHECKED
- AUTOMATED-TESTED
- INTEGRATION-VERIFIED
- HARDWARE-VERIFIED
- NOT VERIFIED

## Verification Sequence

### 1. Scope and diff
Inspect changed files and the final Git diff.

### 2. Build / compile
Run the repository-defined build or compile step if one exists.

### 3. Static checks
Run existing relevant type, lint, format-check, or static-analysis commands when available.

### 4. Automated tests
Run the smallest relevant test set first, then broader tests when appropriate.

### 5. Integration verification
When components interact, verify the relevant end-to-end path if the environment permits.

### 6. Hardware verification
For hardware-dependent behavior, define expected behavior, test conditions, and pass/fail criteria.
If hardware is unavailable, mark NOT HARDWARE-VERIFIED rather than assuming success.

### 7. Security sanity check
For credentials, user input, network services, external APIs, file access, auth, or sensitive data:
- no hardcoded/committed secrets
- validate trust-boundary inputs appropriately
- do not expose secrets in logs
- avoid unnecessary permissions

### 8. Final diff review
Confirm:
- requested behavior is addressed
- no unrelated changes remain
- temporary debug code is removed
- docs match actual behavior

## Completion Report
For non-trivial tasks report:
- Implemented
- Verified
- Not verified
- Docs updated
- Git branch/commit/push status
