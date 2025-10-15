# Experiments

This directory contains documentation for experimental features, prototypes, and feature developments in the HS Agent project.

## Contents

### 01. No HS Code Feature (000000)
**Files:**
- `01-no-hs-code-feature.md` - Implementation details
- `02-no-hs-code-test-results.md` - Test results and validation

**Status:** ✅ Implemented and Tested  
**Branch:** `feature/no-hs-code-classification`  
**Date:** October 15, 2025

Adds support for returning HS code "000000" when product descriptions are invalid, meaningless, or not classifiable (e.g., "test", gibberish). This special classification is available at the final stage of all three workflow types.

---

## Experiment Numbering

Each experiment is numbered sequentially:
- `01-` through `09-` for single-digit experiments
- `10-` and beyond for additional experiments

Multiple related documents for the same experiment should use sub-numbering:
- `01-feature-name.md` - Main implementation doc
- `02-feature-name-test-results.md` - Test results
- `03-feature-name-analysis.md` - Analysis or findings

---

## Adding New Experiments

When adding a new experiment:

1. Create numbered files in this directory
2. Update this README with a new section
3. Include status, branch name, and date
4. Link to related PR or issue if applicable

