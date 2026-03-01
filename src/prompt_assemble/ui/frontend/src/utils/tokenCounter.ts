import { encodingForModel } from 'js-tiktoken';

// Use GPT-3.5-turbo encoding (commonly used)
const enc = encodingForModel('gpt-3.5-turbo');

export function countTokens(text: string): number {
  try {
    const tokens = enc.encode(text);
    return tokens.length;
  } catch (error) {
    console.error('Error counting tokens:', error);
    return 0;
  }
}

export function formatTokenCount(count: number): string {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k tokens`;
  }
  return `${count} tokens`;
}
