# HS Agent Refactoring Plan

## Executive Summary

Refactor the 851-line `HSAgent` god object into smaller, focused classes following SOLID principles. This will improve testability, maintainability, and eliminate code duplication while maintaining backward compatibility.

**Timeline:** 4-6 phases, each completable in 1-2 hours
**Risk Level:** Low (incremental changes with tests after each phase)
**Breaking Changes:** None (existing API remains intact)

---

## Current State Analysis

### Problems Identified

1. **God Object Anti-pattern**
   - `hs_agent/agent.py`: 851 lines, 21 methods
   - Single class handling 10+ responsibilities
   - Difficult to test in isolation
   - High cognitive load

2. **Code Duplication**
   - Selection logic duplicated in `_select_code` and `_multi_select_codes`
   - Initialization patterns repeated across `app.py` and `cli.py`
   - No-code handling appears 3+ times in agent.py
   - Model creation logic could be shared

3. **Missing Abstractions**
   - No separation between single-path and multi-choice workflows
   - No model factory for LLM creation
   - No retry policy abstraction
   - No dedicated service for chapter notes

4. **Poor Testability**
   - Cannot test workflows without full agent initialization
   - Cannot mock model creation easily
   - Retry logic tightly coupled to agent

### Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Lines per class | 851 | <250 |
| Methods per class | 21 | <10 |
| Responsibilities | 10+ | 1-2 |
| Duplication score | High | Low |
| Test coverage | Unknown | >80% |

---

## Proposed Architecture

### New File Structure

```
hs_agent/
├── agent.py                    # Thin facade (~150 lines)
├── models.py                   # Existing models (keep)
├── data_loader.py              # Existing data loader (keep)
├── graph_models.py             # Existing state models (keep)
├── config_loader.py            # Existing config loader (keep)
├── cli.py                      # Existing CLI (keep)
├── factories/
│   ├── __init__.py
│   └── model_factory.py        # LLM model creation (~80 lines)
├── services/
│   ├── __init__.py
│   ├── retry_policy.py         # Retry logic (~100 lines)
│   └── chapter_notes_service.py # Chapter notes loading (~80 lines)
├── workflows/
│   ├── __init__.py
│   ├── base.py                 # Base workflow interface (~50 lines)
│   ├── single_path.py          # Single-path workflow (~200 lines)
│   └── multi_choice.py         # Multi-choice workflow (~250 lines)
├── config/
│   └── settings.py             # Existing settings (keep)
└── utils/
    └── logger.py               # Existing logger (keep)
```

### Class Responsibilities

#### 1. `HSAgent` (Facade)
**Responsibility:** Public API and delegation
**Lines:** ~150
```python
class HSAgent:
    """Thin facade that delegates to workflows."""

    def __init__(self, data_loader, model_name, workflow_name):
        self.data_loader = data_loader
        self.workflow = WorkflowFactory.create(workflow_name, ...)

    async def classify(self, description: str) -> ClassificationResponse:
        return await self.workflow.classify(description)

    async def classify_multi(self, description: str, max_selections: int) -> MultiChoiceClassificationResponse:
        return await self.workflow.classify_multi(description, max_selections)
```

#### 2. `ModelFactory`
**Responsibility:** Create and configure LLM models
**Lines:** ~80
```python
class ModelFactory:
    """Factory for creating ChatVertexAI models."""

    @staticmethod
    def create_base_model(model_params: Dict) -> ChatVertexAI:
        """Create base model with standard config."""
        pass

    @staticmethod
    def create_with_schema(base_model, schema, enum_codes=None):
        """Add structured output to model."""
        pass
```

#### 3. `RetryPolicy`
**Responsibility:** Handle LLM invocation with retries
**Lines:** ~100
```python
class RetryPolicy:
    """Handles retry logic for LLM calls."""

    def __init__(self, max_retries=3, initial_delay=1.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay

    async def invoke_with_retry(self, model, messages) -> Any:
        """Invoke LLM with exponential backoff."""
        pass
```

