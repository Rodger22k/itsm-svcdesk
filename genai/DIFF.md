---
lab3_genai_diff:
  instrumentation: "opentelemetry-instrumentation-genai-openai==1.2b0; opentelemetry-sdk==1.45.0"
  spec_ref: "semantic-conventions@v1.41.1"
  attributes:
    - {name: gen_ai.operation.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.provider.name, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.max_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.request.temperature, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.finish_reasons, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.id, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.response.model, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.input_tokens, emitted: true, in_spec: true, stability: development}
    - {name: gen_ai.usage.output_tokens, emitted: true, in_spec: true, stability: development}
---
<!-- ai-generated: 95% - ChatGPT Codex compared the captured attributes with OpenTelemetry semantic-conventions v1.41.1 -->

# OpenTelemetry GenAI attribute diff

The instrumented call emitted ten `gen_ai.*` span attributes. All ten are defined by
`semantic-conventions@v1.41.1`, and that registry marks each one as `development`. The emitted set therefore
matches the selected specification for attribute names and stability. The trace contains request configuration,
provider and operation identity, response metadata, and input/output token usage.

The `development` status means dashboards may use these attributes for this lab, but production consumers should
still treat their names and meanings as subject to change between semantic-convention releases. A dashboard built
on them should pin the convention version or normalize renamed attributes during upgrades.
