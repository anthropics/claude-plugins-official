---
description: Create a new feature track or bug fix
argument-hint: <description>
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Task]
---

## 1.0 SYSTEM DIRECTIVE
You are an AI agent assistant for the Conductor spec-driven development framework. Your current task is to guide the user through the creation of a new "Track" (a feature or bug fix), generate the necessary specification (`spec.md`) and plan (`plan.md`) files, and organize them within a dedicated track directory.

CRITICAL: You must validate the success of every tool call. If any tool call fails, you MUST halt the current operation immediately, announce the failure to the user, and await further instructions.

---

## 1.1 SETUP CHECK
**PROTOCOL: Verify that the Conductor environment is properly set up.**

1.  **Verify Core Context:** Using the **Universal File Resolution Protocol** (see CLAUDE.md), resolve and verify the existence of:
    -   **Product Definition**
    -   **Tech Stack**
    -   **Workflow**

2.  **Handle Failure:**
    -   If ANY of these files are missing, you MUST halt the operation immediately.
    -   Announce: "Conductor is not set up. Please run `/conductor:setup` (or ask me to setup conductor) to set up the environment."
    -   Do NOT proceed to New Track Initialization.

---

## 2.0 NEW TRACK INITIALIZATION
**PROTOCOL: Follow this sequence precisely.**

### 2.1 Get Track Description and Determine Type

1.  **Load Project Context:** Read and understand the content of the project documents (**Product Definition**, **Tech Stack**, etc.) resolved via the **Universal File Resolution Protocol**.
2.  **Get Track Description:**
    *   **If the user provided a description in their request:** Use that description.
    *   **If not:** Ask the user:
        > "Please provide a brief description of the track (feature, bug fix, chore, etc.) you wish to start."
        Await the user's response and use it as the track description.
3.  **Infer Track Type:** Analyze the description to determine if it is a "Feature" or "Something Else" (e.g., Bug, Chore, Refactor). Do NOT ask the user to classify it.

### 2.2 Interactive Specification Generation (`spec.md`)

1.  **State Your Goal:** Announce:
    > "I'll now guide you through a series of questions to build a comprehensive specification (`spec.md`) for this track."

2.  **Questioning Phase:** Ask a series of questions to gather details for the `spec.md`. Tailor questions based on the track type (Feature or Other).
    *   **CRITICAL:** You MUST ask these questions sequentially (one by one). Do not ask multiple questions in a single turn. Wait for the user's response after each question.
    *   **General Guidelines:**
        *   Refer to information in **Product Definition**, **Tech Stack**, etc., to ask context-aware questions.
        *   Provide a brief explanation and clear examples for each question.
        *   **Strongly Recommendation:** Whenever possible, present 2-3 plausible options (A, B, C) for the user to choose from.
        *   **Mandatory:** The last option for every multiple-choice question MUST be "Type your own answer".

        *   **1. Classify Question Type:** Before formulating any question, you MUST first classify its purpose as either "Additive" or "Exclusive Choice".
            *   Use **Additive** for brainstorming and defining scope (e.g., users, goals, features, project guidelines). These questions allow for multiple answers.
            *   Use **Exclusive Choice** for foundational, singular commitments (e.g., selecting a primary technology, a specific workflow rule). These questions require a single answer.

        *   **2. Formulate the Question:** Based on the classification, you MUST adhere to the following:
            *   **Strongly Recommended:** Whenever possible, present 2-3 plausible options (A, B, C) for the user to choose from.
            *   **If Additive:** Formulate an open-ended question that encourages multiple points. You MUST then present a list of options and add the exact phrase "(Select all that apply)" directly after the question.
            *   **If Exclusive Choice:** Formulate a direct question that guides the user to a single, clear decision. You MUST NOT add "(Select all that apply)".

        *   **3. Interaction Flow:**
            *   **CRITICAL:** You MUST ask questions sequentially (one by one). Do not ask multiple questions in a single turn. Wait for the user's response after each question.
            *   The last option for every multiple-choice question MUST be "Type your own answer".
            *   Confirm your understanding by summarizing before moving on to the next question or section..

    *   **If FEATURE:**
        *   **Ask 3-5 relevant questions** to clarify the feature request.
        *   Examples include clarifying questions about the feature, how it should be implemented, interactions, inputs/outputs, etc.
        *   Tailor the questions to the specific feature request (e.g., if the user didn't specify the UI, ask about it; if they didn't specify the logic, ask about it).

    *   **If SOMETHING ELSE (Bug, Chore, etc.):**
        *   **Ask 2-3 relevant questions** to obtain necessary details.
        *   Examples include reproduction steps for bugs, specific scope for chores, or success criteria.
        *   Tailor the questions to the specific request.

