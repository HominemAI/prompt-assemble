# Research Paper Generator - Example Prompt Source

A comprehensive example system demonstrating variable hierarchy, nested prompt inclusion, and tag-based prompt injection. This example shows how to build complex, reusable prompt systems with modular components.

## Overview

This system generates complete research papers by combining:
- **Main orchestrator** (`research_paper_generator`) that coordinates all sections
- **Reusable templates** (abstract, methodology, references) with variable placeholders
- **Nested prompt includes** (`[[PROMPT: name]]`) for composing complex structures
- **Tag-based injection** (`[[PROMPT_TAG: tags]]`) for dynamically including examples and references
- **Variable hierarchy** allowing each component to maintain its own variable context

## Directory Structure

```
research_paper_system/
├── _registry.json                          # Metadata and tags for all prompts
├── README.md                               # This file
│
├── research_paper_generator.prompt         # Main orchestrator prompt
├── abstract_template.prompt                # Abstract section template
├── research_instructions.prompt            # Research guidelines
├── methodology_template.prompt             # Methodology section
├── validation_checklist.prompt             # Validation checklist
├── reference_guidelines.prompt             # Citation and reference guidelines
│
├── example_ai_research.prompt              # Case study: AI in CS research
├── example_biomedical_study.prompt         # Case study: AI in drug discovery
├── example_social_science.prompt           # Case study: AI in survey analysis
│
├── foundational_machine_learning.prompt    # ML concepts reference
├── foundational_statistics.prompt          # Statistics concepts reference
├── foundational_research_ethics.prompt     # Research ethics reference
│
├── example_citation_ml.prompt              # ML citation examples
└── example_citation_statistics.prompt      # Statistics citation examples
```

## Usage

### Using FileSystemSource

```python
from prompt_assemble.sources import FileSystemSource
from prompt_assemble import PromptProvider

# Load prompts from this directory
source = FileSystemSource("examples/research_paper_system")
provider = PromptProvider(source)

# List all available prompts
all_prompts = provider.list()
print(all_prompts)

# Find prompts by tags (AND intersection)
case_studies = provider.find_by_tag("case_study", "practical_example")
print(case_studies)

# Render a prompt with variables
variables = {
    "PAPER_TITLE": "The Impact of AI on Modern Research",
    "AUTHOR_NAME": "Dr. Jane Smith",
    # ... more variables ...
}

output = provider.render("research_paper_generator", variables=variables)
print(output)
```

### Using DatabaseSource

```python
from prompt_assemble.sources import DatabaseSource
import psycopg2

# Load into database first
conn = psycopg2.connect("dbname=prompts user=postgres")
source = DatabaseSource(conn)

# Refresh to load from disk (if implementing sync mechanism)
# source.refresh()

# Then use like FileSystemSource
provider = PromptProvider(source)
```

### Using in Web UI (PROMPT_ASSEMBLE_UI=true)

1. Start the server:
```bash
cd src/prompt_assemble/ui/frontend
npm install && npm run build
cd ..
export PROMPT_ASSEMBLE_UI=true
export PROMPT_ASSEMBLE_SOURCE=filesystem
export FILESYSTEM_ROOT=../../examples/research_paper_system
python -m prompt_assemble.ui.server
```

2. Open http://localhost:8000 in browser
3. Prompts are automatically loaded and displayed

## Prompt Architecture

### Main Orchestrator: `research_paper_generator`

This is the entry point that:
- Defines the overall paper structure
- References other prompts via `[[PROMPT: name]]`
- Uses variables for metadata
- Demonstrates both prompt inclusion and tag-based injection

**Tags:** `template`, `main`, `research`, `academic`, `paper`

### Template Prompts

These are reusable sections included via `[[PROMPT: name]]`:

| Prompt | Included By | Variables Required |
|--------|-------------|-------------------|
| `abstract_template` | research_paper_generator | SUBJECT_AREA, FOCUS_AREA, METHODOLOGY_BRIEF, KEY_FINDING, FIELD_IMPLICATIONS, KEYWORDS |
| `research_instructions` | research_paper_generator | SUBJECT_AREA, PROBLEM_STATEMENT, METHODOLOGY_BRIEF, SUCCESS_METRICS, RESULTS_PRESENTATION_STYLE, AUDIENCE_LEVEL, ACADEMIC_RIGOR |
| `methodology_template` | research_paper_generator | METHODOLOGY_BRIEF, RESEARCH_DESIGN, PARTICIPANT_DESCRIPTION, DATA_COLLECTION_METHOD, STUDY_DURATION, RESEARCH_TOOLS, STATISTICAL_METHOD, CONFIDENCE_LEVEL |
| `validation_checklist` | methodology_template | SUBJECT_AREA, VALIDITY_CHECK_1/2/3, REVIEW_AUTHORITY, VALIDATION_METHOD |
| `reference_guidelines` | research_paper_generator | CITATION_STYLE, MIN_REFERENCES, RECENCY_YEARS, REFERENCE_BALANCE, AUTHORITY_LEVEL |

