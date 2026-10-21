> **Status: superseded.** See the note at the top of `REFACTORING_PLAN.md`;
> the refactoring took a different direction and these tasks do not describe it.

# Development Workflow für Icon Manager Refactoring

## 🌿 Branch Strategy

### Branch Naming Convention
```
refactor/phase-{phase-number}-{component-name}
refactor/phase-1-service-decomposition
refactor/phase-2-event-bus
refactor/phase-3-async-crawler
```

### Main Branches
- `master` - Production-ready code
- `develop` - Integration branch für Refactoring

## 📋 Task Management mit Git

### 1. Feature Branches für Refactoring-Phasen
Jede Phase wird in einem eigenen Feature Branch entwickelt:

```bash
# Phase 1: Service Decomposition
git checkout -b refactor/phase-1-service-decomposition

# Phase 2: Event-Driven Architecture  
git checkout -b refactor/phase-2-event-driven

# Phase 3: Async Performance
git checkout -b refactor/phase-3-async-performance
```

### 2. Sub-Branches für spezifische Tasks
Für größere Tasks innerhalb einer Phase:

```bash
# Beispiel: LibraryManagementService innerhalb Phase 1
git checkout refactor/phase-1-service-decomposition
git checkout -b refactor/phase-1-library-service

# Nach Fertigstellung: Merge zurück in Phase Branch
git checkout refactor/phase-1-service-decomposition
git merge refactor/phase-1-library-service
```

### 3. Commit Message Convention

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: Neue Funktionalität
- `refactor`: Code-Refactoring ohne Funktionalitäts-Änderung
- `test`: Test-Ergänzungen oder -Änderungen
- `docs`: Dokumentations-Änderungen
- `arch`: Architektur-Änderungen

**Examples:**
```bash
git commit -m "refactor(services): split IconsAppService into focused services

- Create LibraryManagementService for library operations
- Create ContentProcessingService for content operations  
- Create ConfigurationService for config management

Closes #123"

git commit -m "feat(event-bus): implement core event bus system

- Add EventBus class with publish/subscribe
- Define core events: FolderDiscovered, IconApplied, etc.
- Add async event processing support

Part of Phase 2 refactoring"
```

## 🏗️ Development Phasen (flexibel und stressfrei)

### Phase 1: Service Decomposition
**Branch:** `refactor/phase-1-service-decomposition`
**Philosophie:** Saubere Trennung von Verantwortlichkeiten

**Sub-tasks (in beliebiger Reihenfolge):**
1. `refactor/phase-1-library-service` - LibraryManagementService
2. `refactor/phase-1-content-service` - ContentProcessingService  
3. `refactor/phase-1-config-service` - ConfigurationService
4. `refactor/phase-1-di-container` - Dependency Injection

**Merge Strategy:**
- Sub-branches → Phase branch → develop → master
- **Kein Zeitdruck:** Tasks können parallel oder sequenziell bearbeitet werden

### Phase 2: Event-Driven Architecture
**Branch:** `refactor/phase-2-event-driven`
**Philosophie:** Lose Kopplung durch Events

**Sub-tasks (flexibel priorisierbar):**
1. `refactor/phase-2-event-bus` - Event Bus Implementation
2. `refactor/phase-2-core-events` - Core Event Definitions
3. `refactor/phase-2-service-migration` - Service-to-Event Migration

### Phase 3: Async Performance
**Branch:** `refactor/phase-3-async-performance`
**Philosophie:** Performance ohne Komplexität zu opfern

**Sub-tasks (je nach Bedarf):**
1. `refactor/phase-3-async-crawler` - Async Folder Crawler
2. `refactor/phase-3-background-processing` - Background Processing Pipeline
3. `refactor/phase-3-progress-tracking` - Progress Tracking System

## 📊 Progress Tracking

### 1. Branch Status Tracking
Verwende Branch-Namen um Status zu verfolgen:

```bash
# In Arbeit
refactor/phase-1-library-service

# Review bereit
refactor/phase-1-library-service-ready

# Abgeschlossen (gemerged)
# Branch wird gelöscht nach Merge
```

### 2. Commit-basierte Aufgaben-Tracking
Verwende Commit-Messages um Fortschritt zu dokumentieren:

```bash
# Task Start
git commit -m "refactor(library): start LibraryManagementService implementation

WIP: Basic service structure and interface definition"

# Milestone erreicht
git commit -m "refactor(library): complete LibraryManagementService core functionality

✅ create_configs() implemented and tested
✅ update_configs() implemented and tested  
✅ delete_configs() implemented and tested

Remaining: Integration with event system"

# Task Complete
git commit -m "refactor(library): complete LibraryManagementService

✅ All CRUD operations implemented
✅ Event integration completed
✅ Unit tests added (95% coverage)
✅ Integration tests added

Ready for Phase 1 integration"
```

