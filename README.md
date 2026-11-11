# XSDHub XML & XSD Validate

Validate XML files in your GitHub workflow: well-formedness on every file, and XSD 1.0 validation when you pass a schema. Errors appear as line annotations on the pull request, and the job summary links each error to a guide that explains the cause and the fix.

XML and XSD checks run on the runner with `xmllint` (libxml2). By default, no file is uploaded. You can separately choose to save invoices on XSDHub for automatic checks after official rule changes.

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

## Save invoices for future rule changes

Pro and Team accounts can save invoice XML and receive a rule difference report when a new official version takes effect. Free accounts can follow standards and receive rule alert emails at [the rule tracker](https://xsdhub.com/e-invoicing#rule-tracker).

Saving sends the matching invoice XML to your existing XSDHub account. Only turn this on for invoices you intend to keep there. XSDHub checks the stored bytes and records the rule version. You can read results and delete invoices in the rule tracker.

```yaml
      - uses: xsdhub-com/validate-action@main
        with:
          files: 'invoices/*.xml'
          save-for-rule-changes: 'true'
          invoice-standard: xrechnung
          xsdhub-api-key: ${{ secrets.XSDHUB_API_KEY }}
```

Use your existing Pro or Team API key. The optional `project-id` links the saved invoice to a project in your workspace. Saved inputs are capped at 1 MB each. Earlier runs need to be run again with this choice so XSDHub has their input for future checks.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `files` | yes | | XML files or glob patterns, one per line or space separated. `**` is supported on Linux runners. |
| `schema` | no | `''` | Path to an XSD 1.0 schema. Empty means well-formedness only. |
| `fail-on-error` | no | `true` | Fail the step when a file is invalid. |
| `save-for-rule-changes` | no | `false` | Explicitly save invoice XML on XSDHub for future rule checks. Requires Pro or Team. |
| `invoice-standard` | for saving | `''` | `en16931`, `xrechnung`, `facturx`, `ksef`, `ro` or `hr`. |
| `xsdhub-api-key` | for saving | `''` | Existing account API key, supplied as an Actions secret. |
| `project-id` | no | `''` | Existing project in your XSDHub workspace. |

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

## DORA register checks

Use `mode: dora` for one EBA DORA 4.0 register: one submission ZIP, the complete CSV table set (one glob per line), or one DNB 2026 workbook. This mode sends the register to the existing XSDHub validation API only when `allow-upload: true`. Its quotas use your existing optional API key. The default XML/XSD mode continues to run on the runner.

```yaml
- uses: xsdhub-com/validate-action@v1
  with:
    mode: dora
    files: reports/register.zip
    dora-profile: eba-4.0
    allow-upload: 'true'
    xsdhub-api-key: ${{ secrets.XSDHUB_API_KEY }}
```

For a DNB workbook, choose `dora-profile: dnb-4.0` and an `.xlsx` file. Only enable this workflow for a repository authorised to send the register. No register, source values or detailed report is written to logs or artifacts by the Action. Avoid committing private registers. The summary contains counts and a link to the browser validator.

The API and browser use the same parser and key/reference checks. Limits: 2 MiB of input, 1,000 rows per table and a 15-second DORA worker timeout. Missing tables or truncated results fail the check. `checked` is 1 for the complete register request; `failed` is 0 or 1. `fail-on-error: 'false'` allows findings but never hides transport/input failures. DORA mode cannot be combined with schema validation or invoice saving.

A passing result means the implemented keys and references passed, with all 14 tables present. Correct the register, then run your authority’s filing tests for the remaining DORA rules and acceptance. For registers above these bounds, check each entity separately; streaming larger tables is tracked as the next parser extension. [Try the same check in your browser](https://xsdhub.com/standards/dora-roi).
