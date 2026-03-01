/**
 * Convert XML-like tags in text to nested JSON structure.
 *
 * Rules:
 * - <tag>text</tag> → { "tag": "text" }
 * - Nested elements → nested objects
 * - Multiple same-tag siblings → array: [val1, val2]
 * - Mixed text+tags: text under "_text" key
 * - No XML tags found → return string as-is
 * - Output: JSON.stringify(result, null, 2)
 */

interface ParseResult {
  value: any;
  remaining: string;
}

/**
 * Convert XML-formatted text to JSON.
 * If no XML tags found, returns the original text as a string.
 * Otherwise returns a stringified JSON object.
 */
export function xmlToJson(text: string): string {
  // Check if there are any XML-like tags
  if (!/<[a-zA-Z][\w-]*[^>]*>/.test(text)) {
    return text;
  }

  try {
    const parsed = parseXml(text.trim());

    // If the result is a string (no structured XML), return as-is
    if (typeof parsed === 'string') {
      return parsed;
    }

    // Return pretty-printed JSON
    return JSON.stringify(parsed, null, 2);
  } catch (error) {
    // If parsing fails, return original text
    console.warn('XML to JSON conversion failed:', error);
    return text;
  }
}

/**
 * Parse XML from text, returning a structured object or string.
 */
function parseXml(text: string): any {
  const result = parseElements(text);

  if (result.value === null) {
    // No elements found, return text as-is
    return text.trim();
  }

  return result.value;
}

/**
 * Parse XML elements at current level.
 * Returns { value: parsed structure, remaining: unparsed text }
 */
function parseElements(text: string): ParseResult {
  const trimmed = text.trim();

  if (!trimmed) {
    return { value: null, remaining: '' };
  }

  // Match opening tag
  const openMatch = trimmed.match(/^<([a-zA-Z][\w-]*)([^>]*)>/);
  if (!openMatch) {
    return { value: null, remaining: trimmed };
  }

  const tagName = openMatch[1];
  const afterOpen = trimmed.slice(openMatch[0].length);

  // Find closing tag
  const closingTagRegex = new RegExp(`^([\\s\\S]*?)</${tagName}>`, 'm');
  const contentMatch = afterOpen.match(closingTagRegex);

  if (!contentMatch) {
    // Unclosed tag, treat as text
    return { value: null, remaining: trimmed };
  }

  const content = contentMatch[1];
  const afterClose = afterOpen.slice(contentMatch[0].length);

  // Parse content (could be text, nested elements, or mixed)
  const parsedContent = parseContent(content);

  // Check if there's more content after this element
  const nextResult = parseElements(afterClose);

  // If we have a next element at the same level, build an object/array
  if (nextResult.value !== null) {
    const result: Record<string, any> = { [tagName]: parsedContent };

    // Recursively merge next elements
    const merged = mergeElements(result, nextResult.value);
    return { value: merged, remaining: nextResult.remaining };
  }

  // Single element
  const obj: Record<string, any> = { [tagName]: parsedContent };
  return { value: obj, remaining: afterClose };
}

/**
 * Parse content inside a tag (could be text, nested elements, or mixed).
 */
function parseContent(content: string): any {
  const trimmed = content.trim();

  if (!trimmed) {
    return '';
  }

  // Check if content starts with an element
  if (trimmed.match(/^</)) {
    const result = parseElements(trimmed);

    if (result.value !== null) {
      const remaining = result.remaining.trim();

      // If there's remaining text, we have mixed content
      if (remaining) {
        return {
          _text: remaining,
          ...result.value,
        };
      }

      return result.value;
    }
  }

  // Pure text content
  return trimmed;
}

/**
 * Merge parsed elements at the same level.
 * Handles duplicate tag names by creating arrays.
 */
function mergeElements(obj1: Record<string, any>, obj2: any): any {
  if (typeof obj2 !== 'object' || obj2 === null || Array.isArray(obj2)) {
    return obj2;
  }

  const result = { ...obj1 };

  for (const [key, value] of Object.entries(obj2)) {
    if (key in result) {
      // Duplicate key: convert to array or append to array
      const existing = result[key];

      if (Array.isArray(existing)) {
        result[key] = [...existing, value];
      } else {
        result[key] = [existing, value];
      }
    } else {
      result[key] = value;
    }
  }

  return result;
}
