---
name: react-form-validation
description: Validates React forms with Zod
---

## Description

This skill covers form validation patterns using Zod schemas.

## When to use

Use this when you need to validate user input in React forms.

## Usage

Call `validate()` to check your data.

```python
def validate(data):
    return schema.parse(data)
```

```python
validate(data, strict=True)
```