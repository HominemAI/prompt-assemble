"""
Example showing recursive substitution with prompt-assemble.
"""

from prompt_assemble import assemble

# Template with nested substitutions
template = """
Task: [[TASK_DESCRIPTION]]
Focus area: [[FOCUS]]
"""

# Variables can reference other variables
# They'll be resolved in multiple passes
variables = {
    "TASK_DESCRIPTION": "Review [[CODE_TYPE]] code",
    "CODE_TYPE": "Python",
    "FOCUS": "Performance and readability",
}

# With recursive=True (default), nested sigils are resolved
result = assemble(template, variables=variables)

print("Result:")
print(result)
print()

# The nested [[CODE_TYPE]] is resolved to "Python"
# So TASK_DESCRIPTION becomes "Review Python code"
