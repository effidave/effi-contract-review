# **Clean Code Principles for Python**

## 1. Meaningful Names

Use descriptive, intention-revealing names for variables, functions, and classes.

```python
def calculate_total_price(items):  # Clear and descriptive
    ...

def calc(items):  # Too vague
    ...
```

* Avoid abbreviations and magic numbers; use well-named constants.
* Use `snake_case` for variables/functions, `PascalCase` for classes, and `UPPER_CASE` for constants.

---

## 2. Functions Should Be Small and Focused

* Each function should do one thing and do it well.
* Keep functions short (ideally fewer than 20 lines).
* Use early returns to reduce nesting and improve readability.

```python
def get_discount(price: float) -> float:
    if price <= 0:
        return 0.0
    return price * 0.1
```

---

## 3. Comments Explain *Why*, Not *What*

* Write comments to capture intent or reasoning, not code mechanics.
* Strive for self-documenting code via good naming.
* Use docstrings for public modules, classes, and functions.

```python
def send_email(recipient: str, subject: str, body: str) -> None:
    """Send an email message to the specified recipient."""
```

---

## 4. Consistent Formatting

* Follow PEP 8 conventions (use a formatter such as `black`, `ruff`, or `isort`).
* Maintain consistent indentation (4 spaces) and a manageable line length (79-99 characters).
* Group related functions logically and separate them with one blank line.

---

## 5. Handle Errors Gracefully

* Use exceptions for exceptional cases, not for routine control flow.
* Catch specific exceptions and provide clear handling or logging.

```python
try:
    process_file(path)
except FileNotFoundError:
    handle_missing_file(path)
```

---

## 6. Avoid Duplication

* Apply the DRY principle (Don't Repeat Yourself).
* Reuse logic through helper functions or shared utilities.
* Refactor repeated patterns into reusable abstractions.

---

## 7. Keep Classes and Modules Focused

* Give each class a single responsibility.
* Limit the number of instance variables; cohesion matters.
* Smaller modules are easier to test and maintain.

---

## 8. Write Clean Tests

* Tests should be simple, readable, and isolated.
* Use clear naming, e.g. `test_addition_returns_correct_sum`.
* Comprehensive tests should be written before any development work - they should fail until the relevant work is completed.

---

## 9. Optimize for Readability Over Cleverness

* Choose clarity over clever, condensed code.
* Avoid overly concise constructs that hinder understanding.
* Refactor complex logic into clearly named steps.

---

## 10. Refactor Continuously

* Regularly review and refine code.
* Remove dead code and outdated comments.
* Treat refactoring as part of the development cycle, not an afterthought.

---

## 11. Quick Reference

| Principle               | Description                           |
|-------------------------|---------------------------------------|
| Meaningful Names        | Names express intent clearly          |
| Small Functions         | Do one thing only                     |
| Clear Comments          | Explain why, not what                 |
| Consistent Style        | Follow PEP 8                          |
| Graceful Error Handling | Use specific exceptions               |
| No Duplication          | Reuse logic                           |
| Focused Modules         | Single responsibility                 |
| Readable Tests          | Simple and isolated                   |
| Readable Over Clever    | Clarity beats brevity                 |
| Refactor Often          | Continuous improvement                |
