# Common n8n Expression Mistakes

Complete catalog of expression errors with explanations and fixes.

---

## 1. Missing Curly Braces

**Problem**: Expression not recognized, shows as literal text

❌ **Wrong**:
```
$json.email
```

✅ **Correct**:
```
{{$json.email}}
```

**Why it fails**: n8n treats text without {{ }} as a literal string. Expressions must be wrapped to be evaluated.

**How to identify**: Field shows exact text like "$json.email" instead of actual value.

---

## 2. Webhook Body Access

**Problem**: Undefined values when accessing webhook data

❌ **Wrong**:
```
{{$json.name}}
{{$json.email}}
{{$json.message}}
```

✅ **Correct**:
```
{{$json.body.name}}
{{$json.body.email}}
{{$json.body.message}}
```

**Why it fails**: Webhook node wraps incoming data under `.body` property. The root `$json` contains headers, params, query, and body.

**Webhook structure**:
```javascript
{
  "headers": {...},
  "params": {...},
  "query": {...},
  "body": {         // User data is HERE!
    "name": "John",
    "email": "john@example.com"
  }
}
```

**How to identify**: Webhook workflow shows "undefined" for fields that are definitely being sent.

---

## 3. Spaces in Field Names

**Problem**: Syntax error or undefined value

❌ **Wrong**:
```
{{$json.first name}}
{{$json.user data.email}}
```

✅ **Correct**:
```
{{$json['first name']}}
{{$json['user data'].email}}
```

**Why it fails**: Spaces break dot notation. JavaScript interprets space as end of property name.

**How to identify**: Error message about unexpected token, or undefined when field exists.

---

## 4. Spaces in Node Names

**Problem**: Cannot access other node's data

❌ **Wrong**:
```
{{$node.HTTP Request.json.data}}
{{$node.Respond to Webhook.json}}
```

✅ **Correct**:
```
{{$node["HTTP Request"].json.data}}
{{$node["Respond to Webhook"].json}}
```

**Why it fails**: Node names are treated as object property names and need quotes when they contain spaces.

**How to identify**: Error like "Cannot read property 'Request' of undefined"

---

## 5. Incorrect Node Reference Case

**Problem**: Undefined or wrong data returned

❌ **Wrong**:
```
{{$node["http request"].json.data}}  // lowercase
{{$node["Http Request"].json.data}}  // wrong capitalization
```

✅ **Correct**:
```
{{$node["HTTP Request"].json.data}}  // exact match
```

**Why it fails**: Node names are **case-sensitive**. Must match exactly as shown in workflow.

**How to identify**: Undefined value even though node exists and has data.

---

## 6. Double Wrapping

**Problem**: Literal {{ }} appears in output

❌ **Wrong**:
```
{{{$json.field}}}
```

✅ **Correct**:
```
{{$json.field}}
```

**Why it fails**: Only one set of {{ }} is needed. Extra braces are treated as literal characters.

**How to identify**: Output shows "{{value}}" instead of just "value".

---

## 7. Array Access with Dots

**Problem**: Syntax error or undefined

❌ **Wrong**:
```
{{$json.items.0.name}}
{{$json.users.1.email}}
```

✅ **Correct**:
```
{{$json.items[0].name}}
{{$json.users[1].email}}
```

**Why it fails**: Array indices require brackets, not dots. Number after dot is invalid JavaScript.

**How to identify**: Syntax error or "Cannot read property '0' of undefined"

---

## 8. Using Expressions in Code Nodes

**Problem**: Literal string instead of value, or errors

❌ **Wrong (in Code node)**:
```javascript
const email = '{{$json.email}}';
const name = '={{$json.body.name}}';
```

✅ **Correct (in Code node)**:
```javascript
const email = $json.email;
const name = $json.body.name;

// Or using Code node API
const email = $input.item.json.email;
const allItems = $input.all();
```

**Why it fails**: Code nodes have **direct access** to data. The {{ }} syntax is for expression fields in other nodes, not for JavaScript code.

**How to identify**: Literal string "{{$json.email}}" appears in Code node output instead of actual value.

---

## 9. Missing Quotes in $node Reference

**Problem**: Syntax error

❌ **Wrong**:
```
{{$node[HTTP Request].json.data}}
```

✅ **Correct**:
```
{{$node["HTTP Request"].json.data}}
```

**Why it fails**: Node names must be quoted strings inside brackets.

**How to identify**: Syntax error "Unexpected identifier"

---

## 10. Incorrect Property Path

**Problem**: Undefined value

