# InsightConnect Expression Language & String Templates Reference

Sources: [Format Query Language](https://docs.rapid7.com/insightconnect/format-query-language/) |
[Format Strings with Templates](https://docs.rapid7.com/insightconnect/format-strings-with-templates/)

Content was rephrased for compliance with licensing restrictions.

---

## 1. Format Query Language (Decisions & Filters)

Used in **Filter Steps** and **Automated Decisions** only (NOT in artifacts or plugin inputs).
Variables use double-bracket syntax: `{{[step_uuid].[field]}}`.

### Data types
- **string**: double-quoted, e.g. `"hello world"`
- **number**: integer or float
- **boolean**: `true` / `false`
- **array**: collection, e.g. `[1, 2, 3]`
- **regex**: slash-delimited, e.g. `/pattern/`
- **null**: the `null` constant

### Comparison operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `=` | Equals | `{{[uuid].[field]}} = "value"` |
| `!=` | Not equals | `{{[uuid].[field]}} != "value"` |
| `>` | Greater than | `{{[uuid].[count]}} > 5` |
| `>=` | Greater than or equals | |
| `<` | Less than | |
| `<=` | Less than or equals | |
| `=~` or `matches` | Regex matches | `{{[uuid].[field]}} =~ /pattern/` |
| `!~` | Regex not matches | |
| `contains` | Value contains | `{{[uuid].[field]}} contains "substr"` |
| `like` | Case-sensitive pattern match | `{{[uuid].[field]}} like "*a"` (ends in "a") |
| `ilike` | Case-insensitive pattern match | `{{[uuid].[field]}} ilike "a*"` |
| `starts_with` | Starts with | `{{[uuid].[field]}} starts_with "prefix"` |
| `ends_with` | Ends with | `{{[uuid].[field]}} ends_with "suffix"` |

### Logical operators
- `and` (or `AND`): `expr1 and expr2`
- `or` (or `OR`): `expr1 or expr2`
- `not` (or `NOT`): `not expr`

### Functions
- `length(var)` — length of a collection or string. Empty array = length 0.
- `is_defined(var)` — true if variable is defined, otherwise false.
- `try(expr)` — returns expr value, or null on error.
- `try(expr, error_expr)` — returns expr value, or error_expr on error.
- `try(expr, error_expr, success_expr)` — on error returns error_expr, on success returns success_expr.

### Expression AST format (in .icon JSON)

The `expression` object in `stepControlParams` uses a tree structure:

```json
{
  "type": "binary",
  "left": {"name": "uuid.field.subfield", "type": "variable"},
  "op": "=",
  "right": {"type": "literal", "value": "string value"}
}
```

- `op` values: `=`, `!=`, `>`, `>=`, `<`, `<=`, `=~`, `!~`, `contains`, `like`, `ilike`, `starts_with`, `ends_with`
- Use **single `=`** for equality (NOT `==`)
- String literals in `expressionText` are wrapped in double quotes: `= "value"`
- Logical AND/OR uses nested binary with `"op": "AND"` / `"op": "OR"`
- `is_defined` uses function form: `{"type": "function", "name": "is_defined", "args": [{"name": "uuid.field", "type": "variable"}]}`

---

## 2. String Templates (Handlebars)

Used in **Artifacts**, **plugin string inputs**, and any step that accepts string content.
Based on [Handlebars](https://handlebarsjs.com/guide).

### Variable references
- Basic: `{{[step_uuid].[field]}}` (standard InsightConnect variable syntax)
- Within Handlebars blocks: remove outer `{{}}` — a block statement already provides them.

### Conditional display (if/else)
```handlebars
{{#if [step_uuid].[wasfound]}}
The URL {{[step_uuid].[url]}} was found
{{else}}
The URL {{[step_uuid].[url]}} was not found
{{/if}}
```

### Iterate over arrays (each)
```handlebars
{{#each [step_uuid].[$outputs]}}
- {{this}}
{{/each}}
```
- `{{this}}` refers to the current array item.
- For trigger array inputs: `{{#each [trigger_uuid].[array_field]}} ... {{/each}}`

### Display JSON object content
Print all key/value pairs:
```handlebars
{{#each [step_uuid].[object_field]}}
{{@key}}: {{this}}
{{/each}}
```

Print specific keys:
```handlebars
{{#with [step_uuid].[object_field]}}
Name: {{name}}
Status: {{status}}
{{/with}}
```

### String comparison (if equals)
```handlebars
{{#if (eq [step_uuid].[field] "expected_value")}}
Content when matched
{{/if}}
```
- Strings in double quotes, integers without quotes.

### Nested objects/arrays
```handlebars
{{#each [step_uuid].[parent_array]}}
  {{#each nested_array}}
    {{this}}
  {{/each}}
{{/each}}
```

### Time helpers
- `{{now}}` — current time in RFC 3339 format.
- `{{time_format [step_uuid].[time_field] "format"}}` — reformat a time value.

### Length helper
- `{{length [step_uuid].[array_field]}}` — item count for arrays, character count for strings.

### Whitespace control
Add `~` to suppress newlines from block statements:
```handlebars
{{~#if condition}}content{{/if}}
```

---

## Key rules for the generator

1. **Expressions** (automated_decision, filter): Use the Format Query Language operators above. Single `=` for equality. String literals in `expressionText` must be double-quoted.
2. **Artifacts and string fields**: Use Handlebars syntax for conditional display, iteration, and formatting. Plain `{{[uuid].[field]}}` references work everywhere.
3. **`expressionText`** is the human-readable display form; the `expression` object is the AST the platform evaluates. Both must be present and consistent.
4. The `expression` AST `op` field accepts: `=`, `!=`, `>`, `>=`, `<`, `<=`, `=~`, `!~`, `contains`, `like`, `ilike`, `starts_with`, `ends_with`, `AND`, `OR`.
