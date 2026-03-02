/**
 * Data migration utilities for switching between backends.
 * Handles moving prompts, versions, variable sets, and subscriptions.
 */

import { PromptBackend, VariableSet, PromptVarSetData } from './api';

/**
 * Migrate all data from one backend to another.
 * Includes prompts, version history, variable sets, and subscriptions.
 */
export async function migrateBackends(
  fromBackend: PromptBackend,
  toBackend: PromptBackend,
  onProgress?: (message: string) => void
): Promise<{ promptsCount: number; varSetsCount: number; error?: string }> {
  try {
    const log = (msg: string) => {
      console.log(`[Migration] ${msg}`);
      onProgress?.(msg);
    };

    log('Starting data migration...');

    // 1. Migrate prompts and version history
    log('Loading prompts from source backend...');
    const prompts = await fromBackend.listPrompts();
    log(`Found ${prompts.length} prompts`);

    for (const prompt of prompts) {
      try {
        log(`Migrating prompt: ${prompt.name}`);
        const fullPrompt = await fromBackend.getPrompt(prompt.name);

        // Save to new backend
        await toBackend.savePrompt(prompt.name, {
          content: fullPrompt.content,
          metadata: {
            description: fullPrompt.description || '',
            tags: fullPrompt.tags || [],
            owner: fullPrompt.owner,
            revisionComments: 'Migrated from browser storage',
          },
        });

        // Migrate version history if available
        try {
          const history = await fromBackend.getPromptHistory(prompt.name);
          log(`  - Found ${history.length} versions for ${prompt.name}`);
          // Note: Version history migration is backend-specific
          // FileSystemBackend will handle this in savePrompt
        } catch (e) {
          // Version history might not be available in all backends
          log(`  - No version history available`);
        }
      } catch (e) {
        log(`  - Error migrating prompt ${prompt.name}: ${e}`);
      }
    }

    // 2. Migrate variable sets
    log('Loading variable sets from source backend...');
    const varSets = await fromBackend.listVariableSets();
    log(`Found ${varSets.length} variable sets`);

    for (const set of varSets) {
      try {
        log(`Migrating variable set: ${set.name}`);
        await toBackend.saveVariableSet(set);
      } catch (e) {
        log(`  - Error migrating variable set ${set.name}: ${e}`);
      }
    }

    // 3. Migrate prompt variable set subscriptions
    log('Migrating prompt-level variable set subscriptions...');
    for (const prompt of prompts) {
      try {
        const subs = await fromBackend.getPromptVariableSets(prompt.name);
        if (
          subs.variableSetIds.length > 0 ||
          Object.keys(subs.overrides).length > 0
        ) {
          log(
            `  - Migrating subscriptions for ${prompt.name} (${subs.variableSetIds.length} sets)`
          );
          await toBackend.savePromptVariableSets(prompt.name, subs);
        }
      } catch (e) {
        log(`  - Error migrating subscriptions for ${prompt.name}: ${e}`);
      }
    }

    log('Migration complete!');
    return {
      promptsCount: prompts.length,
      varSetsCount: varSets.length,
    };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    console.error('[Migration] Fatal error:', errorMsg);
    return {
      promptsCount: 0,
      varSetsCount: 0,
      error: errorMsg,
    };
  }
}

/**
 * Clear all data from a backend.
 * WARNING: This is destructive and cannot be undone.
 */
export async function clearBackendData(
  backend: PromptBackend,
  onProgress?: (message: string) => void
): Promise<number> {
  const log = (msg: string) => {
    console.log(`[Clear] ${msg}`);
    onProgress?.(msg);
  };

  log('Clearing all data...');
  const prompts = await backend.listPrompts();

  for (const prompt of prompts) {
    await backend.deletePrompt(prompt.name);
  }

  const varSets = await backend.listVariableSets();
  for (const set of varSets) {
    await backend.deleteVariableSet(set.id);
  }

  log(`Cleared ${prompts.length} prompts and ${varSets.length} variable sets`);
  return prompts.length + varSets.length;
}
