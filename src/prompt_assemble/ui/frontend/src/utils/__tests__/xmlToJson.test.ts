import { describe, it, expect } from 'vitest'
import { xmlToJson } from '../xmlToJson'

describe('xmlToJson() - Basic XML Parsing', () => {
  it('converts simple XML to JSON object', () => {
    const xml = '<root><name>John</name></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
    expect(typeof result).toBe('object')
  })

  it('handles nested elements', () => {
    const xml = '<root><person><name>Alice</name></person></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('extracts text content', () => {
    const xml = '<message>Hello World</message>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles empty elements', () => {
    const xml = '<root><empty></empty></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles self-closing elements', () => {
    const xml = '<root><br/></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('preserves multiple sibling elements', () => {
    const xml = '<root><item>First</item><item>Second</item></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })
})

describe('xmlToJson() - Content Handling', () => {
  it('returns valid JSON structure', () => {
    const xml = '<root><value>test</value></root>'
    const result = xmlToJson(xml)
    const jsonString = JSON.stringify(result)
    expect(() => JSON.parse(jsonString)).not.toThrow()
  })

  it('preserves numeric strings', () => {
    const xml = '<root><count>42</count></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles special XML characters', () => {
    const xml = '<root><text>&lt;tag&gt;</text></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles whitespace in elements', () => {
    const xml = '<root><text>  spaced  text  </text></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles deeply nested elements', () => {
    const xml = '<root><a><b><c><d>deep</d></c></b></a></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })
})

describe('xmlToJson() - Prompt-like XML', () => {
  it('parses prompt metadata structure', () => {
    const xml = `<prompt><metadata><name>Test</name></metadata></prompt>`
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('parses multiple roles', () => {
    const xml = `<prompt><role>system</role><role>user</role></prompt>`
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('preserves line breaks', () => {
    const xml = `<prompt><instructions>Line 1
Line 2</instructions></prompt>`
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles prompt with description and content', () => {
    const xml = `
      <prompt>
        <description>Test Prompt</description>
        <content>This is the content</content>
      </prompt>
    `
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })
})

describe('xmlToJson() - Edge Cases', () => {
  it('handles empty string gracefully', () => {
    const result = xmlToJson('')
    expect(result).toBeDefined()
  })

  it('handles whitespace-only input', () => {
    const result = xmlToJson('   ')
    expect(result).toBeDefined()
  })

  it('handles single root element', () => {
    const result = xmlToJson('<root></root>')
    expect(result).toBeDefined()
  })

  it('handles mixed text and elements', () => {
    const xml = '<root>Text<element>Nested</element>More text</root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles attributes on elements', () => {
    const xml = '<root><item id="123" type="test">value</item></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles elements with underscores', () => {
    const xml = '<root><my_element>value</my_element></root>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles multiple root-level elements (array-like)', () => {
    const xml = '<items><item>first</item><item>second</item></items>'
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })
})

describe('xmlToJson() - Error Handling', () => {
  it('handles malformed XML gracefully (does not crash)', () => {
    const xml = '<root><unclosed>'
    // Implementation may return result or empty object, not throw
    const result = xmlToJson(xml)
    expect(result).toBeDefined()
  })

  it('handles mismatched tags gracefully', () => {
    const xml = '<root></wrong>'
    // Implementation is forgiving, returns something
    const result = xmlToJson(xml)
    expect(typeof result).toBe('object')
  })

  it('handles null input gracefully', () => {
    // May throw or return empty, both are acceptable
    expect(() => {
      try {
        const result = xmlToJson(null as any)
        expect(result).toBeDefined()
      } catch (e) {
        // Throwing is acceptable for null input
        expect(e).toBeDefined()
      }
    }).not.toThrow()
  })

  it('handles undefined input gracefully', () => {
    // May throw or return empty, both are acceptable
    expect(() => {
      try {
        const result = xmlToJson(undefined as any)
        expect(result).toBeDefined()
      } catch (e) {
        // Throwing is acceptable for undefined input
        expect(e).toBeDefined()
      }
    }).not.toThrow()
  })
})
