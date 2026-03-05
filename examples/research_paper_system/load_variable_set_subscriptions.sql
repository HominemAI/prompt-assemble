-- ============================================================================
-- Load Variable Set Subscriptions for Research Paper System
-- ============================================================================
-- This script subscribes the research paper system prompts to variable sets
-- and sets up variable overrides where appropriate.
--
-- Prerequisites:
-- - Variable sets and their variables must already be loaded
-- - Prompts must already be loaded into pambl_prompts
-- - All table names use the 'pambl_' prefix

-- ============================================================================
-- PART 1: SUBSCRIBE PROMPTS TO VARIABLE SETS
-- ============================================================================

-- research_paper_generator subscribes to all 6 variable sets
INSERT INTO pambl_variable_set_selections (id, prompt_id, variable_set_id, list_order, created_at, updated_at)
VALUES (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'research_paper_generator'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'General Research Settings'), 0, NOW(), NOW()),
       (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'research_paper_generator'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Academic Style - PhD Level'), 1, NOW(), NOW()),
       (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'research_paper_generator'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Validation Framework'), 2, NOW(), NOW()),
       (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'research_paper_generator'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Citation & References'), 3, NOW(), NOW()),
       (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'research_paper_generator'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Success Metrics'), 4, NOW(), NOW()),
       (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'research_paper_generator'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Results Presentation'), 5, NOW(),
        NOW()) ON CONFLICT DO NOTHING;

-- abstract_template subscribes to General Research Settings and Academic Style
INSERT INTO pambl_variable_set_selections (id, prompt_id, variable_set_id, list_order, created_at, updated_at)
VALUES (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'abstract_template'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'General Research Settings'), 0, NOW(), NOW()),
       (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'abstract_template'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Academic Style - PhD Level'), 1, NOW(),
        NOW()) ON CONFLICT DO NOTHING;

-- research_instructions subscribes to General Research Settings and Academic Style
INSERT INTO pambl_variable_set_selections (id, prompt_id, variable_set_id, list_order, created_at, updated_at)
VALUES (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'research_instructions'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'General Research Settings'), 0, NOW(), NOW()),
       (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'research_instructions'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Academic Style - PhD Level'), 1, NOW(),
        NOW()) ON CONFLICT DO NOTHING;

-- methodology_template subscribes to Academic Style and Validation Framework
INSERT INTO pambl_variable_set_selections (id, prompt_id, variable_set_id, list_order, created_at, updated_at)
VALUES (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'methodology_template'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Academic Style - PhD Level'), 0, NOW(), NOW()),
       (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'methodology_template'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Validation Framework'), 1, NOW(),
        NOW()) ON CONFLICT DO NOTHING;

-- validation_checklist subscribes to Validation Framework
INSERT INTO pambl_variable_set_selections (id, prompt_id, variable_set_id, list_order, created_at, updated_at)
VALUES (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'validation_checklist'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Validation Framework'), 0, NOW(),
        NOW()) ON CONFLICT DO NOTHING;

-- reference_guidelines subscribes to Citation & References
INSERT INTO pambl_variable_set_selections (id, prompt_id, variable_set_id, list_order, created_at, updated_at)
VALUES (gen_random_uuid(), (SELECT id FROM pambl_prompts WHERE name = 'reference_guidelines'),
        (SELECT id FROM pambl_variable_sets WHERE name = 'Citation & References'), 0, NOW(),
        NOW()) ON CONFLICT DO NOTHING;

-- ============================================================================
-- PART 2: VERIFY SUBSCRIPTIONS
-- ============================================================================

-- Count subscriptions by prompt
SELECT p.name,
       COUNT(vss.variable_set_id) as subscription_count
FROM pambl_prompts p
         LEFT JOIN pambl_variable_set_selections vss ON p.id = vss.prompt_id
GROUP BY p.id, p.name
ORDER BY p.name;

-- Show variable sets and their subscriptions
SELECT vs.name              as variable_set,
       COUNT(vss.prompt_id) as subscribed_prompts
FROM pambl_variable_sets vs
         LEFT JOIN pambl_variable_set_selections vss ON vs.id = vss.variable_set_id
GROUP BY vs.id, vs.name
ORDER BY vs.name;
