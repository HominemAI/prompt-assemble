"""
Basic example of prompt-assemble usage.
"""

from prompt_assemble import assemble

# Define a simple template
template = """
<system>
You are a [[PROMPT: persona]] specializing in [[DOMAIN]].
</system>

<task>
[[PROMPT: task-instructions]]
</task>

<question>
[[QUESTION]]
</question>
"""

# Define components (prompt fragments)
components = {
    "persona": "expert software architect",
    "task-instructions": "Analyze the following code and provide recommendations for improvement.",
}

# Define variables (simple substitutions)
variables = {
    "DOMAIN": "Python development",
    "QUESTION": "How can we improve this function's performance?",
}

# Assemble the prompt
result = assemble(template, components=components, variables=variables)

print(result)
