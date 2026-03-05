#!/usr/bin/env python3
"""
Demo script showing how to use the Research Paper Generator example.

This demonstrates:
1. Loading prompts from filesystem
2. Finding prompts by tags
3. Rendering with variable hierarchy
"""

import sys
from pathlib import Path

# Add parent to path so we can import prompt_assemble
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from prompt_assemble.sources import FileSystemSource
from prompt_assemble import PromptProvider


def main():
    # Initialize the filesystem source
    example_dir = Path(__file__).parent
    print(f"Loading prompts from: {example_dir}")

    source = FileSystemSource(str(example_dir))
    provider = PromptProvider(source)

    # List all available prompts
    print("\n" + "=" * 60)
    print("AVAILABLE PROMPTS")
    print("=" * 60)
    all_prompts = provider.list()
    for i, prompt_name in enumerate(sorted(all_prompts), 1):
        print(f"{i:2d}. {prompt_name}")

    # Find by tags
    print("\n" + "=" * 60)
    print("PROMPTS BY TAGS")
    print("=" * 60)

    templates = provider.find_by_tag("template")
    print(f"\nPrompts tagged 'template' ({len(templates)}):")
    for name in templates:
        print(f"  - {name}")

    case_studies = provider.find_by_tag("case_study", "practical_example")
    print(f"\nPrompts tagged 'case_study' AND 'practical_example' ({len(case_studies)}):")
    for name in case_studies:
        print(f"  - {name}")

    foundational = provider.find_by_tag("reference", "foundational")
    print(f"\nPrompts tagged 'reference' AND 'foundational' ({len(foundational)}):")
    for name in foundational:
        print(f"  - {name}")

    # Example variables for rendering
    print("\n" + "=" * 60)
    print("RENDERING EXAMPLE")
    print("=" * 60)

    variables = {
        # Main paper variables
        "PAPER_TITLE": "The Impact of AI on Modern Research Methodologies",
        "AUTHOR_NAME": "Dr. Jane Smith",
        "PUBLICATION_DATE": "2026-02-28",
        "INSTITUTION": "MIT Media Lab",

        # Context and thesis
        "SUBJECT_AREA": "Artificial Intelligence and Research Methods",
        "PROBLEM_STATEMENT": "How can AI improve the speed and accuracy of research workflows?",
        "THESIS_STATEMENT": "Artificial intelligence provides significant advantages in automating research methodologies while maintaining academic rigor.",
        "CONTEXT_BACKGROUND": "Recent advances in machine learning have opened new possibilities for automating research tasks.",

        # Research specifics
        "RESEARCH_DOMAIN": "Computer Science & Research Methodology",
        "FOCUS_AREA": "computational efficiency and validation frameworks",
        "METHODOLOGY_BRIEF": "mixed-methods quantitative and qualitative analysis",
        "KEY_FINDING": "AI-assisted research reduces time-to-insight by 40% without sacrificing rigor",
        "FIELD_IMPLICATIONS": "accelerating innovation across all research disciplines",
        "KEYWORDS": "artificial intelligence, research automation, methodology, academic rigor, machine learning",

        # Academic standards
        "AUDIENCE_LEVEL": "PhD-level researchers and academic professionals",
        "ACADEMIC_RIGOR": "Peer-reviewed publication standard with comprehensive statistical validation",

        # Methodology details
        "RESEARCH_DESIGN": "Randomized controlled trial with 500 participants",
        "PARTICIPANT_DESCRIPTION": "Academic researchers with 5+ years experience across diverse disciplines",
        "DATA_COLLECTION_METHOD": "Automated logging of research workflow metrics combined with semi-structured interviews",
        "STUDY_DURATION": "18 months",
        "RESEARCH_TOOLS": "Python with scikit-learn, custom research tracking dashboard, interview transcription software",
        "STATISTICAL_METHOD": "Multi-variate ANOVA with post-hoc Tukey corrections",
        "CONFIDENCE_LEVEL": "95% (p < 0.05)",

        # Validation
        "VALIDITY_CHECK_1": "Internal consistency confirmed (Cronbach's α = 0.87)",
        "VALIDITY_CHECK_2": "External validity verified through replication study",
        "VALIDITY_CHECK_3": "Construct validity established via triangulation with independent measures",
        "REVIEW_AUTHORITY": "Three peer reviewers from top-tier journals",
        "VALIDATION_METHOD": "Independent blind review with consensus scoring",

        # Results and discussion
        "SUCCESS_METRICS": "completion rate > 90%, user satisfaction > 4.5/5, time reduction > 35%, error rate < 2%",
        "RESULTS_PRESENTATION_STYLE": "quantitative metrics with supporting qualitative narratives",
        "FINDINGS_SUMMARY": "Our analysis revealed that AI-assisted research workflows outperformed traditional methods across all measured dimensions",
        "IMPLICATIONS_FOR_FIELD": "These findings suggest a paradigm shift toward human-AI collaboration in academic research",
        "STUDY_LIMITATIONS": "Limited to academic research domains; may not apply to industry research contexts",

        # Conclusion
        "THESIS_RESTATEMENT": "AI integration in research is transformative and necessary for future academic progress",
        "FUTURE_RESEARCH_DIRECTIONS": "Exploring multi-modal AI applications in research and developing AI-human collaborative frameworks",
        "CLOSING_THOUGHT": "The future of research lies in synergy between human expertise and artificial intelligence",

        # References
        "CITATION_STYLE": "APA 7th Edition",
        "MIN_REFERENCES": "50",
        "RECENCY_YEARS": "5",
        "REFERENCE_BALANCE": "80% peer-reviewed journals, 20% authoritative texts and reports",
        "AUTHORITY_LEVEL": "h-index > 5, published in top-tier venues",

        # Literature review
        "LITERATURE_APPROACH": "systematic review of AI applications across research domains",
    }

    print("\nRendering 'research_paper_generator' with all variables...")
    print(f"Variables provided: {len(variables)}")

    try:
        # Render the main paper generator
        result = provider.render("research_paper_generator", variables=variables)

        print("\n" + "=" * 60)
        print("RENDERED OUTPUT (first 2000 chars)")
        print("=" * 60)
        print(result[:2000])
        if len(result) > 2000:
            print(f"\n... ({len(result) - 2000} more characters)")

        print("\n" + "=" * 60)
        print(f"RENDER COMPLETE - Total output length: {len(result)} characters")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during rendering: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