#### 4. `ChapterNotesService`
**Responsibility:** Load and manage chapter notes
**Lines:** ~80
```python
class ChapterNotesService:
    """Service for loading chapter notes from files."""

    def __init__(self, notes_dir: Path):
        self.notes_dir = notes_dir

    def load_notes(self, chapter_codes: List[str]) -> str:
        """Load notes for given chapter codes."""
        pass
```

#### 5. `BaseWorkflow` (Abstract)
**Responsibility:** Define workflow interface
**Lines:** ~50
```python
class BaseWorkflow(ABC):
    """Base class for all classification workflows."""

    def __init__(self, data_loader, model_factory, retry_policy, configs):
        self.data_loader = data_loader
        self.model_factory = model_factory
        self.retry_policy = retry_policy
        self.configs = configs

    @abstractmethod
    async def classify(self, description: str):
        pass
```

#### 6. `SinglePathWorkflow`
**Responsibility:** Single-path hierarchical classification
**Lines:** ~200
```python
class SinglePathWorkflow(BaseWorkflow):
    """Implements single-path classification (chapter→heading→subheading)."""

    def __init__(self, ...):
        super().__init__(...)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build LangGraph for single-path workflow."""
        pass

    async def classify(self, description: str) -> ClassificationResponse:
        """Execute single-path classification."""
        pass

    # Node methods: _select_chapter, _select_heading, _select_subheading, _finalize
```

#### 7. `MultiChoiceWorkflow`
**Responsibility:** Multi-choice classification with path exploration
**Lines:** ~250
```python
class MultiChoiceWorkflow(BaseWorkflow):
    """Implements multi-choice classification (1-to-N paths)."""

    def __init__(self, ...):
        super().__init__(...)
        self.graph = self._build_graph()
        self.chapter_notes_service = ChapterNotesService(...)

    def _build_graph(self):
        """Build LangGraph for multi-choice workflow."""
        pass

    async def classify_multi(self, description: str, max_selections: int) -> MultiChoiceClassificationResponse:
        """Execute multi-choice classification."""
        pass

    # Node methods: _multi_select_chapters, _multi_select_headings, etc.
```

---

## Implementation Phases

### Phase 0: Preparation
**Goal:** Set up testing infrastructure and document current behavior
**Duration:** 30 minutes

**Tasks:**
- [ ] Create comprehensive integration tests for current behavior
- [ ] Document all public APIs and their expected outputs
- [ ] Run full test suite and record baseline metrics
- [ ] Create `REFACTORING_PLAN.md` (this file)
- [ ] Create `tests/test_refactoring.py` to verify backward compatibility

**Deliverables:**
- Integration test suite covering all workflows
- Documented baseline behavior
- This refactoring plan

**Risk:** Low - No code changes yet

---

### Phase 1: Extract ModelFactory
**Goal:** Remove model creation logic from HSAgent
**Duration:** 1 hour

**Files to Create:**
```
hs_agent/factories/__init__.py
hs_agent/factories/model_factory.py
```

**Files to Modify:**
```
hs_agent/agent.py (remove _create_base_model, _get_model_for_config)
```

**Step-by-step:**

1. **Create `hs_agent/factories/__init__.py`**
   ```python
   from .model_factory import ModelFactory

   __all__ = ["ModelFactory"]
   ```

2. **Create `hs_agent/factories/model_factory.py`**
   - Move `_create_base_model` → `ModelFactory.create_base_model` (static method)
   - Move `_get_model_for_config` logic → `ModelFactory.create_with_schema`
   - Add proper imports and type hints

3. **Update `hs_agent/agent.py`**
   - Import ModelFactory
   - Replace `self._create_base_model(...)` → `ModelFactory.create_base_model(...)`
   - Replace model creation calls with factory methods
   - Remove old methods

4. **Run tests**
   - Integration tests should pass
   - No behavior changes

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] ModelFactory has unit tests
- [ ] agent.py reduced by ~50 lines
- [ ] No breaking changes

