# ai-generated: 95% - ChatGPT Codex drafted the instrumented LM Studio call and span export for Lab 3
import json
import os
from pathlib import Path

from openai import OpenAI
from opentelemetry import trace
from opentelemetry.exporter.otlp.json.file import FileSpanExporter
from opentelemetry.instrumentation.genai.openai import OpenAIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


OUTPUT = Path(__file__).with_name("spans.json")


def collect_genai_keys(value, result):
    if isinstance(value, dict):
        attribute_name = value.get("key")
        if isinstance(attribute_name, str) and attribute_name.startswith("gen_ai."):
            result.add(attribute_name)
        for key, nested in value.items():
            if isinstance(key, str) and key.startswith("gen_ai."):
                result.add(key)
            collect_genai_keys(nested, result)
    elif isinstance(value, list):
        for nested in value:
            collect_genai_keys(nested, result)


def main():
    if OUTPUT.exists():
        OUTPUT.unlink()

    provider = TracerProvider(
        resource=Resource.create({"service.name": "itsm-lab3-genai"})
    )
    provider.add_span_processor(SimpleSpanProcessor(FileSpanExporter(OUTPUT)))
    trace.set_tracer_provider(provider)
    OpenAIInstrumentor().instrument(tracer_provider=provider)

    base_url = os.getenv(
        "OPENAI_BASE_URL",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    api_key = os.environ["OPENAI_API_KEY"]
    model = os.getenv("OPENAI_MODEL", "gemini-3.8-flash")
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=120.0)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: OpenTelemetry Lab 3 trace complete",
            }
        ],
        temperature=0,
        max_tokens=32,
    )
    provider.force_flush()

    keys = set()
    for line in OUTPUT.read_text(encoding="utf-8").splitlines():
        if line.strip():
            collect_genai_keys(json.loads(line), keys)

    print(f"Model: {model}")
    print(f"Answer: {response.choices[0].message.content}")
    print(f"Saved: {OUTPUT}")
    print("GEN_AI_ATTRIBUTES:")
    for key in sorted(keys):
        print(key)


if __name__ == "__main__":
    main()
