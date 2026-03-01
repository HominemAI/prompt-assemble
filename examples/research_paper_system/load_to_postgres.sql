-- PostgreSQL script to load the Research Paper Generator example into the database
-- This script assumes the database schema is already created by DatabaseSource._ensure_schema()
--
-- Usage:
--   psql -U postgres -d prompts -f load_to_postgres.sql
--
-- Or with environment variables:
--   psql -h $DB_HOSTNAME -U $DB_USERNAME -d $DB_DATABASE -f load_to_postgres.sql

-- ============================================================================
-- PART 1: INSERT PROMPTS
-- ============================================================================

INSERT INTO prompts (name, content, created_at, updated_at) VALUES
  ('research_paper_generator', '#! Research Paper Generator - Complete System
#! This prompt demonstrates variable hierarchy, nested prompts, and tag-based injection

<paper>
  <metadata>
    <title>[[PAPER_TITLE]]</title>
    <author>[[AUTHOR_NAME]]</author>
    <date>[[PUBLICATION_DATE]]</date>
    <institution>[[INSTITUTION]]</institution>
  </metadata>

  <abstract>
[[PROMPT: abstract_template]]
  </abstract>

  <introduction>
    <context>[[CONTEXT_BACKGROUND]]</context>
    <problem_statement>[[PROBLEM_STATEMENT]]</problem_statement>
    <thesis>[[THESIS_STATEMENT]]</thesis>
    <instructions>
[[PROMPT: research_instructions]]
    </instructions>
  </introduction>

  <literature_review>
    <title>Literature Review: [[SUBJECT_AREA]]</title>
    <approach>[[LITERATURE_APPROACH]]</approach>
    <key_concepts>
[[PROMPT_TAG: reference, foundational]]
    </key_concepts>
  </literature_review>

  <methodology>
[[PROMPT: methodology_template]]
  </methodology>

  <results>
    <domain>[[RESEARCH_DOMAIN]]</domain>
    <metrics>[[SUCCESS_METRICS]]</metrics>
    <results_approach>[[RESULTS_PRESENTATION_STYLE]]</results_approach>
  </results>

  <discussion>
    <findings_summary>[[FINDINGS_SUMMARY]]</findings_summary>
    <implications>[[IMPLICATIONS_FOR_FIELD]]</implications>
    <limitations>[[STUDY_LIMITATIONS]]</limitations>
    <examples>
[[PROMPT_TAG: 3: case_study, practical_example]]
    </examples>
  </discussion>

  <conclusion>
    <restatement>[[THESIS_RESTATEMENT]]</restatement>
    <future_work>[[FUTURE_RESEARCH_DIRECTIONS]]</future_work>
    <closing>[[CLOSING_THOUGHT]]</closing>
  </conclusion>

  <references>
[[PROMPT: reference_guidelines]]
  </references>
</paper>', NOW(), NOW()),

  ('abstract_template', '#! Abstract Template - Used by research_paper_generator

This paper investigates [[SUBJECT_AREA]] with a focus on [[FOCUS_AREA]].
The research addresses [[PROBLEM_STATEMENT]] through [[METHODOLOGY_BRIEF]].
Our findings demonstrate that [[KEY_FINDING]]. These results have implications
for [[FIELD_IMPLICATIONS]].

Keywords: [[KEYWORDS]]', NOW(), NOW()),

  ('research_instructions', '#! Instructions for conducting research - Used by research_paper_generator

Instructions for conducting [[SUBJECT_AREA]] research:

Structure your research according to these principles:

1. Define [[PROBLEM_STATEMENT]] clearly in your introduction
2. Review relevant [[SUBJECT_AREA]] literature (see: Literature Review section)
3. Employ [[METHODOLOGY_BRIEF]] methodology in your approach
4. Measure success using these metrics: [[SUCCESS_METRICS]]
5. Report findings with [[RESULTS_PRESENTATION_STYLE]]

Audience Level: [[AUDIENCE_LEVEL]]
Academic Rigor Standard: [[ACADEMIC_RIGOR]]

These guidelines ensure consistency and academic quality across all sections.', NOW(), NOW()),

  ('methodology_template', '#! Methodology Template - Used by research_paper_generator

<methodology>
  <approach>[[METHODOLOGY_BRIEF]]</approach>

  <design>[[RESEARCH_DESIGN]]</design>

  <participants>[[PARTICIPANT_DESCRIPTION]]</participants>

  <data_collection>
    <method>[[DATA_COLLECTION_METHOD]]</method>
    <duration>[[STUDY_DURATION]]</duration>
    <tools>[[RESEARCH_TOOLS]]</tools>
  </data_collection>

  <analysis>
    <statistical_method>[[STATISTICAL_METHOD]]</statistical_method>
    <confidence_level>[[CONFIDENCE_LEVEL]]</confidence_level>
  </analysis>

  <validation>
[[PROMPT: validation_checklist]]
  </validation>
</methodology>', NOW(), NOW()),

  ('validation_checklist', '#! Validation Checklist - Used by methodology_template

Validation Checklist for [[SUBJECT_AREA]]:

☐ [[VALIDITY_CHECK_1]]
☐ [[VALIDITY_CHECK_2]]
☐ [[VALIDITY_CHECK_3]]
☐ Reviewed by: [[REVIEW_AUTHORITY]]
☐ Validation Method: [[VALIDATION_METHOD]]

All items must be checked before final submission.', NOW(), NOW()),

  ('reference_guidelines', '#! Reference Guidelines - Used by research_paper_generator

Reference Guidelines for [[SUBJECT_AREA]]

All references must follow [[CITATION_STYLE]] format.

Citation Standards:
- Minimum [[MIN_REFERENCES]] references required for [[SUBJECT_AREA]]
- Preference for sources from last [[RECENCY_YEARS]] years
- Balance of [[REFERENCE_BALANCE]] sources
- Authority Level Required: [[AUTHORITY_LEVEL]]

Example citations in [[SUBJECT_AREA]]:
[[PROMPT_TAG: reference, example]]

Ensure all citations are complete with authors, dates, and URLs where applicable.', NOW(), NOW()),

  ('example_ai_research', '#! Case Study: AI in Modern Research

<case_study>
  <title>AI-Assisted Research Acceleration in Computer Science</title>

  <context>
  A major research university integrated AI tools into their computer science department workflow. Researchers used machine learning models to help analyze large datasets and generate preliminary hypotheses.
  </context>

  <results>
  - Time to initial analysis: reduced from 4 weeks to 2 weeks (50% reduction)
  - Hypothesis quality: improved by 35% (validated against expert judgment)
  - Number of variables examined: increased from 50 to 300+ (maintaining accuracy)
  - Publication timeline: accelerated by 6 months on average
  </results>

  <lessons_learned>
  1. AI tools are most effective when combined with human expert review
  2. Data quality is critical - garbage in, garbage out still applies
  3. Researchers need training to effectively utilize AI capabilities
  4. Integration takes 2-3 months for full adoption in established labs
  </lessons_learned>

  <key_insight>
  AI should augment, not replace, human research judgment. The most successful implementations paired AI efficiency with human oversight.
  </key_insight>
</case_study>', NOW(), NOW()),

  ('example_biomedical_study', '#! Case Study: AI in Biomedical Research

<case_study>
  <title>AI-Enhanced Drug Discovery and Protein Analysis</title>

  <context>
  A biomedical research institute used AI to accelerate protein structure prediction and drug candidate screening. Instead of traditional manual analysis, they employed neural networks trained on known protein structures.
  </context>

  <results>
  - Protein structure predictions: accuracy improved from 75% to 92%
  - Drug candidate screening: processed 10,000+ compounds in 2 weeks (vs 6 months traditionally)
  - False positives: reduced by 40% through ensemble methods
  - Cost per successful candidate: reduced by 65%
  </results>

  <challenges_addressed>
  1. Limited training data in some disease areas - solved with transfer learning
  2. Regulatory compliance requirements - implemented explainability layers
  3. Validation against wet-lab results - created hybrid validation pipeline
  </challenges_addressed>

  <impact>
  AI acceleration reduced time-to-clinic by an estimated 2-3 years for new drug candidates, with significant cost savings and improved success rates in early-stage trials.
  </impact>
</case_study>', NOW(), NOW()),

  ('example_social_science', '#! Case Study: AI in Social Science Research

<case_study>
  <title>Natural Language Processing in Survey Data Analysis</title>

  <context>
  A psychology research group used AI to analyze open-ended survey responses from 50,000 participants about workplace stress. Manual coding would have taken 6 researchers a full year.
  </context>

  <results>
  - Thematic analysis completed in 3 weeks (vs estimated 52 weeks manual)
  - Inter-rater reliability: improved from 0.72 to 0.89 with AI + human review
  - Identified 247 distinct themes (vs ~80 with traditional methods)
  - Cost reduction: 94% savings on analysis labor
  </results>

  <methodology>
  1. AI preprocessing: cleaned and categorized responses
  2. Thematic extraction: identified common themes and sentiment
  3. Human validation: researchers reviewed and refined categories
  4. Subgroup analysis: AI performed demographic breakdowns
  </methodology>

  <findings>
  Discovered nuanced distinctions in stress factors across different organizational types, which would have been lost in purely manual analysis due to scale limitations.
  </findings>
</case_study>', NOW(), NOW()),

  ('foundational_machine_learning', '#! Foundational Concepts: Machine Learning

<foundational_concept>
  <topic>Supervised Learning Fundamentals</topic>

  <definition>
  Supervised learning is a machine learning paradigm where models learn from labeled training data to predict outputs for new inputs. Each training example includes both features (inputs) and the correct answer (label/output).
  </definition>

  <key_principles>
  1. Training Data: Must contain sufficient labeled examples representing the problem space
  2. Generalization: Model should work well on unseen data, not just memorize training data
  3. Overfitting: Risk of learning training noise instead of underlying patterns
  4. Cross-Validation: Essential technique for assessing true performance
  </key_principles>

  <common_algorithms>
  - Linear Regression: for continuous predictions
  - Logistic Regression: for binary classification
  - Decision Trees: for interpretable non-linear classification
  - Support Vector Machines: for high-dimensional classification
  - Neural Networks: for complex pattern recognition
  </common_algorithms>

  <application_in_research>
  Supervised learning is ideal for research applications where labeled training data is available, such as image classification, text categorization, or scientific measurement prediction.
  </application_in_research>
</foundational_concept>', NOW(), NOW()),

  ('foundational_statistics', '#! Foundational Concepts: Statistics

<foundational_concept>
  <topic>Statistical Hypothesis Testing</topic>

  <definition>
  Hypothesis testing is a formal statistical method to evaluate claims about a population based on sample data. It involves formulating null and alternative hypotheses, calculating test statistics, and determining statistical significance.
  </definition>

  <core_concepts>
  1. Null Hypothesis (H0): Assumes no effect or no difference exists
  2. Alternative Hypothesis (H1): Claims an effect or difference exists
  3. P-value: Probability of observing results as extreme as actual data, given H0 is true
  4. Significance Level (α): Threshold (typically 0.05) for rejecting the null hypothesis
  5. Type I Error: Rejecting true null hypothesis (false positive)
  6. Type II Error: Failing to reject false null hypothesis (false negative)
  </core_concepts>

  <common_tests>
  - t-test: Compares means of two groups
  - ANOVA: Compares means across multiple groups
  - Chi-square: Tests independence of categorical variables
  - Correlation Analysis: Measures relationship strength between variables
  - Regression: Models relationship between dependent and independent variables
  </common_tests>

  <research_importance>
  Proper hypothesis testing provides objective criteria for determining whether observed research results are statistically significant or due to random chance, ensuring reproducibility and credibility of scientific findings.
  </research_importance>
</foundational_concept>', NOW(), NOW()),

  ('foundational_research_ethics', '#! Foundational Concepts: Research Ethics

<foundational_concept>
  <topic>Research Ethics and IRB Requirements</topic>

  <definition>
  Research ethics involves principles and standards that govern the conduct of research to protect human subjects, ensure data integrity, and maintain academic integrity. Institutional Review Boards (IRBs) provide ethical oversight.
  </definition>

  <core_principles>
  1. Respect for Persons: Recognize autonomy and protect vulnerable populations
  2. Beneficence: Maximize benefits and minimize harm
  3. Justice: Fair and equitable treatment and distribution of research benefits
  4. Informed Consent: Participants must understand research procedures and risks
  5. Confidentiality: Protect participant privacy and data
  </core_principles>

  <irb_requirements>
  - Risk Assessment: Classify research as minimal, low, or high risk
  - Informed Consent Forms: Written documentation of participant understanding
  - Data Security: Protocols for storing and protecting sensitive information
  - Conflict of Interest: Disclosure of financial or personal interests
  - Adverse Event Reporting: Procedures for reporting unexpected harmful effects
  </irb_requirements>

  <special_considerations>
  - Research involving vulnerable populations requires enhanced protections
  - International research must comply with local ethical standards
  - AI and algorithmic research raises new ethical questions about bias and transparency
  - Big data research requires careful handling of privacy concerns
  </special_considerations>
</foundational_concept>', NOW(), NOW()),

  ('example_citation_ml', '#! Example Citation: Machine Learning

<citation>
  <format>APA 7th Edition</format>

  <example_citations>
  1. LeCun, Y., Bengio, Y., & Hinton, G. E. (2015). Deep learning. Nature, 521(7553), 436-444. https://doi.org/10.1038/nature14539

  2. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. Advances in Neural Information Processing Systems, 30, 5998-6008.

  3. Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep learning. MIT Press.

  4. Kingma, D. P., & Ba, J. (2014). Adam: A method for stochastic optimization. arXiv preprint arXiv:1412.6980.

  5. Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). Learning representations by back-propagating errors. Nature, 323(6088), 533-536.
  </example_citations>

  <citation_tips>
  - Include DOI when available for maximum precision
  - Conference papers are cited with venue (e.g., "Advances in Neural Information Processing Systems")
  - Preprints (arXiv) are acceptable but peer-reviewed versions are preferred
  - Ensure all author names are included for proper credit
  </citation_tips>
</citation>', NOW(), NOW()),

  ('example_citation_statistics', '#! Example Citation: Statistics

<citation>
  <format>APA 7th Edition</format>

  <example_citations>
  1. Cohen, J. (1988). Statistical power analysis for the behavioral sciences (2nd ed.). Lawrence Erlbaum Associates.

  2. Kline, R. B. (2015). Principles and practice of structural equation modeling (4th ed.). Guilford Press.

  3. Tukey, J. W. (1977). Exploratory data analysis. Addison-Wesley.

  4. Efron, B., & Tibshirani, R. J. (1993). An introduction to the bootstrap. Chapman and Hall.

  5. Wilkinson, L., & The Task Force on Statistical Inference. (1999). Statistical methods in psychology journals: Guidelines and explanations. American Psychologist, 54(8), 594-604.
  </example_citations>

  <citation_context>
  These foundational statistical references are frequently cited in methodology sections. They provide established protocols for statistical analysis and are highly credible sources for statistical methods.
  </citation_context>

  <usage_guidelines>
  - Use Cohen (1988) for power analysis and effect size discussions
  - Reference Kline (2015) for structural equation modeling details
  - Cite Tukey (1977) for exploratory data analysis approaches
  - Bootstrap methods: cite Efron & Tibshirani (1993)
  </usage_guidelines>
</citation>', NOW(), NOW())
ON CONFLICT (name) DO UPDATE SET
  content = EXCLUDED.content,
  updated_at = NOW();

-- ============================================================================
-- PART 2: INSERT PROMPT REGISTRY ENTRIES (descriptions)
-- ============================================================================

INSERT INTO prompt_registry (prompt_id, description, owner, created_at, updated_at) VALUES
  ((SELECT id FROM prompts WHERE name = 'research_paper_generator'), 'Main research paper generator that orchestrates all sections through nested prompts and tag-based injection', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'abstract_template'), 'Reusable abstract template used by research_paper_generator. Contains variable placeholders for subject, focus, and key findings.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'research_instructions'), 'Guidelines for conducting research in the specified domain. Covers structure, methodology, and quality standards.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'methodology_template'), 'Detailed methodology section template covering research design, participants, data collection, and analysis methods.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'validation_checklist'), 'Validation checklist for research methodology. Ensures all quality and validation criteria are met before submission.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'reference_guidelines'), 'Guidelines for formatting references and citations. Includes citation style requirements and authority level standards.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'example_ai_research'), 'Real-world case study of AI integration in computer science research. Demonstrates 50% time reduction and improved hypothesis quality.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'example_biomedical_study'), 'Case study of AI-enhanced drug discovery. Shows AI acceleration in protein prediction and drug candidate screening.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'example_social_science'), 'Case study of NLP in social science research. Demonstrates how AI analyzed 50,000 survey responses in 3 weeks.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'foundational_machine_learning'), 'Foundational concepts in supervised machine learning. Covers key principles, algorithms, and research applications.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'foundational_statistics'), 'Foundational statistical hypothesis testing concepts. Covers p-values, significance levels, common tests, and research importance.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'foundational_research_ethics'), 'Research ethics and IRB requirements. Covers core principles, IRB procedures, and special considerations for different research types.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'example_citation_ml'), 'Example citations in machine learning field. Shows proper APA 7th edition formatting with DOI links.', 'research-team', NOW(), NOW()),
  ((SELECT id FROM prompts WHERE name = 'example_citation_statistics'), 'Example citations in statistics field. Covers foundational statistical texts and guidelines for usage.', 'research-team', NOW(), NOW())
ON CONFLICT (prompt_id) DO UPDATE SET
  description = EXCLUDED.description,
  owner = EXCLUDED.owner,
  updated_at = NOW();

-- ============================================================================
-- PART 3: INSERT TAGS
-- ============================================================================

INSERT INTO prompt_tags (prompt_id, tag) VALUES
  ((SELECT id FROM prompts WHERE name = 'research_paper_generator'), 'template'),
  ((SELECT id FROM prompts WHERE name = 'research_paper_generator'), 'main'),
  ((SELECT id FROM prompts WHERE name = 'research_paper_generator'), 'research'),
  ((SELECT id FROM prompts WHERE name = 'research_paper_generator'), 'academic'),
  ((SELECT id FROM prompts WHERE name = 'research_paper_generator'), 'paper'),
  ((SELECT id FROM prompts WHERE name = 'abstract_template'), 'template'),
  ((SELECT id FROM prompts WHERE name = 'abstract_template'), 'academic'),
  ((SELECT id FROM prompts WHERE name = 'abstract_template'), 'introduction'),
  ((SELECT id FROM prompts WHERE name = 'abstract_template'), 'abstract'),
  ((SELECT id FROM prompts WHERE name = 'research_instructions'), 'template'),
  ((SELECT id FROM prompts WHERE name = 'research_instructions'), 'academic'),
  ((SELECT id FROM prompts WHERE name = 'research_instructions'), 'methods'),
  ((SELECT id FROM prompts WHERE name = 'research_instructions'), 'guidelines'),
  ((SELECT id FROM prompts WHERE name = 'methodology_template'), 'template'),
  ((SELECT id FROM prompts WHERE name = 'methodology_template'), 'methods'),
  ((SELECT id FROM prompts WHERE name = 'methodology_template'), 'academic'),
  ((SELECT id FROM prompts WHERE name = 'methodology_template'), 'detailed'),
  ((SELECT id FROM prompts WHERE name = 'validation_checklist'), 'template'),
  ((SELECT id FROM prompts WHERE name = 'validation_checklist'), 'validation'),
  ((SELECT id FROM prompts WHERE name = 'validation_checklist'), 'checklist'),
  ((SELECT id FROM prompts WHERE name = 'validation_checklist'), 'quality'),
  ((SELECT id FROM prompts WHERE name = 'reference_guidelines'), 'template'),
  ((SELECT id FROM prompts WHERE name = 'reference_guidelines'), 'academic'),
  ((SELECT id FROM prompts WHERE name = 'reference_guidelines'), 'references'),
  ((SELECT id FROM prompts WHERE name = 'reference_guidelines'), 'citations'),
  ((SELECT id FROM prompts WHERE name = 'example_ai_research'), 'case_study'),
  ((SELECT id FROM prompts WHERE name = 'example_ai_research'), 'practical_example'),
  ((SELECT id FROM prompts WHERE name = 'example_ai_research'), 'ai'),
  ((SELECT id FROM prompts WHERE name = 'example_ai_research'), 'computer_science'),
  ((SELECT id FROM prompts WHERE name = 'example_ai_research'), 'success_story'),
  ((SELECT id FROM prompts WHERE name = 'example_biomedical_study'), 'case_study'),
  ((SELECT id FROM prompts WHERE name = 'example_biomedical_study'), 'practical_example'),
  ((SELECT id FROM prompts WHERE name = 'example_biomedical_study'), 'biomedical'),
  ((SELECT id FROM prompts WHERE name = 'example_biomedical_study'), 'health'),
  ((SELECT id FROM prompts WHERE name = 'example_biomedical_study'), 'drug_discovery'),
  ((SELECT id FROM prompts WHERE name = 'example_social_science'), 'case_study'),
  ((SELECT id FROM prompts WHERE name = 'example_social_science'), 'practical_example'),
  ((SELECT id FROM prompts WHERE name = 'example_social_science'), 'social_science'),
  ((SELECT id FROM prompts WHERE name = 'example_social_science'), 'psychology'),
  ((SELECT id FROM prompts WHERE name = 'example_social_science'), 'nlp'),
  ((SELECT id FROM prompts WHERE name = 'foundational_machine_learning'), 'reference'),
  ((SELECT id FROM prompts WHERE name = 'foundational_machine_learning'), 'foundational'),
  ((SELECT id FROM prompts WHERE name = 'foundational_machine_learning'), 'machine_learning'),
  ((SELECT id FROM prompts WHERE name = 'foundational_machine_learning'), 'ai'),
  ((SELECT id FROM prompts WHERE name = 'foundational_machine_learning'), 'supervised_learning'),
  ((SELECT id FROM prompts WHERE name = 'foundational_statistics'), 'reference'),
  ((SELECT id FROM prompts WHERE name = 'foundational_statistics'), 'foundational'),
  ((SELECT id FROM prompts WHERE name = 'foundational_statistics'), 'statistics'),
  ((SELECT id FROM prompts WHERE name = 'foundational_statistics'), 'methodology'),
  ((SELECT id FROM prompts WHERE name = 'foundational_statistics'), 'hypothesis_testing'),
  ((SELECT id FROM prompts WHERE name = 'foundational_research_ethics'), 'reference'),
  ((SELECT id FROM prompts WHERE name = 'foundational_research_ethics'), 'foundational'),
  ((SELECT id FROM prompts WHERE name = 'foundational_research_ethics'), 'ethics'),
  ((SELECT id FROM prompts WHERE name = 'foundational_research_ethics'), 'irb'),
  ((SELECT id FROM prompts WHERE name = 'foundational_research_ethics'), 'research_integrity'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_ml'), 'reference'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_ml'), 'example'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_ml'), 'citations'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_ml'), 'machine_learning'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_ml'), 'apa'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_statistics'), 'reference'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_statistics'), 'example'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_statistics'), 'citations'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_statistics'), 'statistics'),
  ((SELECT id FROM prompts WHERE name = 'example_citation_statistics'), 'apa')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- PART 4: CREATE VARIABLE SETS
-- ============================================================================

-- Variable Set 1: General Research Settings
INSERT INTO variable_sets (id, name, created_at, updated_at) VALUES
  (gen_random_uuid(), 'General Research Settings', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Variable Set 2: Academic Style - PhD Level
INSERT INTO variable_sets (id, name, created_at, updated_at) VALUES
  (gen_random_uuid(), 'Academic Style - PhD Level', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Variable Set 3: Validation Framework
INSERT INTO variable_sets (id, name, created_at, updated_at) VALUES
  (gen_random_uuid(), 'Validation Framework', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Variable Set 4: Citation & References
INSERT INTO variable_sets (id, name, created_at, updated_at) VALUES
  (gen_random_uuid(), 'Citation & References', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Variable Set 5: Success Metrics
INSERT INTO variable_sets (id, name, created_at, updated_at) VALUES
  (gen_random_uuid(), 'Success Metrics', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- Variable Set 6: Results Presentation
INSERT INTO variable_sets (id, name, created_at, updated_at) VALUES
  (gen_random_uuid(), 'Results Presentation', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- PART 5: INSERT VARIABLES
-- ============================================================================

-- Variable Set 1: General Research Settings
INSERT INTO variable_set_variables (variable_set_id, name, value, created_at, updated_at) VALUES
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'PAPER_TITLE', 'The Impact of AI on Modern Research Methodologies', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'AUTHOR_NAME', 'Dr. Jane Smith', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'PUBLICATION_DATE', '2026-02-28', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'INSTITUTION', 'MIT Media Lab', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'SUBJECT_AREA', 'Artificial Intelligence and Research Methods', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'PROBLEM_STATEMENT', 'How can AI improve the speed and accuracy of research workflows?', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'THESIS_STATEMENT', 'Artificial intelligence provides significant advantages in automating research methodologies while maintaining academic rigor.', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'CONTEXT_BACKGROUND', 'Recent advances in machine learning have opened new possibilities for automating research tasks.', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'RESEARCH_DOMAIN', 'Computer Science & Research Methodology', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'STUDY_LIMITATIONS', 'Limited to academic research domains; may not apply to industry research.', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'THESIS_RESTATEMENT', 'AI integration in research is transformative and necessary for future academic progress.', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'FUTURE_RESEARCH_DIRECTIONS', 'Exploring multi-modal AI applications in research and developing AI-human collaborative frameworks.', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'CLOSING_THOUGHT', 'The future of research lies in synergy between human expertise and artificial intelligence.', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'), 'LITERATURE_APPROACH', 'systematic review of AI applications across research domains', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Variable Set 2: Academic Style - PhD Level
INSERT INTO variable_set_variables (variable_set_id, name, value, created_at, updated_at) VALUES
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'FOCUS_AREA', 'computational efficiency and validation frameworks', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'METHODOLOGY_BRIEF', 'mixed-methods quantitative and qualitative analysis', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'KEY_FINDING', 'AI-assisted research reduces time-to-insight by 40% without sacrificing rigor', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'FIELD_IMPLICATIONS', 'accelerating innovation across all research disciplines', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'KEYWORDS', 'artificial intelligence, research automation, methodology, academic rigor, machine learning', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'AUDIENCE_LEVEL', 'PhD-level researchers and academic professionals', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'ACADEMIC_RIGOR', 'Peer-reviewed publication standard with comprehensive statistical validation', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'RESEARCH_DESIGN', 'Randomized controlled trial with 500 participants', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'PARTICIPANT_DESCRIPTION', 'Academic researchers with 5+ years experience across diverse disciplines', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'DATA_COLLECTION_METHOD', 'Automated logging of research workflow metrics combined with semi-structured interviews', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'STUDY_DURATION', '18 months', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'RESEARCH_TOOLS', 'Python with scikit-learn, custom research tracking dashboard, interview transcription software', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'STATISTICAL_METHOD', 'Multi-variate ANOVA with post-hoc Tukey corrections', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Academic Style - PhD Level'), 'CONFIDENCE_LEVEL', '95% (p < 0.05)', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Variable Set 3: Validation Framework
INSERT INTO variable_set_variables (variable_set_id, name, value, created_at, updated_at) VALUES
  ((SELECT id FROM variable_sets WHERE name = 'Validation Framework'), 'VALIDITY_CHECK_1', 'Internal consistency confirmed (Cronbach''s α = 0.87)', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Validation Framework'), 'VALIDITY_CHECK_2', 'External validity verified through replication study', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Validation Framework'), 'VALIDITY_CHECK_3', 'Construct validity established via triangulation with independent measures', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Validation Framework'), 'REVIEW_AUTHORITY', 'Three peer reviewers from top-tier journals', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Validation Framework'), 'VALIDATION_METHOD', 'Independent blind review with consensus scoring', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Variable Set 4: Citation & References
INSERT INTO variable_set_variables (variable_set_id, name, value, created_at, updated_at) VALUES
  ((SELECT id FROM variable_sets WHERE name = 'Citation & References'), 'CITATION_STYLE', 'APA 7th Edition', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Citation & References'), 'MIN_REFERENCES', '50', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Citation & References'), 'RECENCY_YEARS', '5', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Citation & References'), 'REFERENCE_BALANCE', '80% peer-reviewed journals, 20% authoritative texts and reports', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Citation & References'), 'AUTHORITY_LEVEL', 'h-index > 5, published in top-tier venues', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Variable Set 5: Success Metrics
INSERT INTO variable_set_variables (variable_set_id, name, value, created_at, updated_at) VALUES
  ((SELECT id FROM variable_sets WHERE name = 'Success Metrics'), 'SUCCESS_METRICS', 'completion rate > 90%, user satisfaction > 4.5/5, time reduction > 35%, error rate < 2%', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Success Metrics'), 'FINDINGS_SUMMARY', 'Our analysis revealed that AI-assisted research workflows outperformed traditional methods across all measured dimensions', NOW(), NOW()),
  ((SELECT id FROM variable_sets WHERE name = 'Success Metrics'), 'IMPLICATIONS_FOR_FIELD', 'These findings suggest a paradigm shift toward human-AI collaboration in academic research', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- Variable Set 6: Results Presentation
INSERT INTO variable_set_variables (variable_set_id, name, value, created_at, updated_at) VALUES
  ((SELECT id FROM variable_sets WHERE name = 'Results Presentation'), 'RESULTS_PRESENTATION_STYLE', 'quantitative metrics with supporting qualitative narratives', NOW(), NOW())
ON CONFLICT DO NOTHING;
