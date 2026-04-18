---
description: Run integration tests and enforce the slice gate. Pass a slice number to filter (e.g. /test-slice 4).
allowed_tools: ["Bash"]
---

Run the full integration test suite and report results.

If the argument $ARGUMENTS contains a slice number (e.g. "4" or "Slice 4"), filter tests for that slice only:

```bash
./gradlew test --tests "*Slice$ARGUMENTS*" --continue 2>&1
```

If no argument was given, run all tests:

```bash
./gradlew test --continue 2>&1
```

After running:
- If all tests pass: report "Gate cleared — all tests pass. Ready for next slice." and show the test count summary.
- If any tests fail: list each failing test class and method with the failure message. **Stop. Do not write any more code. Do not proceed to the next slice.** Wait for the user to fix the failures and run `/test-slice` again.