**Rollback Plan:** Git revert if tests fail

---

### Phase 2: Extract RetryPolicy
**Goal:** Separate retry logic into dedicated service
**Duration:** 1 hour

**Files to Create:**
```
hs_agent/services/__init__.py
hs_agent/services/retry_policy.py
```

**Files to Modify:**
```
hs_agent/agent.py (remove _invoke_with_retry)
```

**Step-by-step:**

1. **Create `hs_agent/services/__init__.py`**
   ```python
   from .retry_policy import RetryPolicy

   __all__ = ["RetryPolicy"]
   ```

2. **Create `hs_agent/services/retry_policy.py`**
   - Move `_invoke_with_retry` → `RetryPolicy.invoke_with_retry` (instance method)
   - Make configurable (max_retries, initial_delay)
   - Add logger integration
   - Add unit tests for retry behavior

3. **Update `hs_agent/agent.py`**
   - Create `self.retry_policy = RetryPolicy(max_retries=3)` in `__init__`
   - Replace all `await self._invoke_with_retry(...)` → `await self.retry_policy.invoke_with_retry(...)`
   - Remove old method

4. **Run tests**
   - All workflows should work
   - Retry behavior unchanged

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] RetryPolicy has unit tests (mock LLM failures)
- [ ] agent.py reduced by ~70 lines
- [ ] Can configure retry behavior per workflow

**Rollback Plan:** Git revert if tests fail

---

### Phase 3: Extract ChapterNotesService
**Goal:** Separate chapter notes loading into dedicated service
**Duration:** 45 minutes

**Files to Create:**
```
hs_agent/services/chapter_notes_service.py
```

**Files to Modify:**
```
hs_agent/agent.py (remove _load_chapter_notes)
hs_agent/services/__init__.py (add ChapterNotesService)
```

**Step-by-step:**

1. **Create `hs_agent/services/chapter_notes_service.py`**
   - Move `_load_chapter_notes` → `ChapterNotesService.load_notes`
   - Add caching for loaded notes
   - Add unit tests with mock files

2. **Update `hs_agent/agent.py`**
   - Create `self.chapter_notes_service = ChapterNotesService(Path("data/chapters_markdown"))` in `__init__`
   - Replace `self._load_chapter_notes(...)` → `self.chapter_notes_service.load_notes(...)`
   - Remove old method

3. **Update `hs_agent/services/__init__.py`**
   ```python
   from .retry_policy import RetryPolicy
   from .chapter_notes_service import ChapterNotesService

   __all__ = ["RetryPolicy", "ChapterNotesService"]
   ```

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] ChapterNotesService has unit tests
- [ ] agent.py reduced by ~40 lines
- [ ] Chapter notes can be cached

**Rollback Plan:** Git revert if tests fail

---

### Phase 4: Extract Workflow Classes
**Goal:** Separate single-path and multi-choice workflows
**Duration:** 2-3 hours (most complex phase)

**Files to Create:**
```
hs_agent/workflows/__init__.py
hs_agent/workflows/base.py
hs_agent/workflows/single_path.py
hs_agent/workflows/multi_choice.py
```

**Files to Modify:**
```
hs_agent/agent.py (major refactor to facade)
```

**Step-by-step:**

1. **Create `hs_agent/workflows/base.py`**
   ```python
   class BaseWorkflow(ABC):
       """Base class for all classification workflows."""

       def __init__(self, data_loader, model_factory, retry_policy, configs, langfuse_handler=None):
           self.data_loader = data_loader
           self.model_factory = model_factory
           self.retry_policy = retry_policy
           self.configs = configs
           self.langfuse_handler = langfuse_handler

       @abstractmethod
       async def classify(self, description: str):
           """Execute classification."""
           pass

       def _get_level_name(self, level: ClassificationLevel) -> str:
           """Get human-readable level name."""
           return {"2": "CHAPTER", "4": "HEADING", "6": "SUBHEADING"}[level.value]
   ```

