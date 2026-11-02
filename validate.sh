#!/usr/bin/env bash
# Validates XML with xmllint on the runner and reports GitHub annotations.
# No file content leaves the runner.
set -uo pipefail
shopt -s nullglob
shopt -s globstar 2>/dev/null || true  # bash 3.2 (macOS) has no globstar; ** then acts like *

GUIDES="https://xsdhub.com/learn"

if ! command -v xmllint >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq >/dev/null && sudo apt-get install -y -qq libxml2-utils >/dev/null
  elif command -v brew >/dev/null 2>&1; then
    brew install libxml2 >/dev/null
  fi
fi
if ! command -v xmllint >/dev/null 2>&1; then
  echo "::error::xmllint is not available on this runner."
  exit 1
fi

# Map an xmllint message to the XSDHub guide that explains the cause.
guide_for() {
  local m="$1"
  case "$m" in
    *"This element is not expected"*|*"is not expected"*) echo "$GUIDES/xsd-element-not-expected" ;;
    *"Opening and ending tag mismatch"*) echo "$GUIDES/xml-tag-mismatch" ;;
    *"Extra content at the end of the document"*) echo "$GUIDES/xml-extra-content-after-root" ;;
    *"Premature end of data"*) echo "$GUIDES/xml-premature-end-of-data" ;;
    *"Namespace prefix"*"not defined"*) echo "$GUIDES/xml-namespace-prefix-not-defined" ;;
    *"XML declaration allowed only at the start"*) echo "$GUIDES/xml-declaration-position" ;;
    *"Document is empty"*|*"Start tag expected"*) echo "$GUIDES/xml-empty-document" ;;
    *"EntityRef"*|*"Entity '"*"not defined"*) echo "$GUIDES/xml-escape-characters" ;;
    *"invalid Char value"*|*"Char 0x"*|*"not a valid XML character"*) echo "$GUIDES/xml-invalid-character" ;;
    *"No matching global declaration"*) echo "$GUIDES/xml-namespaces-explained" ;;
    *"[facet "*) echo "$GUIDES/xsd-facet-errors" ;;
    *"atomic type"*) echo "$GUIDES/xsd-data-types" ;;
    *"attribute"*"is required but missing"*|*"attribute is not allowed"*|*"The attribute"*"is not allowed"*) echo "$GUIDES/xsd-required-and-invalid-attributes" ;;
    *"Missing child element"*) echo "$GUIDES/xsd-minoccurs-maxoccurs" ;;
    *"key-sequence"*|*"identity-constraint"*) echo "$GUIDES/xsd-identity-constraints" ;;
    *"xsi:nil"*|*"nillable"*) echo "$GUIDES/xsd-nillable" ;;
    *"failed to load"*|*"Failed to locate"*|*"import"*|*"include"*) echo "$GUIDES/xsd-import-include-errors" ;;
    *) echo "$GUIDES/fix-xml-validation-errors" ;;
  esac
}

escape_data() {
  local s="$1"
  s="${s//'%'/'%25'}"; s="${s//$'\r'/'%0D'}"; s="${s//$'\n'/'%0A'}"
  printf '%s' "$s"
}

# Collect files from patterns (newline or space separated).
files=()
while IFS= read -r pattern; do
  [ -z "$pattern" ] && continue
  matches=( $pattern )
  if [ ${#matches[@]} -eq 0 ]; then
    echo "::warning::No files match pattern: $pattern"
  fi
  for f in "${matches[@]}"; do [ -f "$f" ] && files+=("$f"); done
done < <(printf '%s\n' "$INPUT_FILES" | tr ' ' '\n')

if [ ${#files[@]} -eq 0 ]; then
  echo "::error::No XML files found for the given patterns."
  exit 1
fi

schema_args=()
mode="well-formedness"
if [ -n "${INPUT_SCHEMA}" ]; then
  if [ ! -f "${INPUT_SCHEMA}" ]; then
    echo "::error::Schema not found: ${INPUT_SCHEMA}"
    exit 1
  fi
  schema_args=(--schema "${INPUT_SCHEMA}")
  mode="XSD (${INPUT_SCHEMA})"
fi

checked=0; failed=0
summary_rows=""
for f in "${files[@]}"; do
  checked=$((checked + 1))
  out="$(xmllint --noout ${schema_args[@]+"${schema_args[@]}"} "$f" 2>&1)"
  status=$?
  if [ $status -eq 0 ]; then
    summary_rows+="| \`$f\` | ✅ valid | |"$'\n'
    continue
  fi
  failed=$((failed + 1))
  first=""
  while IFS= read -r line; do
    # file.xml:LINE: ... error : MESSAGE
    if [[ "$line" =~ ^(.+):([0-9]+):\ (.*)$ ]]; then
      lf="${BASH_REMATCH[1]}"; ln="${BASH_REMATCH[2]}"; msg="${BASH_REMATCH[3]}"
      msg="${msg#*error : }"
      [ -z "$first" ] && first="$msg"
      guide="$(guide_for "$msg")"
      echo "::error file=${lf},line=${ln},title=XML validation::$(escape_data "$msg — how to fix: $guide")"
    fi
  done <<< "$out"
  if [ -z "$first" ]; then
    first="$(printf '%s' "$out" | head -n 1)"
    echo "::error file=${f}::$(escape_data "$first")"
  fi
  guide="$(guide_for "$first")"
  short="${first//|/\\|}"
  summary_rows+="| \`$f\` | ❌ ${short:0:160} | [fix guide]($guide) |"$'\n'
done

echo "checked=$checked" >> "${GITHUB_OUTPUT:-/dev/null}"
echo "failed=$failed" >> "${GITHUB_OUTPUT:-/dev/null}"

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "### XML validation: $((checked - failed))/$checked valid"
    echo
    echo "Mode: $mode · engine: $(xmllint --version 2>&1 | head -n 1)"
    echo
    echo "| File | Result | |"
    echo "|---|---|---|"
    printf '%s' "$summary_rows"
    echo
    echo "Checked locally on the runner; no files were uploaded. Need XSD 1.1, Schematron or EN 16931 invoice rules? [XSDHub](https://xsdhub.com/)"
  } >> "$GITHUB_STEP_SUMMARY"
fi

echo "XSDHub validate: $checked checked, $failed failed ($mode)."
if [ "$failed" -gt 0 ] && [ "${INPUT_FAIL_ON_ERROR}" = "true" ]; then
  exit 1
fi
exit 0