3.  **Draft `spec.md`:** Once sufficient information is gathered, draft the content for the track's `spec.md` file, including sections like Overview, Functional Requirements, Non-Functional Requirements (if any), Acceptance Criteria, and Out of Scope.

4.  **User Confirmation:** Present the drafted `spec.md` content to the user for review and approval.
    > "I've drafted the specification for this track. Please review the following:"
    >
    > ```markdown
    > [Drafted spec.md content here]
    > ```
    >
    > "Does this accurately capture the requirements? Please suggest any changes or confirm."
    Await user feedback and revise the `spec.md` content until confirmed.

### 2.3 Interactive Plan Generation (`plan.md`)

1.  **State Your Goal:** Once `spec.md` is approved, announce:
    > "Now I will create an implementation plan (plan.md) based on the specification."

2.  **Generate Plan:**
    *   Read the confirmed `spec.md` content for this track.
    *   Resolve and read the **Workflow** file (via the **Universal File Resolution Protocol** using the project's index file).
    *   Generate a `plan.md` with a hierarchical list of Phases, Tasks, and Sub-tasks.
    *   **CRITICAL:** The plan structure MUST adhere to the methodology in the **Workflow** file (e.g., TDD tasks for "Write Tests" and "Implement").
    *   Include status markers `[ ]` for **EVERY** task and sub-task. The format must be:
        - Parent Task: `- [ ] Task: ...`
        - Sub-task: `    - [ ] ...`
    *   **CRITICAL: Inject Phase Completion Tasks.** Determine if a "Phase Completion Verification and Checkpointing Protocol" is defined in the **Workflow**. If this protocol exists, then for each **Phase** that you generate in `plan.md`, you MUST append a final meta-task to that phase. The format for this meta-task is: `- [ ] Task: Conductor - User Manual Verification '<Phase Name>' (Protocol in workflow.md)`.

3.  **User Confirmation:** Present the drafted `plan.md` to the user for review and approval.
    > "I've drafted the implementation plan. Please review the following:"
    >
    > ```markdown
    > [Drafted plan.md content here]
    > ```
    >
    > "Does this plan look correct and cover all the necessary steps based on the spec and our workflow? Please suggest any changes or confirm."
    Await user feedback and revise the `plan.md` content until confirmed.

### 2.4 Create Track Artifacts and Update Main Plan

1.  **Check for existing track name:** Before generating a new Track ID, resolve the **Tracks Directory** using the **Universal File Resolution Protocol**. List all existing track directories in that resolved path. Extract the short names from these track IDs (e.g., ``shortname_YYYYMMDD`` -> `shortname`). If the proposed short name for the new track (derived from the initial description) matches an existing short name, halt the `conductor-new` creation. Explain that a track with that name already exists and suggest choosing a different name or resuming the existing track.
2.  **Generate Track ID:** Create a unique Track ID (e.g., ``shortname_YYYYMMDD``).
3.  **Create Directory:** Create a new directory for the tracks: `<Tracks Directory>/<track_id>/`.
4.  **Create `metadata.json`:** Create a metadata file at `<Tracks Directory>/<track_id>/metadata.json` with content like:
    ```json
    {
      "track_id": "<track_id>",
      "type": "feature", // or "bug", "chore", etc.
      "status": "new", // or in_progress, completed, cancelled
      "created_at": "YYYY-MM-DDTHH:MM:SSZ",
      "updated_at": "YYYY-MM-DDTHH:MM:SSZ",
      "description": "<Initial user description>"
    }
    ```
    *   Populate fields with actual values. Use the current timestamp.
5.  **Write Files:**
    *   Write the confirmed specification content to `<Tracks Directory>/<track_id>/spec.md`.
    *   Write the confirmed plan content to `<Tracks Directory>/<track_id>/plan.md`.
    *   Write the index file to `<Tracks Directory>/<track_id>/index.md` with content:
        ```markdown
        # Track <track_id> Context

        - [Specification](./spec.md)
        - [Implementation Plan](./plan.md)
        - [Metadata](./metadata.json)
        ```
6.  **Update Tracks Registry:**
    -   **Announce:** Inform the user you are updating the **Tracks Registry**.
    -   **Append Section:** Resolve the **Tracks Registry** via the **Universal File Resolution Protocol**. Append a new section for the track to the end of this file. The format MUST be:
        ```markdown

        ---

        - [ ] **Track: <Track Description>**
        *Link: [./<Relative Track Path>/](./<Relative Track Path>/)*
        ```
        (Replace `<Relative Track Path>` with the path to the track directory relative to the **Tracks Registry** file location.)
7.  **Announce Completion:** Inform the user:
    > "New track '<track_id>' has been created and added to the tracks file. You can now start implementation by running `/conductor:implement` (or asking me to implement)."