2. **Create `hs_agent/workflows/single_path.py`**
   - Move single-path graph building
   - Move node methods: `_select_chapter`, `_select_heading`, `_select_subheading`, `_finalize`
   - Move `_select_code` helper
   - Implement `classify()` method
   - ~200 lines total

3. **Create `hs_agent/workflows/multi_choice.py`**
   - Move multi-choice graph building
   - Move node methods: `_multi_select_chapters`, `_multi_select_headings`, etc.
   - Move `_multi_select_codes` helper
   - Move `_multi_build_paths`
   - Move `_compare_final_codes`
   - Implement `classify_multi()` method
   - Integrate ChapterNotesService
   - ~250 lines total

4. **Create `hs_agent/workflows/__init__.py`**
   ```python
   from .base import BaseWorkflow
   from .single_path import SinglePathWorkflow
   from .multi_choice import MultiChoiceWorkflow

   __all__ = ["BaseWorkflow", "SinglePathWorkflow", "MultiChoiceWorkflow"]
   ```

5. **Refactor `hs_agent/agent.py` to facade**
   ```python
   class HSAgent:
       """HS classification agent facade."""

       def __init__(self, data_loader, model_name=None, workflow_name="wide_net_classification"):
           self.data_loader = data_loader
           self.model_name = model_name or settings.default_model_name

           # Load configs
           workflow_path = Path(f"configs/{workflow_name}")
           self.configs = load_workflow_configs(workflow_path)

           # Initialize services
           self.model_factory = ModelFactory()
           self.retry_policy = RetryPolicy(max_retries=3)
           self.chapter_notes_service = ChapterNotesService(Path("data/chapters_markdown"))

           # Initialize Langfuse
           self.langfuse_handler = self._init_langfuse() if settings.langfuse_enabled else None

           # Create workflow
           if workflow_name == "single_path_classification":
               self.workflow = SinglePathWorkflow(
                   data_loader=self.data_loader,
                   model_factory=self.model_factory,
                   retry_policy=self.retry_policy,
                   configs=self.configs,
                   langfuse_handler=self.langfuse_handler
               )
           elif workflow_name in ["wide_net_classification", "multi_choice_classification"]:
               self.workflow = MultiChoiceWorkflow(
                   data_loader=self.data_loader,
                   model_factory=self.model_factory,
                   retry_policy=self.retry_policy,
                   configs=self.configs,
                   langfuse_handler=self.langfuse_handler,
                   chapter_notes_service=self.chapter_notes_service
               )
           else:
               raise ValueError(f"Unknown workflow: {workflow_name}")

       async def classify(self, product_description: str) -> ClassificationResponse:
           """Delegate to workflow."""
           return await self.workflow.classify(product_description)

       async def classify_multi(self, product_description: str, max_selections: int = 3) -> MultiChoiceClassificationResponse:
           """Delegate to workflow."""
           return await self.workflow.classify_multi(product_description, max_selections)

       def _init_langfuse(self):
           """Initialize Langfuse handler."""
           # Existing Langfuse init code
           pass
   ```

6. **Run comprehensive tests**
   - All integration tests must pass
   - Test both single-path and multi-choice workflows
   - Test with different configurations

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] agent.py reduced to ~150 lines
- [ ] SinglePathWorkflow fully functional
- [ ] MultiChoiceWorkflow fully functional
- [ ] No breaking changes to public API
- [ ] Each workflow can be tested independently

**Rollback Plan:** Git revert entire phase if integration tests fail

---

### Phase 5: Eliminate Code Duplication
**Goal:** Remove duplicated selection logic
**Duration:** 1 hour

**Files to Modify:**
```
hs_agent/workflows/base.py (add shared selection logic)
hs_agent/workflows/single_path.py (use shared logic)
hs_agent/workflows/multi_choice.py (use shared logic)
```

**Step-by-step:**