❌ **Wrong**:
```
{{$json.data.items.name}}       // items is an array
{{$json.user.email}}            // user doesn't exist, it's userData
```

✅ **Correct**:
```
{{$json.data.items[0].name}}    // access array element
{{$json.userData.email}}        // correct property name
```

**Why it fails**: Wrong path to data. Arrays need index, property names must be exact.

**How to identify**: Check actual data structure using expression editor preview.

---

## 11. Using = Prefix Outside JSON

**Problem**: Literal "=" appears in output

❌ **Wrong (in text field)**:
```
Email: ={{$json.email}}
```

✅ **Correct (in text field)**:
```
Email: {{$json.email}}
```

**Note**: The `=` prefix is **only** needed in JSON mode or when you want to set entire field value to expression result:

```javascript
// JSON mode (set property to expression)
{
  "email": "={{$json.body.email}}"
}

// Text mode (no = needed)
Hello {{$json.body.name}}!
```

**Why it fails**: The `=` is parsed as literal text in non-JSON contexts.

**How to identify**: Output shows "=john@example.com" instead of "john@example.com"

---

## 12. Expressions in Webhook Path

**Problem**: Path doesn't update, validation error

❌ **Wrong**:
```
path: "{{$json.user_id}}/webhook"
path: "users/={{$env.TENANT_ID}}"
```

✅ **Correct**:
```
path: "my-webhook"              // Static paths only
path: "user-webhook/:userId"    // Use dynamic URL parameters instead
```

**Why it fails**: Webhook paths must be static. Use dynamic URL parameters (`:paramName`) instead of expressions.

**How to identify**: Webhook path doesn't change or validation warns about invalid path.

---

## 13. Forgetting .json in $node Reference

**Problem**: Undefined or wrong data

❌ **Wrong**:
```
{{$node["HTTP Request"].data}}          // Missing .json
{{$node["Webhook"].body.email}}         // Missing .json
```

✅ **Correct**:
```
{{$node["HTTP Request"].json.data}}
{{$node["Webhook"].json.body.email}}
```

**Why it fails**: Node data is always under `.json` property (or `.binary` for binary data).

**How to identify**: Undefined value when you know the node has data.

---

## 14. String Concatenation Confusion

**Problem**: Attempting JavaScript template literals

❌ **Wrong**:
```
`Hello ${$json.name}!`          // Template literal syntax
"Hello " + $json.name + "!"     // String concatenation
```

✅ **Correct**:
```
Hello {{$json.name}}!           // n8n expressions auto-concatenate
```

**Why it fails**: n8n expressions don't use JavaScript template literal syntax. Adjacent text and expressions are automatically concatenated.

**How to identify**: Literal backticks or + symbols appear in output.

---

## 15. Empty Expression Brackets

**Problem**: Literal {{}} in output

❌ **Wrong**:
```
{{}}
{{ }}
```

✅ **Correct**:
```
{{$json.field}}                 // Include expression content
```

**Why it fails**: Empty expression brackets have nothing to evaluate.

**How to identify**: Literal "{{ }}" text appears in output.

---

## Quick Reference Table

| Error | Symptom | Fix |
|-------|---------|-----|
| No {{ }} | Literal text | Add {{ }} |
| Webhook data | Undefined | Add `.body` |
| Space in field | Syntax error | Use `['field name']` |
| Space in node | Undefined | Use `["Node Name"]` |
| Wrong case | Undefined | Match exact case |
| Double {{ }} | Literal braces | Remove extra {{ }} |
| .0 array | Syntax error | Use [0] |
| {{ }} in Code | Literal string | Remove {{ }} |
| No quotes in $node | Syntax error | Add quotes |
| Wrong path | Undefined | Check data structure |
| = in text | Literal = | Remove = prefix |
| Dynamic path | Doesn't work | Use static path |
| Missing .json | Undefined | Add .json |
| Template literals | Literal text | Use {{ }} |
| Empty {{ }} | Literal braces | Add expression |

---

## Debugging Process

When expression doesn't work:

1. **Check braces**: Is it wrapped in {{ }}?
2. **Check data source**: Is it webhook data? Add `.body`
3. **Check spaces**: Field or node name has spaces? Use brackets
4. **Check case**: Does node name match exactly?
5. **Check path**: Is the property path correct?
6. **Use expression editor**: Preview shows actual result
7. **Check context**: Is it a Code node? Remove {{ }}

---

**Related**: See [EXAMPLES.md](EXAMPLES.md) for working examples of correct syntax.
