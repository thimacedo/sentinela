# Handle Junk Data in Scraping and Classification

This plan addresses the user's request to signal the worker when a scrape returns junk data (UI elements) and to prevent the AI classifier from scoring junk.

## User Review Required

Please review the definitions of "lixo" and the proposed actions when junk is detected. 

## Open Questions

None at this moment.

## Proposed Changes

### `core/ai_service.py`

Update the AI classifier to recognize and handle "lixo" correctly:
- **[MODIFY]** Update `SYSTEM_PROMPT` to add instructions on how to identify UI elements (e.g., "Também da Meta", "Instagram Lite", "Localizações", "Áudio original") and fragment texts, assigning them the category `"LIXO"`.
- **[MODIFY]** Update `_parse_json_response` to check if `categoria_ia == "LIXO"`. If so, force `is_hate = False` and `confianca_ia = 0.0`, ensuring it does not score or pollute analytics.

### `core/instagram_scraper_v2.py`

Implement junk detection during the extraction phase:
- **[MODIFY]** Expand `commentTextBlacklist` to include the specific UI terms identified in logs ("também da meta", "instagram lite", "localizações", etc.).
- **[MODIFY]** Add a local heuristic check `is_junk(text)` inside `_scrape_post` or `scrape_profile`. If the extracted comments for a post contain a high ratio of junk (or if any critical junk patterns are found that indicate we are reading the page footer instead of the comments section), we flag it.
- **[MODIFY]** Add a `junk_detected` metric to `stats`.

### `workers/scrapers/ig_worker_v2.py`

Signal the worker to take action when junk is detected:
- **[MODIFY]** After `self.scraper.scrape_profile`, inspect the scraper stats or the returned comments.
- **[MODIFY]** If a significant amount of junk was detected (e.g., the fallback DOM parser grabbed the footer instead of comments), filter the junk out locally before hitting the database or the AI.
- **[MODIFY]** Return a specific `error="junk_detected"` in `CycleResult` if the scrape was compromised by junk, so the orchestrator knows the DOM extraction missed the target, preventing repeated useless movements.

## Verification Plan

### Automated Tests
- Run `pytest` or `test_scraper_v2.py` to ensure normal comments still extract properly.
- Verify `ai_service.py` returns `confianca_ia = 0.0` when text is classified as "LIXO".

### Manual Verification
- Check worker logs to see if it correctly aborts or filters when encountering "Também da Meta".
