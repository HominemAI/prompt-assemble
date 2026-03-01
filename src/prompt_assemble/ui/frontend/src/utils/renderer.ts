/**
 * TypeScript port of the Python substitute() function.
 * Handles recursive sigil-based prompt substitution with async prompt fetching.
 * Silent failures: undefined variables/prompts return empty string instead of throwing.
 */

export interface RendererOptions {
  maxDepth?: number;
  recursive?: boolean;
}

/**
 * Render a prompt template with variable substitution and nested prompt injection.
 *
 * Supports sigils:
 * - [[VAR_NAME]]: Variable substitution
 * - [[PROMPT: name]]: Inject named prompt
 * - [[PROMPT_TAG: t1, t2]]: Inject all prompts matching tags (AND)
 * - [[PROMPT_TAG:N: t1, t2]]: Inject N most recent prompts matching tags
 *
 * @param content The template text containing sigils
 * @param variables Variables to substitute (all converted to strings)
 * @param fetchPrompt Async function to fetch prompt content by name
 * @param findByTags Sync function to find prompt names matching tags (AND intersection, desc order)
 * @param options Rendering options (maxDepth, recursive)
 * @returns Promise<string> with all sigils replaced
 */
export async function renderPrompt(
  content: string,
  variables: Record<string, string>,
  fetchPrompt: (name: string) => Promise<string>,
  findByTags: (tags: string[]) => string[],
  options: RendererOptions = {},
): Promise<string> {
  const maxDepth = options.maxDepth ?? 10;
  const recursive = options.recursive ?? true;

  // Strip comments first
  let text = stripComments(content);

  let currentText = text;
  for (let depth = 0; depth < maxDepth; depth++) {
    const newText = await replaceSigils(currentText, variables, fetchPrompt, findByTags);

    // If no changes, we're done
    if (newText === currentText) {
      break;
    }

    currentText = newText;

    // If not recursive, stop after first pass
    if (!recursive) {
      break;
    }
  }

  return currentText;
}

/**
 * Strip comments from text.
 * - Single-line: #! comment
 * - Multiline: <!-- comment -->
 */
function stripComments(text: string): string {
  // Remove single-line comments (#! ...)
  text = text.replace(/#!.*?$/gm, '');

  // Remove multiline comments (<!-- ... -->)
  text = text.replace(/<!--[\s\S]*?-->/g, '');

  return text;
}

/**
 * Parse PROMPT_TAG sigil content into (limit, tags).
 *
 * Examples:
 * - "tag1, tag2" -> (null, ['tag1', 'tag2'])
 * - "3: tag1, tag2" -> (3, ['tag1', 'tag2'])
 * - "0: tag1" -> (0, ['tag1'])
 */
function parsePromptTagSigil(content: string): [number | null, string[]] {
  const trimmed = content.trim();

  if (trimmed.includes(':')) {
    const [limitStr, tagsStr] = trimmed.split(':', 1);
    const limit = parseInt(limitStr.trim(), 10);
    const tags = tagsStr
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    if (limit === 0) {
      console.warn('PROMPT_TAG with limit 0 will return empty string');
    }

    return [limit, tags];
  } else {
    const tags = trimmed
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
    return [null, tags];
  }
}

/**
 * Replace all sigils in text (one pass).
 * Uses silent failure: undefined vars/prompts return "".
 */
async function replaceSigils(
  text: string,
  variables: Record<string, string>,
  fetchPrompt: (name: string) => Promise<string>,
  findByTags: (tags: string[]) => string[],
): Promise<string> {
  // Find all sigils
  const sigilRegex = /\[\[([^\[\]]+)\]\]/g;
  const sigils: Array<{ match: string; content: string; index: number }> = [];
  let match;

  while ((match = sigilRegex.exec(text)) !== null) {
    sigils.push({
      match: match[0],
      content: match[1].trim(),
      index: match.index,
    });
  }

  // Process sigils and build replacements
  const replacements: Record<string, string> = {};

  for (const sigil of sigils) {
    if (replacements[sigil.match]) {
      continue; // Already computed
    }

    const replacement = await resolveSigil(
      sigil.content,
      variables,
      fetchPrompt,
      findByTags,
    );
    replacements[sigil.match] = replacement;
  }

  // Apply replacements
  let result = text;
  for (const [match, replacement] of Object.entries(replacements)) {
    // Use split/join for compatibility instead of replaceAll
    result = result.split(match).join(replacement);
  }

  return result;
}

/**
 * Resolve a single sigil to its replacement value.
 * Silent failure: returns "" if variable/prompt not found.
 */
async function resolveSigil(
  content: string,
  variables: Record<string, string>,
  fetchPrompt: (name: string) => Promise<string>,
  findByTags: (tags: string[]) => string[],
): Promise<string> {
  // PROMPT_TAG: sigil
  if (content.startsWith('PROMPT_TAG:')) {
    const tagsContent = content.slice(11).trim();
    const [limit, tags] = parsePromptTagSigil(tagsContent);

    if (tags.length === 0) {
      return '';
    }

    try {
      let matchingNames = findByTags(tags);

      if (limit !== null && limit >= 0) {
        matchingNames = matchingNames.slice(0, limit);
      }

      if (matchingNames.length === 0) {
        return '';
      }

      // Fetch content for each matching prompt
      const results: string[] = [];
      for (const name of matchingNames) {
        try {
          const promptContent = await fetchPrompt(name);
          results.push(promptContent);
        } catch (error) {
          // Silent failure: skip this prompt
          console.warn(`Failed to fetch prompt: ${name}`, error);
        }
      }

      return results.join('\n\n');
    } catch (error) {
      // Silent failure
      console.warn('PROMPT_TAG resolution failed:', error);
      return '';
    }
  }

  // PROMPT: sigil
  if (content.startsWith('PROMPT:')) {
    const promptName = content.slice(7).trim();

    try {
      return await fetchPrompt(promptName);
    } catch (error) {
      // Silent failure
      console.warn(`Failed to fetch prompt: ${promptName}`, error);
      return '';
    }
  }

  // Simple variable substitution
  if (content in variables) {
    return variables[content];
  }

  // Silent failure: undefined variable returns empty string
  console.warn(`Undefined variable: ${content}`);
  return '';
}
