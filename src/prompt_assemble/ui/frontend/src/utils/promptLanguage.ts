import { Decoration, DecorationSet, EditorView } from '@codemirror/view';
import { Extension } from '@codemirror/state';
import { RangeSetBuilder } from '@codemirror/state';

// Create custom mark decorations for our syntax tokens
// These are read-only and don't interfere with editing
const varMark = Decoration.mark({ class: 'cm-prompt-var', readonly: false });
const componentMark = Decoration.mark({ class: 'cm-prompt-component', readonly: false });
const componentNameMark = Decoration.mark({ class: 'cm-prompt-name', readonly: false });
const tagMark = Decoration.mark({ class: 'cm-prompt-tag', readonly: false });
const tagNameMark = Decoration.mark({ class: 'cm-prompt-name', readonly: false });
const commentMark = Decoration.mark({ class: 'cm-prompt-comment', readonly: false });
const xmlTagMark = Decoration.mark({ class: 'cm-xml-tag', readonly: false });

// Plugin to highlight our custom syntax
export function promptSyntaxHighlight(): Extension {
  return EditorView.decorations.compute(['doc'], (state) => {
    const builder = new RangeSetBuilder<Decoration>();
    const text = state.doc.toString();

    // Match all tokens - collect all matches first, then sort by position
    const patterns = [
      // HTML multiline comments
      { regex: /<!--[\s\S]*?-->/g, mark: commentMark },
      { regex: /#!.*$/gm, mark: commentMark },
      { regex: /\[\[PROMPT_TAG:\d*:[^\]]*\]\]|\[\[PROMPT_TAG:[^\]]*\]\]/g, mark: tagMark },
      { regex: /\[\[PROMPT:[^\]]*\]\]/g, mark: componentMark },
      { regex: /\[\[[A-Za-z_][A-Za-z0-9_]*\]\]/g, mark: varMark },
      // Only match complete XML tags that are NOT part of our special syntax
      { regex: /<(?!--)(?!!\[)(?:\/)?([a-zA-Z_][a-zA-Z0-9_:-]*)\b[^<]*?(?:\/)?>/g, mark: xmlTagMark },
    ];

    // Collect all matches
    const matches: Array<{ from: number; to: number; mark: any }> = [];

    for (const { regex, mark } of patterns) {
      let match;
      regex.lastIndex = 0;
      while ((match = regex.exec(text)) !== null) {
        matches.push({
          from: match.index,
          to: match.index + match[0].length,
          mark,
        });
      }
    }

    // Add purple highlighting for prompt and tag names
    // PROMPT: name - highlight just "name"
    let promptMatch;
    const promptRegex = /\[\[PROMPT:\s*([^\[\]\s][^\[\]]*?)\s*\]\]/g;
    promptRegex.lastIndex = 0;
    while ((promptMatch = promptRegex.exec(text)) !== null) {
      const nameStart = promptMatch.index + promptMatch[0].indexOf(promptMatch[1]);
      const nameEnd = nameStart + promptMatch[1].length;
      matches.push({
        from: nameStart,
        to: nameEnd,
        mark: componentNameMark,
      });
    }

    // PROMPT_TAG: tags or PROMPT_TAG:N: tags - highlight just "tags"
    let tagMatch;
    const tagRegex = /\[\[PROMPT_TAG:\d*:\s*([^\[\]]+?)\s*\]\]|\[\[PROMPT_TAG:\s*([^\[\]]+?)\s*\]\]/g;
    tagRegex.lastIndex = 0;
    while ((tagMatch = tagRegex.exec(text)) !== null) {
      // Match group 1 is for PROMPT_TAG:N: format, group 2 is for PROMPT_TAG: format
      const tagContent = tagMatch[1] || tagMatch[2];
      const tagStart = tagMatch.index + tagMatch[0].indexOf(tagContent);
      const tagEnd = tagStart + tagContent.length;
      matches.push({
        from: tagStart,
        to: tagEnd,
        mark: tagNameMark,
      });
    }

    // Sort by position and add to builder
    matches.sort((a, b) => a.from - b.from);
    for (const { from, to, mark } of matches) {
      builder.add(from, to, mark);
    }

    return builder.finish();
  });
}