### 3. Tag-basierte Meilensteine
Verwende Git Tags für wichtige Meilensteine:

```bash
# Phase Completion Tags
git tag -a "refactor-phase-1-complete" -m "Phase 1: Service Decomposition completed"
git tag -a "refactor-phase-2-complete" -m "Phase 2: Event-Driven Architecture completed"

# Performance Milestone Tags
git tag -a "performance-baseline" -m "Performance baseline before async refactoring"
git tag -a "performance-improved" -m "4x performance improvement achieved"
```

## 🧪 Quality Gates

### Pre-Commit Checks
Jeder Commit muss folgende Checks bestehen:

```bash
# Code Quality
ruff check .
ruff format --check .

# Type Checking  
pyright

# Tests
pytest tests/unit/ --tb=short
pytest tests/integration/ --tb=short

# Performance (für relevante Branches)
pytest tests/performance/ --benchmark-only
```

### Branch Protection Rules
```yaml
# Für master und develop branches
required_checks:
  - "pytest-unit"
  - "pytest-integration"  
  - "ruff-check"
  - "pyright"
  - "performance-tests" # nur für performance-relevante PRs

required_reviews: 1
dismiss_stale_reviews: true
```

## 📈 Progress Visualization

### 1. Git Log als Task History
```bash
# Zeige Refactoring-Fortschritt
git log --oneline --grep="refactor" --since="1 month ago"

# Zeige Phase-spezifischen Fortschritt
git log --oneline refactor/phase-1-service-decomposition

# Zeige Performance-Improvements
git log --oneline --grep="performance"
```

### 2. Branch Tree Visualization
```bash
# Zeige Branch-Struktur
git log --graph --pretty=format:'%h -%d %s (%cr) <%an>' --abbrev-commit --all

# Nur Refactoring-Branches
git branch -a | grep refactor
```

### 3. Statistiken und Metriken
```bash
# Code-Änderungen pro Phase
git diff --stat master..refactor/phase-1-service-decomposition

# Contributor-Statistiken
git shortlog -sn --since="1 month ago" --grep="refactor"

# File-Change-Häufigkeit
git log --pretty=format: --name-only --since="1 month ago" | sort | uniq -c | sort -rg
```

## 🔄 Merge Strategy

### 1. Feature Branch → Phase Branch
```bash
# Squash smaller commits
git checkout refactor/phase-1-service-decomposition
git merge --squash refactor/phase-1-library-service
git commit -m "refactor(library): add LibraryManagementService

Complete implementation of LibraryManagementService with:
- CRUD operations for library configs
- Event integration
- Comprehensive test suite

Part of Phase 1: Service Decomposition"
```

### 2. Phase Branch → Develop
```bash
# Merge commit für Phase-Abschluss
git checkout develop
git merge --no-ff refactor/phase-1-service-decomposition
git tag -a "refactor-phase-1-complete" -m "Phase 1: Service Decomposition completed"
```

### 3. Develop → Master
```bash
# Nach Abschluss aller Phasen und Testing
git checkout master
git merge --no-ff develop
git tag -a "v2.0.0-refactored" -m "Major refactoring: Event-driven architecture implemented"
```

## 📝 Documentation in Git

### 1. Commit-basierte Dokumentation
Jeder wichtige Commit enthält detaillierte Beschreibung:

```bash
git commit -m "refactor(event-bus): implement async event processing

Implementation Details:
- AsyncEventBus with asyncio.Queue for event processing
- Event handler registration with type safety
- Automatic error handling and retry logic
- Performance optimization with event batching

Performance Impact:
- Event processing: ~1000 events/second
- Memory usage: <10MB for 10k events
- Latency: <1ms for local events

Testing:
- Unit tests: 15 new tests added
- Performance tests: Benchmark suite added
- Integration tests: Event flow validation

Breaking Changes:
- EventBus.publish() is now async
- Event handlers must be async functions

Migration Guide:
See MIGRATION.md for upgrade instructions"
```

### 2. Branch-basierte Dokumentation
Jeder Phase-Branch enthält spezifische README:

```bash
# In refactor/phase-1-service-decomposition/
echo "# Phase 1: Service Decomposition

## Current Status
- [x] LibraryManagementService
- [ ] ContentProcessingService
- [ ] ConfigurationService
- [ ] Dependency Injection

## Performance Metrics
- Code complexity: -40%
- Test coverage: +25%
- Build time: -15%" > PHASE_1_STATUS.md
```

---

Diese Git-basierte Workflow ermöglicht es, das gesamte Refactoring systematisch zu verfolgen, ohne externe Tools zu benötigen. Jeder Commit, Branch und Tag erzählt die Geschichte des Refactorings und macht den Fortschritt transparent und nachvollziehbar.