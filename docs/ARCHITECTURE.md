# Architecture and system flow

GitHub renders the diagrams below natively.

## 1. System flow (what runs, in order)

```mermaid
flowchart TD
    U["Student (signed-in, IAM-scoped caller)"] -->|InvokeHarness| H1

    subgraph GATE1["Layer 1-2: input gate"]
        H1["before_invocation hook<br/>Lambda, failureMode=deny"]
        H1 --> C1{"1 text-only user msg?<br/>under 2000 chars?<br/>no injection pattern?"}
        C1 -->|no| D1["DENY<br/>R4-*"]
        C1 -->|yes| GR["Bedrock ApplyGuardrail<br/>denied topics + prompt-attack"]
        GR -->|intervened or error| D2["DENY<br/>R3-GUARDRAIL / R4-GUARDRAIL-ERROR"]
    end

    GR -->|pass| AG["AgentCore managed harness<br/>model + instructions<br/>NO shell / browser / code / purchase tools"]

    AG -->|tool call| H2

    subgraph GATE2["Layer 3-5: tool gate"]
        H2["before_tool_call hook"]
        H2 --> C2{"type in allowlist?<br/>name in allowlist?<br/>args within limits.py?"}
        C2 -->|no| D3["DENY<br/>R1 / A4 / R2"]
    end

    C2 -->|yes| GW["AgentCore Gateway"]
    GW --> L["Tool Lambdas<br/>re-validate with limits.py"]
    L -->|outlier price update| CF["inline_function: confirm_action<br/>human confirmation"]
    CF --> L
    L --> DDB[("DynamoDB<br/>user key from caller identity")]
    L --> LOC["Amazon Location<br/>SearchPlaceIndexForText only"]

    AG --> OUT["Answer to student"]
    AG -. afterInvocation .-> EB["EventBridge audit trail"]
    D1 -.-> EB
    D2 -.-> EB
    D3 -.-> EB
```

## 2. One request, step by step

```mermaid
sequenceDiagram
    actor S as Student
    participant HK as Hook Lambda
    participant GD as Guardrail
    participant AG as Harness (model)
    participant GW as Gateway + tool Lambdas
    participant DB as DynamoDB
    S->>HK: "Set my calories to 700"
    HK->>GD: ApplyGuardrail(INPUT)
    GD-->>HK: NONE (allowed)
    HK-->>AG: allow
    AG->>HK: before_tool_call set_targets(700, ...)
    HK-->>AG: DENY [R2-CALORIE-FLOOR]
    AG-->>S: "I can't go below 1,400 kcal/day. Here is a plan at 1,400+."
    Note over HK,DB: The write never reaches DynamoDB. Even if the hook were bypassed, the tool Lambda re-checks the same limits.
```

## 3. Defence in depth map

| If this layer fails... | ...this one still stops it |
|---|---|
| Regex misses an obfuscated injection (known gap, stress case S10) | Guardrail prompt-attack filter, then tool gate rejects the resulting 600 kcal call |
| Unicode-obfuscated injection (S12) | Normalization before regex catches it; if not, guardrail and tool gate still apply |
| Model is talked into calling a purchase tool | Tool gate allowlist, and no such tool is attached at all |
| Tool Lambda trusts a forged user ID | It ignores user IDs in arguments and reads identity from the caller context (A1) |
| Hook is bypassed | Tool Lambdas re-validate; IAM scopes each Lambda to its own table |
| Guardrail service is down | Hook fails closed (`R4-GUARDRAIL-ERROR`) |
| Hook Lambda itself errors or times out | `failureMode: deny` in `infra/hooks.json` |