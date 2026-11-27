# Slice Report: 2026-11-27-smm-lowram-decoder-and-fast-queue

## What was done
1. Fixed `512 MB RAM` OOM & `>540s` timeouts on `1080p` clips (`Job #10` *Breaking Bad*) by placing `-threads 1` BEFORE `-i input_path` so FFmpeg's H.264 decoder stops spawning 8–32 multi-core frame buffers (`scraper/smm_clipper.py`).
2. Switched `0.35s` poster cover overlay to `-loop 1 -t 0.35` + `overlay=0:0:eof_action=pass` (bypassing overlay compositing after `0.35s`) and moved `eq=contrast=1.06:saturation=1.12` onto `[fg]` (`3.2x` fewer pixels).
3. Added `compute_worker_sleep_seconds()` in `scraper/smm_worker.py` (`10s` sleep instead of `180s` when actively rendering queued clips) + TDD tests in `backend/tests/test_smm_clipper.py` and `backend/tests/test_smm_worker.py`.

## Changed files
- `scraper/smm_clipper.py` - Place `-threads 1` before `-i`, move `eq` to `[fg]`, and use `eof_action=pass`.
- `scraper/smm_worker.py` - Add `compute_worker_sleep_seconds` (`10s` fast-chain on active queue).
- `backend/tests/test_smm_clipper.py`, `backend/tests/test_smm_worker.py` - TDD tests for decoder threads and worker sleep.
- `STATE.md` - Update live status and check output.

## check output
```text
ruff check & ruff check --select F821: All checks passed!
pytest test_smm_clipper + test_smm_scene_scorer + test_smm_pipeline_and_telegram_pub + test_smm_worker + test_catalog_worker: 78 passed in 30.19s
pytest test_smm_api.py: 10 passed in 2.58s
pytest bot/tests/: 116 passed in 6.95s
```

## Risks and unknowns
- Render `0.1 vCPU` starter plan remains slower than paid multi-vCPU plans for `1080p` inputs (`~3-5` min/clip), though OOM kills and `180s` idle waits between queued jobs are eliminated.

## Concept to explain to the user
- Input Decoder Thread Placement (`-threads 1` BEFORE `-i`) & Overlay `eof_action=pass` Short-Circuit.

## Next step
- Push fix to `main`, re-queue `#10` (*Mashaqqatlar sari*) alongside `#19` (*Yigitlar*), and verify `#13` (*Taxtlar oʻyini*), `#10`, and `#19` outputs.