### Tag-Based Injection

#### `[[PROMPT_TAG: reference, foundational]]`
Injects all documents tagged with BOTH "reference" AND "foundational":
- `foundational_machine_learning`
- `foundational_statistics`
- `foundational_research_ethics`

#### `[[PROMPT_TAG: 3: case_study, practical_example]]`
Injects up to 3 documents tagged with BOTH "case_study" AND "practical_example":
- `example_ai_research`
- `example_biomedical_study`
- `example_social_science`

#### `[[PROMPT_TAG: reference, example]]`
Injects citation examples (in `reference_guidelines`):
- `example_citation_ml`
- `example_citation_statistics`

## Variables

### Document-Level Variables

Variables are organized by document type and purpose:

#### Main Paper Variables (in `research_paper_generator`)
```
PAPER_TITLE              = "The Impact of AI on Modern Research"
AUTHOR_NAME              = "Dr. Jane Smith"
PUBLICATION_DATE         = "2026-02-28"
INSTITUTION              = "MIT Media Lab"
SUBJECT_AREA             = "Artificial Intelligence and Research Methods"
PROBLEM_STATEMENT        = "How can AI improve research workflows?"
THESIS_STATEMENT         = "AI provides significant advantages..."
CONTEXT_BACKGROUND       = "Recent advances in ML..."
RESEARCH_DOMAIN          = "Computer Science & Research Methodology"
STUDY_LIMITATIONS        = "Limited to academic research..."
THESIS_RESTATEMENT       = "AI integration is transformative..."
FUTURE_RESEARCH_DIRECTIONS = "Exploring multi-modal AI..."
CLOSING_THOUGHT          = "The future lies in synergy..."
SUCCESS_METRICS          = "completion rate > 90%, satisfaction > 4.5/5..."
FINDINGS_SUMMARY         = "Analysis revealed AI-assisted methods..."
IMPLICATIONS_FOR_FIELD   = "These findings suggest paradigm shift..."
RESULTS_PRESENTATION_STYLE = "quantitative metrics with narratives"
LITERATURE_APPROACH      = (custom approach description)
```

#### Academic Style Variables (in templates)
```
FOCUS_AREA               = "computational efficiency"
METHODOLOGY_BRIEF        = "mixed-methods analysis"
KEY_FINDING              = "AI reduces time-to-insight by 40%"
FIELD_IMPLICATIONS       = "accelerating innovation"
KEYWORDS                 = "AI, research automation, methodology..."
AUDIENCE_LEVEL           = "PhD-level researchers"
ACADEMIC_RIGOR           = "Peer-reviewed publication standard"
RESEARCH_DESIGN          = "Randomized controlled trial with 500 participants"
PARTICIPANT_DESCRIPTION  = "Academic researchers with 5+ years experience"
DATA_COLLECTION_METHOD   = "Automated logging + interviews"
STUDY_DURATION           = "18 months"
RESEARCH_TOOLS           = "Python, scikit-learn, dashboard, transcription software"
STATISTICAL_METHOD       = "Multi-variate ANOVA"
CONFIDENCE_LEVEL         = "95% (p < 0.05)"
```

#### Validation Variables (in `validation_checklist`)
```
VALIDITY_CHECK_1         = "Internal consistency confirmed"
VALIDITY_CHECK_2         = "External validity verified"
VALIDITY_CHECK_3         = "Construct validity established"
REVIEW_AUTHORITY         = "Three peer reviewers"
VALIDATION_METHOD        = "Blind review with consensus"
```

#### Citation Variables (in `reference_guidelines`)
```
CITATION_STYLE           = "APA 7th Edition"
MIN_REFERENCES           = "50"
RECENCY_YEARS            = "5"
REFERENCE_BALANCE        = "80% journals, 20% texts"
AUTHORITY_LEVEL          = "h-index > 5"
```

### Variable Hierarchy Example

When rendering `research_paper_generator`:

1. **Load Main Document Variables**: All variables for the paper
2. **Render `abstract_template`**:
   - Inherits SUBJECT_AREA, PROBLEM_STATEMENT from parent
   - Adds FOCUS_AREA, METHODOLOGY_BRIEF from its own context
   - Result: merged variables available for substitution
