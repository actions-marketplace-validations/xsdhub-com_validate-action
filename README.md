# XSDHub XML & XSD Validate

Validate XML files in your GitHub workflow: well-formedness on every file, and XSD 1.0 validation when you pass a schema. Errors appear as line annotations on the pull request, and the job summary links each error to a guide that explains the cause and the fix.

Everything runs on the runner with `xmllint` (libxml2). No file is uploaded anywhere.

## Usage

```yaml
name: Validate XML
on: [push, pull_request]
jobs:
  xml:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: xsdhub-com/validate-action@v1
        with:
          files: |
            config/**/*.xml
            feeds/*.xml
          schema: schemas/feed.xsd
```

Well-formedness only (no schema):

```yaml
      - uses: xsdhub-com/validate-action@v1
        with:
          files: '**/*.xml'
```

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `files` | yes | | XML files or glob patterns, one per line or space separated. `**` is supported on Linux runners. |
| `schema` | no | `''` | Path to an XSD 1.0 schema. Empty means well-formedness only. |
| `fail-on-error` | no | `true` | Fail the step when a file is invalid. |

## Outputs

| Output | Description |
|---|---|
| `checked` | Number of files checked |
| `failed` | Number of files that failed |

## What you get on a failure

```
order.xml:4  Element 'total': This element is not expected. Expected is ( date ).
             how to fix: https://xsdhub.com/learn/xsd-element-not-expected
```

Messages are libxml2's own text. Guides for the common causes: [XSDHub validation guides](https://xsdhub.com/learn).

## Limits

- XSD 1.0 only (libxml2). For XSD 1.1, Schematron, two-engine comparison or EN 16931 / XRechnung invoice rules, use [XSDHub](https://xsdhub.com/) or its [API and CLI](https://xsdhub.com/developers).
- File paths with spaces are not supported in `files`.
- Schema imports and includes must be resolvable from the runner (local paths or reachable URLs).

## License

MIT
