## 1. Contract And Tests

- [x] 1.1 Add OpenSpec spec deltas for wrapper-only command and finalizer-owned publish state.
- [x] 1.2 Add unit test rejecting prompt-heavy managed-runtime commands.
- [x] 1.3 Add unit test rejecting forged `COMPLETE` manifest when `target-state.json=FAIL`.
- [x] 1.4 Add unit test rejecting stale latest marker.

## 2. Runtime Implementation

- [x] 2.1 Add `validate-target-publish-state.py`.
- [x] 2.2 Add finalizer-owned manifest seal fields.
- [x] 2.3 Extend generated runtime validation to require wrapper-only commands and publish state doctor availability.
- [x] 2.4 Ensure packaged plugin includes the new validator.

## 3. Documentation And Verification

- [x] 3.1 Update HighLevel/LowLevel/README/templates with wrapper-only and finalizer-owned publish semantics.
- [x] 3.2 Run targeted unit tests.
- [x] 3.3 Run `validate-workflow.py`.
- [x] 3.4 Rebuild plugin payload.
- [x] 3.5 Migrate FreeSTRIDE through Claude Code and verify wrapper/runtime/spec alignment.