3. **Render `methodology_template`**:
   - Inherits SUBJECT_AREA from parent
   - Adds RESEARCH_DESIGN, PARTICIPANT_DESCRIPTION from its context
   - When rendering nested `validation_checklist`:
     - Further accumulates VALIDITY_CHECK_* variables

## Tag Reference

| Tag | Purpose | Count | Examples |
|-----|---------|-------|----------|
| `template` | Reusable templates | 6 | abstract, methodology, validation |
| `academic` | Academic-focused | 5 | instructions, metadata |
| `methods` | Methodological content | 3 | instructions, methodology |
| `case_study` | Practical case studies | 3 | example_* documents |
| `practical_example` | Real-world examples | 3 | example_* documents |
| `reference` | Reference materials | 5 | foundational_*, examples |
| `foundational` | Foundational knowledge | 3 | foundational_* |
| `validation` | Validation content | 1 | validation_checklist |
| `introduction` | Introduction sections | 2 | abstract_template |
| `citations` | Citation examples | 2 | example_citation_* |

## Variable Set Strategy

For the web UI, create 6 Variable Sets:

### Set 1: "General Research Settings"
```json
{
  "PAPER_TITLE": "The Impact of AI on Modern Research",
  "AUTHOR_NAME": "Dr. Jane Smith",
  "PUBLICATION_DATE": "2026-02-28",
  "INSTITUTION": "MIT Media Lab",
  "SUBJECT_AREA": "Artificial Intelligence and Research Methods",
  "PROBLEM_STATEMENT": "How can AI improve the speed and accuracy of research workflows?",
  "THESIS_STATEMENT": "Artificial intelligence provides significant advantages...",
  "CONTEXT_BACKGROUND": "Recent advances in machine learning...",
  "RESEARCH_DOMAIN": "Computer Science & Research Methodology",
  "STUDY_LIMITATIONS": "Limited to academic research domains...",
  "THESIS_RESTATEMENT": "AI integration in research is transformative...",
  "FUTURE_RESEARCH_DIRECTIONS": "Exploring multi-modal AI applications...",
  "CLOSING_THOUGHT": "The future of research lies in synergy..."
}
```

### Set 2: "Academic Style - PhD Level"
Contains all the academic methodology variables (see Variables section)

### Set 3: "Validation Framework"
Contains VALIDITY_CHECK_* and VALIDATION_METHOD variables

### Set 4: "Citation & References"
Contains CITATION_STYLE, MIN_REFERENCES, etc.

### Set 5: "Success Metrics"
Contains SUCCESS_METRICS, FINDINGS_SUMMARY, IMPLICATIONS_FOR_FIELD

### Set 6: "Results Presentation"
Contains RESULTS_PRESENTATION_STYLE

## Features Demonstrated

✅ **Variable Substitution**: `[[VAR_NAME]]` throughout all prompts
✅ **Nested Prompt Inclusion**: `[[PROMPT: name]]` for composition
✅ **Tag-Based Injection**: `[[PROMPT_TAG: tag1, tag2]]` for dynamic lists
✅ **Variable Hierarchy**: Each prompt inherits parent variables
✅ **Metadata Organization**: _registry.json stores tags and descriptions
✅ **Complex Structure**: 14 prompts with multiple levels of nesting
✅ **Practical Example**: Realistic research paper generation use case

## Extending This Example

### Add New Domain Templates
1. Create new prompt: `domain_methodology_template.prompt`
2. Add to _registry.json with domain-specific tags
3. Reference in main orchestrator via `[[PROMPT: domain_methodology_template]]`

### Add More Case Studies
1. Create new case study: `example_domain_study.prompt`
2. Tag with `case_study` and domain-specific tags
3. Automatically included via `[[PROMPT_TAG: case_study, domain]]`

### Create Variable Set Variants
1. Create new variant set for different audience (undergrad, master's, PhD)
2. Override appropriate variables
3. Use in document-level variable set selection

## Testing

### Load and List
```bash
python -c "
from prompt_assemble.sources import FileSystemSource
source = FileSystemSource('examples/research_paper_system')
print('Prompts:', len(source.list()))
print('Tags:', source.list_by_tag('template'))
"
```

### Render Complete Paper
```bash
python examples/research_paper_system/demo.py
```

## Notes

- All prompts are in .prompt format (plain text with [[sigils]])
- _registry.json provides metadata for UI display
- Comments (#!) at start of each file explain purpose
- Tags use lowercase, hyphenated format for consistency
- Variables use UPPERCASE_WITH_UNDERSCORES convention
- Each prompt is independently usable and composable

