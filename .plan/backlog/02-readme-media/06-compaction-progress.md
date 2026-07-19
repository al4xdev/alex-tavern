# Capture 06: Compaction progress

**README placeholder (`README.md:388`):**

```text
<place_6:screenshot of the compact-session button with its progress bar mid-animation>
```

## What to capture

- Use a session with more than `compaction_keep_recent_turns` distinct turns so the backend
  performs a real compaction instead of returning “nothing to compact.”
- Click the compact-session control.
- Capture while the simulated fill is visibly between 0% and 90%, before the API response
  completes.
- Keep the compact button and enough neighboring action controls visible to establish where
  the feature lives.

## Deliverable

- Preferred output: `docs/media/readme/06-compaction-progress.webp`.
- Replace the literal `<place_6:...>` line in `README.md`.

## Done when

- The compact control is identifiable and its partially filled progress layer is visible.
- The surrounding text must not imply that the progress percentage is measured backend
  progress; the README explicitly documents it as simulated.