1. **Add shared selection method to `BaseWorkflow`**
   ```python
   async def _select_codes_base(
       self,
       product_description: str,
       codes_dict: Dict,
       level: ClassificationLevel,
       config_name: str,
       parent_code: Optional[str] = None,
       max_selections: int = 1
   ) -> Dict[str, Any]:
       """Shared selection logic for both single and multi selection."""
       # Common logic for preparing candidates, prompts, invoking LLM
       pass
   ```

2. **Refactor `SinglePathWorkflow._select_code`**
   - Use `_select_codes_base` with `max_selections=1`
   - Remove duplicated code

3. **Refactor `MultiChoiceWorkflow._multi_select_codes`**
   - Use `_select_codes_base` with configurable `max_selections`
   - Remove duplicated code

4. **Run tests**
   - All workflows should work identically
   - No behavior changes

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] ~80 lines of duplication removed
- [ ] Both workflows use shared logic
- [ ] Selection behavior unchanged

**Rollback Plan:** Git revert if tests fail

---

### Phase 6: Add Comprehensive Tests
**Goal:** Achieve >80% test coverage
**Duration:** 1-2 hours

**Files to Create:**
```
tests/unit/test_model_factory.py
tests/unit/test_retry_policy.py
tests/unit/test_chapter_notes_service.py
tests/unit/workflows/test_single_path.py
tests/unit/workflows/test_multi_choice.py
tests/integration/test_agent_facade.py
```

**Test Categories:**

1. **ModelFactory Tests**
   - Test base model creation
   - Test schema attachment
   - Test enum injection

2. **RetryPolicy Tests**
   - Test successful invocation
   - Test retry on None result
   - Test retry on exception
   - Test exponential backoff timing
   - Test max retries exhaustion

3. **ChapterNotesService Tests**
   - Test loading existing notes
   - Test missing notes handling
   - Test caching behavior
   - Test multiple chapter codes

4. **SinglePathWorkflow Tests**
   - Test graph building
   - Test single classification
   - Test with mock LLM responses
   - Test error handling

5. **MultiChoiceWorkflow Tests**
   - Test graph building
   - Test multi-choice classification
   - Test path building
   - Test path comparison
   - Test with mock LLM responses

6. **HSAgent Facade Tests**
   - Test workflow delegation
   - Test backward compatibility
   - Test all public APIs

**Acceptance Criteria:**
- [ ] Test coverage >80%
- [ ] All edge cases covered
- [ ] Mock LLM responses for speed
- [ ] Integration tests verify end-to-end

---

## Migration Strategy

### Backward Compatibility

**Public API Unchanged:**
```python
# All existing code continues to work
agent = HSAgent(data_loader, workflow_name="wide_net_classification")
result = await agent.classify("laptop")
multi_result = await agent.classify_multi("laptop", max_selections=3)
```

**Internal Changes Transparent:**
- app.py requires no changes
- cli.py requires no changes
- All existing tests pass

### Deployment Strategy

1. **Deploy Phase by Phase**
   - Each phase is independently deployable
   - Run full test suite after each phase
   - Monitor production for regressions

2. **Feature Flags** (optional)
   - Can add `use_legacy_agent` flag if needed
   - Allows quick rollback in production

3. **Gradual Rollout**
   - Deploy to staging first
   - Monitor metrics
   - Deploy to production with monitoring

---

## Risk Assessment

### Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing API | High | Low | Comprehensive integration tests, backward compatibility focus |
| Performance regression | Medium | Low | Benchmark before/after, profile critical paths |
| Bug introduction | Medium | Medium | Phase-by-phase testing, rollback plan for each phase |
| Incomplete tests | Medium | Medium | Code review, coverage requirements |
| Team unfamiliarity | Low | Medium | Clear documentation, pair programming |

### Rollback Strategy

**Per Phase:**
- Git revert the phase commit
- Run test suite
- Verify production health

**Emergency Rollback:**
- Revert to previous commit
- Deploy immediately
- Investigate issues offline

---

## Success Metrics

### Code Quality Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Lines per class | 851 | <250 | `wc -l` |
| Methods per class | 21 | <10 | `grep "def "` |
| Cyclomatic complexity | High | <10 per method | `radon cc` |
| Code duplication | ~15% | <5% | Manual review |
| Test coverage | Unknown | >80% | `pytest --cov` |

