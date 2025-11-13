# Documentation Reorganization Plan

## Current State
- **48 markdown files** scattered in `/Users/e.chan/` root directory
- Existing organized structure in `/Users/e.chan/content-summarizer/docs/`

## Target Structure

```
/Users/e.chan/content-summarizer/docs/
├── setup/                    # Installation & configuration
├── features/                 # Feature documentation
├── user-guide/              # How-to guides & usage
├── api-integration/         # API & integration docs (NEW)
├── development/             # Development & updates
├── troubleshooting/         # Fixes & debugging
├── migration/               # Migration guides
└── archive/                 # Deprecated/old docs
```

## File Categorization

### 📁 setup/ (Installation & Configuration)
- START_HERE.md → **README.md** (main entry point)
- DEEPSEEK_SETUP.md
- FFMPEG_INSTALL.md
- FFMPEG_INSTALLED.md
- FREE_AI_SETUP.md
- OLLAMA_QUICK_GUIDE.md
- SETUP_SLASH_COMMAND.md
- LOCALHOST_READY.md

### 📁 features/ (Feature Documentation)
- DARK_MODE_ADDED.md
- DARK_MODE_HEADER_FIX.md
- DARK_MODE_WHITE_TEXT_FIX.md
- NEW_SEARCH_FEATURE_GUIDE.md
- PODCAST_SUPPORT.md
- SEARCH_FEATURE_COMPLETE.md
- YOUTUBE_TRANSCRIPT_README.md
- AI_SUMMARIZATION_README.md

### 📁 user-guide/ (Usage & How-To)
- STREAMLIT_USAGE_GUIDE.md
- STREAMLIT_UPDATED.md
- LISTEN_NOTES_USAGE_GUIDE.md
- QUICK_START_LISTEN_NOTES.md
- QUICK_START_TADDY.md
- LISTEN_NOTES_QUICK_REF.md
- HOW_TO_GET_PODCAST_ID.md
- GET_PODCAST_ID_GUIDE.md

### 📁 api-integration/ (NEW - API & Integration)
- LISTEN_NOTES_API_FIX.md
- LISTEN_NOTES_MIGRATION.md
- TADDY_API_FIXES.md
- TADDY_IMPLEMENTATION_COMPLETE.md
- TADDY_INTEGRATION.md
- TADDY_SETUP_COMPLETE.md
- TADDY_VS_ALTERNATIVES.md
- FIX_TADDY_CREDENTIALS.md

### 📁 development/ (Development & Updates)
- OLLAMA_UPGRADE_SUMMARY.md
- IMPLEMENTATION_SUMMARY.md
- DEPLOYMENT_COMPLETE.md
- DEPLOYMENT_SUCCESS.md
- SESSION_SUMMARY.md
- MIGRATION_CHECKLIST.md
- DATA_FLOW_VISUAL.md

### 📁 troubleshooting/ (Fixes & Debugging)
- AI_FIXED.md
- BUG_FIX_SUMMARY.md
- FIXES_QUICK_REFERENCE.md
- PODCAST_FIXES_COMPLETE.md
- PERFORMANCE_IMPROVEMENTS_COMPLETE.md
- PERFORMANCE_OPTIMIZATION.md
- PROCESSING_TRACE.md
- RSS_EPISODE_MATCHING_FIX.md
- YOUTUBE_FALLBACK_FIX.md

## Actions Required

1. ✅ Create `/Users/e.chan/content-summarizer/docs/api-integration/` folder
2. ✅ Move all 48 files to appropriate folders
3. ✅ Create master README.md in docs/ with navigation
4. ✅ Update content-summarizer/README.md to point to docs
5. ✅ Create index files in each subfolder
6. ✅ Clean up root directory

## Benefits

- ✅ **Single source of truth** - All docs in one place
- ✅ **Easy navigation** - Clear folder structure
- ✅ **Better organization** - Grouped by purpose
- ✅ **Clean root directory** - Only code files remain
- ✅ **Easier maintenance** - Logical categorization
