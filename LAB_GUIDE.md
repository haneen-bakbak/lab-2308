# IBM TechXchange 2026 — Lab 2308
# Build an Autonomous Risk & Compliance Agent Across the IBM Stack

---

## Notices and Disclaimers

© 2026 International Business Machines Corporation. No part of this document may be reproduced or transmitted in any form without written permission from IBM.

U.S. Government Users Restricted Rights — use, duplication or disclosure restricted by GSA ADP Schedule Contract with IBM.

IBM, the IBM logo, and ibm.com are trademarks of International Business Machines Corporation, registered in many jurisdictions worldwide. A current list of IBM trademarks is available at [www.ibm.com/legal/copytrade.shtml](https://www.ibm.com/legal/copytrade.shtml).

*IBM TechXchange 2026 / © 2026 IBM Corporation*

---

## Table of Contents

| Section | Title |
|---------|-------|
| **1** | **Introduction** |
| 1.1 | About This Lab |
| 1.2 | Key Terms & Concepts |
| 1.3 | Lab Objectives |
| **2** | **Architecture Overview** |
| **3** | **Your Lab Environments & Credentials Walkthrough** |
| 3.1 | Environment Credentials Reference Table |
| 3.2 | Step 1: Log In to IBM Cloud via TechZone App ID |
| 3.3 | Step 2: Access Your Resources & watsonx Orchestrate Instance |
| 3.4 | Step 3: Locating Your Service ID API Key for Bob |
| 3.5 | Step 4: Accessing & Logging In to OpenPages (watsonx.governance) |
| **4** | **Module 1 — Start Here: Talk to Bob** |
| 4.1 | Open IBM Bob |
| 4.2 | Bob Sets Everything Up |
| **5** | **Module 2 — Explore OpenPages** |
| 5.1 | Log In to OpenPages |
| 5.2 | Navigate the Risk Register |
| **6** | **Module 3 — Chat With Your Risk Agent** |
| 6.1 | Open the Agent in watsonx Orchestrate |
| 6.2 | Guided Test Prompts |
| 6.3 | What the Agent Is Doing |
| **7** | **Module 4 — Inspect Live Telemetry & Execution Traces** |
| 7.1 | Open the Agent Telemetry & Debug Inspector |
| 7.2 | Anatomy of an MCP Execution Trace |
| 7.3 | Try Your Own Prompts & Watch the Traces |
| **8** | **Troubleshooting** |
| **9** | **Wrap-Up & Feedback** |
| **10** | **Reference** |

---

## 1 Introduction

### 1.1 About This Lab

GRC teams spend hours reading dashboards, chasing risk owners, and manually cross-referencing registers. What if an AI agent could answer questions about your risk posture — in plain English — by talking directly to your GRC system?

In this lab you will build exactly that: an **autonomous AI risk agent** powered by **IBM watsonx Orchestrate** that communicates with **IBM OpenPages** through the **OpenPages Model Context Protocol (MCP) server**.

The best part: **you don't write a single line of code, and you don't touch a terminal.** You simply tell IBM Bob what you need, and Bob handles every bit of wiring behind the scenes. By the time you walk into the watsonx Orchestrate UI, your agent is already built, connected, and ready to chat.

---

### 1.2 Key Terms & Concepts

**IBM OpenPages**
IBM's GRC platform for managing operational risk, compliance, internal audit, and policy. Risk records (*SOXRisk*), controls (*SOXControl*), and issues (*SOXIssue*) live here.

**IBM watsonx Orchestrate (WxO)**
An agentic AI platform. Agents use natural language to plan actions and call tools. WxO handles reasoning, tool selection, and response generation automatically.

**Model Context Protocol (MCP)**
An open standard for exposing tools to AI agents. The IBM OpenPages MCP server wraps the entire OpenPages REST API as callable MCP tools — so a WxO agent can query risks, read schemas, and create records with no custom integration code.

**IBM Bob**
Your AI development assistant for this lab. Bob has a special skill loaded for Lab 2308 — when you tell him you're starting the lab and share your environment details, he silently wires up your entire agent stack, then hands you off to the WxO UI to start chatting.

---

### 1.3 Lab Objectives

By the end of this lab you will be able to:

1. Explain how MCP bridges AI agents and enterprise GRC systems.
2. Describe the schema-first query pattern that prevents AI field-name hallucination.
3. Query live OpenPages risk data through a watsonx Orchestrate agent in natural language.
4. Trace the tool calls an agent makes to satisfy a user request.

---

## 2 Architecture Overview

![Lab 2308 End-to-End Architecture Flow](assets/diagrams/architecture-overview.svg)

```
┌──────────────────────────────────────────────────────────────┐
│  Your Browser                                                 │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  watsonx Orchestrate Chat UI                          │    │
│  └─────────────────────┬────────────────────────────────┘    │
│                        │  natural language                    │
│                        ▼                                      │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  lab2308_risk_agent                                   │    │
│  │  • Reads OpenPages schema before every query          │    │
│  │  • Never guesses field names                          │    │
│  │  • Rewrites internal Docker URLs automatically        │    │
│  └─────────────────────┬────────────────────────────────┘    │
│                        │  MCP tool calls                      │
└────────────────────────┼─────────────────────────────────────┘
                         │
             ┌───────────▼──────────────────┐
             │  OpenPages MCP Server         │
             │  (running in your TechZone)   │
             │  8 tools exposed via MCP      │
             └───────────┬──────────────────┘
                         │  OpenPages REST API
                         ▼
             ┌──────────────────────────────┐
             │  IBM OpenPages GRC            │
             │  SOXRisk · SOXControl ·       │
             │  SOXIssue · Register          │
             └──────────────────────────────┘
```

**What Bob does behind the scenes (invisible to you):**
- Installs the watsonx Orchestrate ADK
- Registers your OpenPages environment as an MCP toolkit in WxO
- Builds and imports the risk agent with your environment's URLs baked in

---

## 3 Your Lab Environments & Credentials Walkthrough

This lab bridges two cloud environments:
1. **IBM watsonx Orchestrate (WxO)** — where your AI agent reasons and executes tool calls.
2. **IBM watsonx.governance / OpenPages (WxGov)** — your GRC platform containing live risks and controls.

> ⚠️ **IMPORTANT: Always Use a Private / Incognito Window**
> Use a clean **Private / Incognito browser window** for accessing IBM Cloud and watsonx Orchestrate to prevent single sign-on conflicts with personal or corporate IBM IDs.

---

### 3.1 Find Your Two Values — Instructor Screen or Printout

Your instructor will display credentials on the projected screen, or hand you a printed sheet.
**Bob needs three values**, marked with ★ below. Everything else is for logging in to the browser UIs.

```
============================================================
  IBM TechXchange 2026 — LAB-2308
  YOUR ENVIRONMENT INFO
============================================================

── PART 1 — watsonx Orchestrate (WxO) ──────────────────────

App ID Login URL
  https://cloud.ibm.com/authorize/<tenant_id>/<slug>       ← use this to log in to IBM Cloud

App ID Username
  student<N>@<tenant_id>.techzone.com

App ID Password
  <your password>

★ WXO INSTANCE URL                                         ← GIVE THIS TO BOB (Question 2)
  https://api.us-south.watson-orchestrate.cloud.ibm.com/instances/XXXX

★ SERVICE ID API KEY                                        ← GIVE THIS TO BOB (Question 3)
  AbCdEfGhIjKlMnOpQrStUvWxYz0123456789AbCd_-x

── PART 2 — OpenPages / watsonx.governance (WxGov) ─────────

watsonx.Gov Application URL
  https://wxgov-govconsole-demo-XXXX.vsi.techzone.ibm.com/openpages

★ MCP SERVER URL                                           ← GIVE THIS TO BOB (Question 1)
  https://wxgov-govconsole-demo-XXXX.vsi.techzone.ibm.com/mcp

OpenPages Login
  Username: OpenPagesAdministrator
  Password: passw0rd
```

> 💡 **The three ★ starred values are all Bob needs.** Keep the instructor screen or printed sheet visible when you start Module 1.

---

### 3.2 Step 1: Log In to IBM Cloud via TechZone App ID

![Step 1: IBM Cloud App ID Login](assets/screenshots/01-new-cloud-login.png)

1. Open a **Private/Incognito** browser window.
2. On the instructor screen or printed sheet, find the **App ID Login URL** under *PART 1*:
   ```text
   https://cloud.ibm.com/authorize/<tenant_id>/<slug>
   ```
   Paste it into your browser's address bar and press Enter.
3. On the login page, enter your credentials from the instructor screen or printed sheet:
   - **Username**: the `App ID Username` line (e.g. `student3@abc123.techzone.com`)
   - **Password**: the `App ID Password` line
4. Click **Sign in**.

---

### 3.3 Step 2: Access Your Resources & Launch watsonx Orchestrate

1. In IBM Cloud, open your **Resource List** (`https://cloud.ibm.com/resources`) and expand **AI / Machine Learning**, or click into your provisioned **watsonx Orchestrate** service instance:

![Step 2: IBM Cloud watsonx Orchestrate Service Instance Page](assets/screenshots/real-cloud-wxo-instance-detail.png)

2. On the service instance overview page (shown above), click the blue **Launch watsonx Orchestrate** button.
3. You will be authenticated directly into your live **IBM watsonx Orchestrate workspace** dashboard:

![Step 3: IBM watsonx Orchestrate Workspace Dashboard](assets/screenshots/real-wxo-dashboard-clean.png)

4. Here you can see your active agents, deployment status, and the floating **AI Chat trigger** in the bottom-left corner to converse with your agent.

---

### 3.4 Step 3: Find Your WxO Instance URL for Bob

When Bob sets up your agent in Module 1, his **second question** will be your WxO Instance URL.

1. On the instructor screen or printed sheet, find the line labelled **★ WXO INSTANCE URL** under *PART 1*:
   ```text
   https://api.us-south.watson-orchestrate.cloud.ibm.com/instances/XXXX
   ```

2. Copy the full URL including `https://`.

> **Can't find it on screen?** Go to [cloud.ibm.com/resources](https://cloud.ibm.com/resources) → **AI / Machine Learning** → click your **watsonx Orchestrate** instance → copy the **Instance URL** field.

---

### 3.5 Step 4: Find Your Service ID API Key for Bob

When Bob sets up your agent in Module 1, his **third question** will be your API key.

1. On the instructor screen or printed sheet, find the line labelled **★ SERVICE ID API KEY** under *PART 1*.
   It looks like this (your actual key will be different):
   ```text
   AbCdEfGhIjKlMnOpQrStUvWxYz0123456789AbCd_-x
   ```
   It is approximately 44 characters, containing letters, numbers, underscores, and hyphens.

2. Copy the key value — just the key itself, not the label.

3. Keep it ready to paste when Bob asks.

> **Can't find it?** In IBM Cloud, go to **Manage → Access (IAM) → Service IDs**, click your Service ID, then the **API keys** tab.

---

### 3.6 Step 5: Find Your MCP Server URL for Bob

Bob's **first question** will be your OpenPages MCP Server URL.

1. On the instructor screen or printed sheet, find the line labelled **★ MCP SERVER URL** under *PART 2*:
   ```text
   https://wxgov-govconsole-demo-XXXX.vsi.techzone.ibm.com/mcp
   ```
   The `XXXX` part is a unique ID for your TechZone reservation.

2. Copy the full URL including `https://`.

3. Keep it ready to paste when Bob asks.

> **Can't find it on screen?** Take the **watsonx.Gov Application URL** from PART 2 and change `/openpages` at the end to `/mcp`. That's your MCP Server URL.

---

### 3.7 Step 6: Log In to OpenPages (for Module 2)

![Step 5: OpenPages Login & SSL Bypass](assets/screenshots/real-openpages-login.png)

1. On the instructor screen or printed sheet, find the **watsonx.Gov Application URL** under *PART 2*:
   ```text
   https://wxgov-govconsole-demo-XXXX.vsi.techzone.ibm.com/openpages
   ```
2. Open this URL in your browser. You will see a browser security warning (TechZone uses a self-signed certificate):
   - Click **Advanced**
   - Click **Proceed to wxgov-govconsole... (unsafe)**
3. On the OpenPages login page, enter:
   - **Username**: `OpenPagesAdministrator`
   - **Password**: `passw0rd`
4. Click **Log In**.

> ⚠️ **Shared tenant reminder:** Multiple attendees share this WxO instance. Only create or modify assets named `lab2308_*`. Do not delete other attendees' agents or toolkits.

---

## 4 Module 1 — Start Here: Talk to Bob

**⏱ ~10 minutes**

This is where the magic happens. You will have a short conversation with Bob, share your environment details, and Bob will set up your entire agent stack while you watch.

### 4.1 Open IBM Bob

Open IBM Bob in your browser. Bob should already be running — your lab instructor will confirm the URL.

### 4.2 Bob Sets Everything Up

Type this to start:

```
Hi Bob! I'm in Lab 2308 at TechXchange. Can you set me up?
```

Bob will greet you and ask for two things — one at a time:

1. **Your OpenPages MCP endpoint URL**
   This is your OpenPages Application URL with `/openpages` replaced by `/mcp` (e.g. `https://wxgov-govconsole-demo-<reservation_id>.vsi.techzone.ibm.com/mcp`).

2. **Your watsonx Orchestrate API key**
   This is the **IBM Cloud Service API key** on your own TechZone reservation page (watsonx environment section). Bob works out your own watsonx Orchestrate instance from it — you don't need to find an instance URL.

> ⚠️ Always use the values from **your own** reservation. Bob never uses a shared key, instance or OpenPages server.

Once you confirm your details, Bob will say something like *"Give me a moment while I wire everything up..."* — and then silently:
- Connects to your WxO instance
- Registers an OpenPages MCP toolkit pointing at your TechZone environment
- Builds and imports your personalised risk agent

When Bob says **"🎉 You're all set!"**, your agent is live. Move on to Module 2.

> **If Bob asks you to run a single terminal command:** This only happens if one step needs a quick manual assist. Copy and paste the command exactly as Bob gives it, run it, then tell Bob "done" and he'll continue.

---

## 5 Module 2 — Explore OpenPages

**⏱ ~10 minutes**

Before chatting with the agent, spend a few minutes in the source system it will be querying.

### 5.1 Log In to OpenPages

1. Open your OpenPages URL (the one provided by your instructor — ending in `/openpages`).
2. Log in with the credentials provided (*Ask your lab instructors for credentials*).
3. Accept the browser security warning for the self-signed certificate (click **Advanced → Proceed**).

### 5.2 Navigate the Risk Register

![OpenPages Navigation Menu](assets/screenshots/real-openpages-nav-menu.png)

1. In the top-left corner, click the **Navigation Menu** (hamburger icon, shown above).
2. In the search box or categories, locate the Risk register under **Assessments** or **Organization**.
3. Notice the **Resource ID** format (e.g. `I01-RSK-01-01`). This is how the agent references individual risks.
4. Click into any risk record and look at the field names — notice they use prefixes like `OPSS-Rsk:Status`, `OPSS-Rsk:RiskLevel`. Your agent reads the schema at runtime to get these exact names — it never guesses.

---

## 6 Module 3 — Chat With Your Risk Agent

**⏱ ~25 minutes**

### 6.1 Open the Chat and Select Your Agent

1. In the **left navigation bar**, click **Chat** (the speech bubble icon, second from the top).
   The chat drawer opens on the left side of the screen.

2. At the top of the chat drawer, click the **agent selector dropdown** — it may default to *"watsonx"* or *"AskOrchestrate"*. Select **`lab2308_risk_agent`** from the list.

3. Confirm the header shows **`lab2308_risk_agent`** before typing anything.

![lab2308_risk_agent in the Build & Run inventory](assets/screenshots/06-real-wxo-inventory-search-lab2308.png)

> ⚠️ **Make sure the dropdown says `lab2308_risk_agent`.** If it says *AskOrchestrate* or *watsonx*, it has no OpenPages tools and cannot answer your prompts — switch it before sending anything.
>
> ⚠️ **Traces are only recorded for the Live agent.** Bob already deployed it live. If traces are missing in Module 4, tell Bob: *"re-deploy my agent"*.

---

### 6.2 The Scenario: Find the Gap, Log the Risk, Link the Control

You are a risk analyst at a financial services firm. Every control in this environment is sitting at **"Awaiting Assessment"** — meaning no risk category has confirmed coverage. Your job:

1. **Find** which risk category is most exposed
2. **Log** a new risk in OpenPages to capture the gap
3. **Link** an existing control to the new risk to begin closing it

Work through the four prompts below in order.

---

#### Prompt 1 — Find the compliance gap

```
Which of our risk categories have controls that are still awaiting assessment?
Show me a breakdown by category with counts.
```

**What the agent does:**
- Reads the SOXRisk and SOXControl schemas (schema-first, every time)
- Queries all controls and checks their `OPSS-Ctl:Status` field
- Groups by risk category and counts unassessed controls per category

**What you'll see:** A markdown table of risk categories alongside how many controls are still "Awaiting Assessment" — every single one, which is your gap.

---

#### Prompt 2 — Explain the Gap

```
Explain the gap briefly.
```

**What the agent does:**
- Uses the data already retrieved in Prompt 1
- Identifies the top risk category by volume and notes the control assessment backlog

**What you'll see:** A short plain-English summary — which category is most exposed and how many controls are awaiting assessment.

---

#### Prompt 3 — Log a new risk for the gap

```
Log a new risk called "Unassessed Control Coverage — Client Products" in the
"Clients, Products and Business Practices" category. Add a description that
explains the compliance gap we just found.
```

**What the agent does:**
- Calls `openpages_upsert_object` with the correct field names from the schema
- Places the risk under the Retail Banking business entity
- Returns the new Resource ID and a clickable link

**What you'll see:**
```
✅ Created: Unassessed Control Coverage — Client Products (Resource ID: XXXXX)
View in OpenPages: https://wxgov-govconsole-demo-<reservation_id>.vsi.techzone.ibm.com/...
```

> **Verify it live:** Click the link — you'll land directly on the new record in OpenPages. It's real data in the system.

---

#### Prompt 4 — Link a control to close the loop

```
Find a control related to client products and link it to the risk we just created.
```

**What the agent does:**
- Queries SOXControl records and picks a relevant one
- Calls `openpages_associate_objects` to create a Parent/Child relationship
- Returns the linked control name and a verification link

**What you'll see:**
```
✅ Linked: CTL-04-03-03-01 → Unassessed Control Coverage — Client Products
View control in OpenPages: https://wxgov-govconsole-demo-<reservation_id>.vsi.techzone.ibm.com/...
```

> **Verify it live:** Open the new risk record in OpenPages → **Controls** tab. The linked control appears there.

---

### 6.3 What the Agent Is Doing

Every response follows this sequence — invisible to you, but critical to why it works reliably:

```
Your message
    │
    ▼
1. get_resource("openpages://catalog/object_types")  ← What types exist?
    │
    ▼
2. get_resource("openpages://schema/SOXRisk")         ← What fields does this type have?
    │
    ▼
3. execute_openpages_query(SELECT confirmed fields…)  ← Query with verified field names only
    │
    ▼
4. Rewrite any internal opapp:10108 URLs             ← Clean up for display
    │
    ▼
5. Format and respond
```

This **schema-first pattern** is what separates a reliable enterprise AI agent from one that occasionally invents field names and returns errors. The schema check costs one extra tool call but eliminates an entire class of AI failure.

---

## 7 Module 4 — Inspect Live Telemetry & Execution Traces

**⏱ ~15 minutes**

In enterprise AI systems, observing *why* an agent made a decision and *how* it retrieved external data is critical for compliance and trust. watsonx Orchestrate captures every tool call, reasoning step, and response in a live trace you can inspect after each conversation.

![lab2308_risk_agent selected in AgentOps Observability](assets/screenshots/07-real-wxo-agent-selected.png)

---

### 7.1 Open AgentOps Observability

1. In the **left navigation bar**, scroll down to the **AGENTOPS** section and click **Observability**.
2. On the Observability page, find and click **`lab2308_risk_agent`** in the agent list.
3. Click the **Conversations** tab to see every conversation the agent has had.
4. Find your conversation and click **Debug** on the right side of that row.
5. You will land on a **node / tree diagram** showing every step the agent took. Click any node to see the full input and output for that step — exact queries sent, raw JSON responses from OpenPages, and the model's reasoning.

---

### 7.2 Anatomy of an MCP Execution Trace

Each interaction in the trace inspector is broken down into structured execution spans:

| Span Type | Component | What It Reveals in the Trace |
|---|---|---|
| **TOOL (Schema Discovery)** | `openpages_get_resource` | The exact URI (`openpages://schema/SOXControl`) requested to introspect object fields before generating queries. |
| **TOOL (Data Query)** | `execute_openpages_query` | The exact SQL/REST query payload sent over MCP, execution duration (ms), HTTP status (200 OK), and row count. |
| **TOOL (Write / Association)** | `openpages_upsert_object` | The mutation payload sent to OpenPages, parent process ID binding, and the returned primary `resource_id`. |
| **LLM SPAN (Reasoning & Synthesis)** | `gpt-oss-120b` | ReAct reasoning steps, prompt/completion token counts, inference latency, and final response formatting. |

> 🔍 **Why This Matters:**
> Notice how the agent NEVER guessed field names like `status` or `risk_level`. The trace proves that `openpages_get_resource` was called first, ensuring field names (`OPSS-Ctl:Status`, `OPSS-Shared-Basel:Risk Category`) were 100% verified against the live OpenPages schema before the query executed.

---

### 7.3 Try Your Own Prompts & Watch the Traces

Pick at least two:

```
How many risks are currently in an Open status?
```

```
List risks that are High severity.
```

```
What controls are available in OpenPages?
```

```
Summarise the risk landscape — how many risks exist per status?
```

```
Which business entity has the most open risks?
```

For each, watch the trace. Ask yourself:
- Did the agent read the schema before querying?
- Are the field names in the query prefixed correctly (e.g. `OPSS-Rsk:Status`)?
- Do all links in the response point to your TechZone hostname?

---

## 8 Troubleshooting

**If something isn't working right, just tell Bob.** Bob has full visibility into your setup and can silently re-run any step. Example:

```
Bob, my risk agent isn't returning any results. Can you check the connection?
```

Bob will diagnose and fix it quietly.

---

**Common issues and what to say to Bob:**

| What you see | What to tell Bob |
|---|---|
| Agent says "I don't have access to that tool" | "Bob, my agent says it can't find the MCP tools. Can you re-register the toolkit?" |
| Responses time out | "Bob, the agent is timing out. Can you check the OpenPages endpoint?" |
| My traces are empty / missing | "Bob, please deploy my agent to live." Then open the **Live** agent and ask again. |
| Auth error / 401 | "Bob, I'm getting an authentication error. Can you refresh the connection?" |
| No risks returned | "Bob, the agent returned an empty list. My OpenPages URL is `<paste URL>`." |

---

## 9 Wrap-Up & Feedback

### What You Built

✅ An AI risk agent connected live to IBM OpenPages via MCP  
✅ Schema-first query behaviour — zero field-name hallucination  
✅ Natural language interface over a real GRC system  
✅ End-to-end tracing of agent tool calls  

### What Comes Next

Today's lab covers end-to-end risk management through an AI agent. The OpenPages MCP server also supports:

- **Creating risks** — `openpages_upsert_object` with a `SOXRisk` type
- **Linking controls** — `openpages_associate_objects`
- **Multi-step workflows** — e.g. "Create a risk, find the most relevant control, and link it"
- **Multi-agent patterns** — a parent orchestrator routing between a risk agent, an audit agent, and a policy agent

Future iterations of this lab cover write operations and multi-agent GRC workflows.

### Feedback

Please scan the QR code at your station or use the link your instructor provides to complete the session survey. Your feedback directly shapes future TechXchange lab content.

---

## 10 Reference

### Quick Links

| Resource | URL |
|---|---|
| WxO UI | Open from your IBM Cloud resource list → **Launch watsonx Orchestrate** (`https://<region>.watson-orchestrate.cloud.ibm.com`) |
| OpenPages UI | Your TechZone URL + `/openpages` |
| OpenPages 9.0 Docs | `https://www.ibm.com/docs/en/openpages/9.0.0` |
| OpenPages MCP GitHub | `https://github.com/IBM/ibm-openpages-mcp-server` |
| WxO Docs | `https://www.ibm.com/docs/en/watsonx-orchestrate` |

### MCP Tools on Your Agent

| Tool | What it does |
|---|---|
| `execute_openpages_query` | Runs SQL-style queries against OpenPages objects |
| `get_resource` | Fetches a schema or catalog resource (e.g. `openpages://schema/SOXRisk`) |
| `list_resources` | Lists all available MCP resource URIs |
| `openpages_upsert_object` | Creates or updates a GRC object |
| `openpages_associate_objects` | Links two objects (e.g. Control → Risk) |
| `openpages_dissociate_objects` | Removes a link between two objects |
| `openpages_delete_object` | Deletes a GRC object |
| `echo` | Tests MCP connectivity |

### OpenPages Object Types

| Type | Purpose | Key Fields |
|---|---|---|
| `SOXRisk` | Risk records | `OPSS-Rsk:Status`, `OPSS-Rsk:RiskLevel`, `OPSS-Rsk:Owner` |
| `SOXControl` | Control records | `OPSS-Ctl:Status`, `OPSS-Ctl:ControlType` |
| `SOXIssue` | Issue / finding records | `OPSS-Iss:Status`, `OPSS-Iss:Severity` |
| `Register` | Risk register (parent container) | `Name`, `Description` |

---

*IBM TechXchange 2026 / Lab 2308 / © 2026 IBM Corporation*