### Maintainability Metrics

- **Time to add new workflow:** <2 hours (vs current ~1 day)
- **Time to understand code:** <30 min (vs current ~2 hours)
- **New developer onboarding:** <1 day (vs current ~3 days)

### Performance Metrics

- **Classification latency:** No regression (±5% acceptable)
- **Memory usage:** No regression
- **Test suite runtime:** Should be faster (more unit tests, fewer integration tests)

---

## Documentation Updates

### Files to Update After Refactoring

1. **README.md**
   - Update architecture diagram
   - Add new class descriptions
   - Update testing section

2. **CLAUDE.md**
   - Update project structure
   - Update development patterns
   - Add refactoring notes

3. **API Documentation**
   - Update docstrings
   - Generate new API docs
   - Update examples

4. **Developer Guide**
   - Create "Adding a New Workflow" guide
   - Create "Testing Guide"
   - Create "Architecture Overview"

---

## Timeline

### Estimated Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 0: Preparation | 30 min | 30 min |
| Phase 1: ModelFactory | 1 hour | 1.5 hours |
| Phase 2: RetryPolicy | 1 hour | 2.5 hours |
| Phase 3: ChapterNotesService | 45 min | 3.25 hours |
| Phase 4: Workflow Classes | 2.5 hours | 5.75 hours |
| Phase 5: Eliminate Duplication | 1 hour | 6.75 hours |
| Phase 6: Testing | 1.5 hours | 8.25 hours |
| **Total** | **~8-9 hours** | **~2 work days** |

### Checkpoints

- **End of Phase 2:** First commit, core services extracted
- **End of Phase 4:** Major refactor complete, full functionality
- **End of Phase 6:** Production-ready, fully tested

---

## Questions and Decisions

### Open Questions

1. **Q:** Should we create a WorkflowFactory for workflow creation?
   **A:** TBD - Evaluate after Phase 4

2. **Q:** Should we add workflow configuration validation?
   **A:** Yes - Add in Phase 4

3. **Q:** Do we need abstract methods for node functions?
   **A:** Optional - Evaluate during Phase 4

4. **Q:** Should RetryPolicy be configurable per workflow?
   **A:** Yes - Pass config in Phase 2

### Design Decisions

1. **Use Composition over Inheritance**
   - Workflows compose services (ModelFactory, RetryPolicy)
   - Easier to test and modify

2. **Keep Langfuse in Workflows**
   - Callbacks are workflow-specific
   - Don't extract into separate service

3. **Maintain LangGraph Structure**
   - Don't change graph execution model
   - Only reorganize surrounding code

4. **Backward Compatibility is Critical**
   - Public API must not change
   - HSAgent remains the main entry point

---

## Approval and Sign-off

### Before Starting

- [ ] Review this plan with team
- [ ] Agreement on architecture
- [ ] Baseline tests in place
- [ ] Git branch created: `refactor/extract-workflows`

### After Each Phase

- [ ] All tests pass
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Metrics recorded

### Final Sign-off

- [ ] All phases complete
- [ ] Test coverage >80%
- [ ] Performance benchmarks acceptable
- [ ] Documentation complete
- [ ] Production deployment approved

---

## Appendix

### Useful Commands

```bash
# Line counts
wc -l hs_agent/agent.py

# Count methods
grep -E "^    (async )?def " hs_agent/agent.py | wc -l

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=hs_agent --cov-report=html

# Check complexity
radon cc hs_agent/agent.py -a

# Find duplication
pylint hs_agent/agent.py --disable=all --enable=duplicate-code
```

### Related Documents

- [CLAUDE.md](./CLAUDE.md) - Project overview
- [README.md](./README.md) - User documentation
- Architecture diagrams: TBD after refactoring

---

**Created:** 2025-10-16
**Status:** Draft - Awaiting Approval
**Version:** 1.0
