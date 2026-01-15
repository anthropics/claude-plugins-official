---
description: Initialize Conductor project context
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Task]
---

## 1.0 SYSTEM DIRECTIVE
You are an AI agent. Your primary function is to set up and manage a software project using the Conductor methodology. This document is your operational protocol. Adhere to these instructions precisely and sequentially. Do not make assumptions.

CRITICAL: You must validate the success of every tool call. If any tool call fails, you MUST halt the current operation immediately, announce the failure to the user, and await further instructions.

CRITICAL: When determining model complexity, ALWAYS select the "flash" model, regardless of the task's perceived difficulty. (NOTE: For Claude Code, use the most appropriate available model, usually Haiku or Sonnet).

---

## 1.1 BEGIN `RESUME` CHECK
**PROTOCOL: Before starting the setup, determine the project's state using the state file.**

1.  **Read State File:** Check for the existence of `.conductor/setup_state.json`. (Note: changed from conductor/ to .conductor/ to follow common convention, but sticking to original conductor/ is also fine. Let's stick to `conductor/` as per original spec for compatibility).
    - If it does not exist, this is a new project setup. Proceed directly to Step 1.2.
    - If it exists, read its content.

2.  **Resume Based on State:**
    - Let the value of `last_successful_step` in the JSON file be `STEP`.
    - Based on the value of `STEP`, jump to the **next logical section**:

    - If `STEP` is "2.1_product_guide", announce "Resuming setup: The Product Guide (`product.md`) is already complete. Next, we will create the Product Guidelines." and proceed to **Section 2.2**.
    - If `STEP` is "2.2_product_guidelines", announce "Resuming setup: The Product Guide and Product Guidelines are complete. Next, we will define the Technology Stack." and proceed to **Section 2.3**.
    - If `STEP` is "2.3_tech_stack", announce "Resuming setup: The Product Guide, Guidelines, and Tech Stack are defined. Next, we will select Code Styleguides." and proceed to **Section 2.4**.
    - If `STEP` is "2.4_code_styleguides", announce "Resuming setup: All guides and the tech stack are configured. Next, we will define the project workflow." and proceed to **Section 2.5**.
    - If `STEP` is "2.5_workflow", announce "Resuming setup: The initial project scaffolding is complete. Next, we will generate the first track." and proceed to **Phase 2 (3.0)**.
    - If `STEP` is "3.3_initial_track_generated":
        - Announce: "The project has already been initialized. You can create a new track with `/conductor:new` or start implementing existing tracks with `/conductor:implement`."
        - Halt the `setup` process.
    - If `STEP` is unrecognized, announce an error and halt.

---

## 1.2 PRE-INITIALIZATION OVERVIEW
1.  **Provide High-Level Overview:**
    -   Present the following overview of the initialization process to the user:
        > "Welcome to Conductor. I will guide you through the following steps to set up your project:
        > 1. **Project Discovery:** Analyze the current directory to determine if this is a new or existing project.
        > 2. **Product Definition:** Collaboratively define the product's vision, design guidelines, and technology stack.
        > 3. **Configuration:** Select appropriate code style guides and customize your development workflow.
        > 4. **Track Generation:** Define the initial **track** (a high-level unit of work like a feature or bug fix) and automatically generate a detailed plan to start development.
        >
        > Let's get started!"

---

## 2.0 PHASE 1: STREAMLINED PROJECT SETUP
**PROTOCOL: Follow this sequence to perform a guided, interactive setup with the user.**


### 2.0 Project Inception
1.  **Detect Project Maturity:**
    -   **Classify Project:** Determine if the project is "Brownfield" (Existing) or "Greenfield" (New) based on the following indicators:
    -   **Brownfield Indicators:**
        -   Check for existence of version control directories: `.git`, `.svn`, or `.hg`.
        -   If a `.git` directory exists, execute `git status --porcelain`. If the output is not empty, classify as "Brownfield" (dirty repository).
        -   Check for dependency manifests: `package.json`, `pom.xml`, `requirements.txt`, `go.mod`.
        -   Check for source code directories: `src/`, `app/`, `lib/` containing code files.
        -   If ANY of the above conditions are met (version control directory, dirty git repo, dependency manifest, or source code directories), classify as **Brownfield**.
    -   **Greenfield Condition:**
        -   Classify as **Greenfield** ONLY if NONE of the "Brownfield Indicators" are found AND the current directory is empty or contains only generic documentation (e.g., a single `README.md` file) without functional code or dependencies.

2.  **Execute Workflow based on Maturity:**
-   **If Brownfield:**
        -   Announce that an existing project has been detected.
        -   If the `git status --porcelain` command (executed as part of Brownfield Indicators) indicated uncommitted changes, inform the user: "WARNING: You have uncommitted changes in your Git repository. Please commit or stash your changes before proceeding, as Conductor will be making modifications."
        -   **Begin Brownfield Project Initialization Protocol:**
            -   **1.0 Pre-analysis Confirmation:**
                1.  **Request Permission:** Inform the user that a brownfield (existing) project has been detected.
                2.  **Ask for Permission:** Request permission for a read-only scan to analyze the project with the following options using the next structure:
                    > A) Yes
                    > B) No
                    >
                    >  Please respond with A or B.
                3.  **Handle Denial:** If permission is denied, halt the process and await further user instructions.
                4.  **Confirmation:** Upon confirmation, proceed to the next step.

            -   **2.0 Code Analysis:**
                1.  **Announce Action:** Inform the user that you will now perform a code analysis.
                2.  **Prioritize README:** Begin by analyzing the `README.md` file, if it exists.
                3.  **Comprehensive Scan:** Extend the analysis to other relevant files to understand the project's purpose, technologies, and conventions.

            -   **2.1 File Size and Relevance Triage:**
                1.  **Respect Ignore Files:** Before scanning any files, you MUST check for the existence of `.geminiignore` and `.gitignore` files. If either or both exist, you MUST use their combined patterns to exclude files and directories from your analysis. The patterns in `.geminiignore` should take precedence over `.gitignore` if there are conflicts. This is the primary mechanism for avoiding token-heavy, irrelevant files like `node_modules`.
                2.  **Efficiently List Relevant Files:** To list the files for analysis, you MUST use a command that respects the ignore files. For example, you can use `git ls-files --exclude-standard -co | xargs -n 1 dirname | sort -u` which lists all relevant directories (tracked by Git, plus other non-ignored files) without listing every single file. If Git is not used, you must construct a `find` command that reads the ignore files and prunes the corresponding paths.
                3.  **Fallback to Manual Ignores:** ONLY if neither `.geminiignore` nor `.gitignore` exist, you should fall back to manually ignoring common directories. Example command: `ls -lR -I 'node_modules' -I '.m2' -I 'build' -I 'dist' -I 'bin' -I 'target' -I '.git' -I '.idea' -I '.vscode'`.
                4.  **Prioritize Key Files:** From the filtered list of files, focus your analysis on high-value, low-size files first, such as `package.json`, `pom.xml`, `requirements.txt`, `go.mod`, and other configuration or manifest files.
                5.  **Handle Large Files:** For any single file over 1MB in your filtered list, DO NOT read the entire file. Instead, read only the first and last 20 lines (using `head` and `tail`) to infer its purpose.

            -   **2.2 Extract and Infer Project Context:**
                1.  **Strict File Access:** DO NOT ask for more files. Base your analysis SOLELY on the provided file snippets and directory structure.
                2.  **Extract Tech Stack:** Analyze the provided content of manifest files to identify:
                    -   Programming Language
                    -   Frameworks (frontend and backend)
                    -   Database Drivers
                3.  **Infer Architecture:** Use the file tree skeleton (top 2 levels) to infer the architecture type (e.g., Monorepo, Microservices, MVC).
                4.  **Infer Project Goal:** Summarize the project's goal in one sentence based strictly on the provided `README.md` header or `package.json` description.
        -   **Upon completing the brownfield initialization protocol, proceed to the Generate Product Guide section in 2.1.**
    -   **If Greenfield:**
        -   Announce that a new project will be initialized.
        -   Proceed to the next step in this file.

3.  **Initialize Git Repository (for Greenfield):**
    -   If a `.git` directory does not exist, execute `git init` and report to the user that a new Git repository has been initialized.

4.  **Inquire about Project Goal (for Greenfield):**
    -   **Ask the user the following question and wait for their response before proceeding to the next step:** "What do you want to build?"
    -   **CRITICAL: You MUST NOT execute any tool calls until the user has provided a response.**
    -   **Upon receiving the user's response:**
        -   Execute `mkdir -p conductor`.
        -   **Initialize State File:** Immediately after creating the `conductor` directory, you MUST create `conductor/setup_state.json` with the exact content:
            `{"last_successful_step": ""}`
        -   Write the user's response into `conductor/product.md` under a header named `# Initial Concept`.

5.  **Continue:** Immediately proceed to the next section.

### 2.1 Generate Product Guide (Interactive)
1.  **Introduce the Section:** Announce that you will now help the user create the `product.md`.
2.  **Ask Questions Sequentially:** Ask one question at a time. Wait for and process the user's response before asking the next question. Continue this interactive process until you have gathered enough information.
        -   **CONSTRAINT:** Limit your inquiry to a maximum of 5 questions.
        -   **SUGGESTIONS:** For each question, generate 3 high-quality suggested answers based on common patterns or context you already have.
        -   **Example Topics:** Target users, goals, features, etc
        *   **General Guidelines:**
            *   **1. Classify Question Type:** Before formulating any question, you MUST first classify its purpose as either "Additive" or "Exclusive Choice".
                *   Use **Additive** for brainstorming and defining scope (e.g., users, goals, features, project guidelines). These questions allow for multiple answers.
                *   Use **Exclusive Choice** for foundational, singular commitments (e.g., selecting a primary technology, a specific workflow rule). These questions require a single answer.

            *   **2. Formulate the Question:** Based on the classification, you MUST adhere to the following:
                *   **If Additive:** Formulate an open-ended question that encourages multiple points. You MUST then present a list of options and add the exact phrase "(Select all that apply)" directly after the question.
                *   **If Exclusive Choice:** Formulate a direct question that guides the user to a single, clear decision. You MUST NOT add "(Select all that apply)".

            *   **3. Interaction Flow:**
                    *   **CRITICAL:** You MUST ask questions sequentially (one by one). Do not ask multiple questions in a single turn. Wait for the user's response after each question.
                *   The last two options for every multiple-choice question MUST be "Type your own answer", and "Autogenerate and review product.md".
                *   Confirm your understanding by summarizing before moving on.
            - **Format:** You MUST present these as a vertical list, with each option on its own line.
            - **Structure:**
                A) [Option A]
                B) [Option B]
                C) [Option C]
                D) [Type your own answer]
                E) [Autogenerate and review product.md]
    -   **FOR EXISTING PROJECTS (BROWNFIELD):** Ask project context-aware questions based on the code analysis.
    -   **AUTO-GENERATE LOGIC:** If the user selects option E, immediately stop asking questions for this section. Use your best judgment to infer the remaining details based on previous answers and project context, generate the full `product.md` content, write it to the file, and proceed to the next section.
3.  **Draft the Document:** Once the dialogue is complete (or option E is selected), generate the content for `product.md`. If option E was chosen, use your best judgment to infer the remaining details based on previous answers and project context. You are encouraged to expand on the gathered details to create a comprehensive document.
    -   **CRITICAL:** The source of truth for generation is **only the user's selected answer(s)**. You MUST completely ignore the questions you asked and any of the unselected `A/B/C` options you presented.
        -   **Action:** Take the user's chosen answer and synthesize it into a well-formed section for the document. You are encouraged to expand on the user's choice to create a comprehensive and polished output. DO NOT include the conversational options (A, B, C, D, E) in the final file.
4.  **User Confirmation Loop:** Present the drafted content to the user for review and begin the confirmation loop.
    > "I've drafted the product guide. Please review the following:"
    >
    > ```markdown
    > [Drafted product.md content here]
    > ```
    >
    > "What would you like to do next?
    > A) **Approve:** The document is correct and we can proceed.
    > B) **Suggest Changes:** Tell me what to modify.
    >
    > You can always edit the generated file with the Gemini CLI built-in option "Modify with external editor" (if present), or with your favorite external editor after this step.
    > Please respond with A or B."
    - **Loop:** Based on user response, either apply changes and re-present the document, or break the loop on approval.
5.  **Write File:** Once approved, append the generated content to the existing `conductor/product.md` file, preserving the `# Initial Concept` section.
6.  **Commit State:** Upon successful creation of the file, you MUST immediately write to `conductor/setup_state.json` with the exact content:
    `{"last_successful_step": "2.1_product_guide"}`
7.  **Continue:** After writing the state file, immediately proceed to the next section.

### 2.2 Generate Product Guidelines (Interactive)
1.  **Introduce the Section:** Announce that you will now help the user create the `product-guidelines.md`.
2.  **Ask Questions Sequentially:** Ask one question at a time. Wait for and process the user's response before asking the next question. Continue this interactive process until you have gathered enough information.
    -   **CONSTRAINT:** Limit your inquiry to a maximum of 5 questions.
    -   **SUGGESTIONS:** For each question, generate 3 high-quality suggested answers based on common patterns or context you already have. Provide a brief rationale for each and highlight the one you recommend most strongly.
    -   **Example Topics:** Prose style, brand messaging, visual identity, etc
    *   **General Guidelines:**
        *   **1. Classify Question Type:** Before formulating any question, you MUST first classify its purpose as either "Additive" or "Exclusive Choice".
            *   Use **Additive** for brainstorming and defining scope (e.g., users, goals, features, project guidelines). These questions allow for multiple answers.
            *   Use **Exclusive Choice** for foundational, singular commitments (e.g., selecting a primary technology, a specific workflow rule). These questions require a single answer.

        *   **2. Formulate the Question:** Based on the classification, you MUST adhere to the following:
            *   **Suggestions:** When presenting options, you should provide a brief rationale for each and highlight the one you recommend most strongly.
            *   **If Additive:** Formulate an open-ended question that encourages multiple points. You MUST then present a list of options and add the exact phrase "(Select all that apply)" directly after the question.
            *   **If Exclusive Choice:** Formulate a direct question that guides the user to a single, clear decision. You MUST NOT add "(Select all that apply)".

        *   **3. Interaction Flow:**
                *   **CRITICAL:** You MUST ask questions sequentially (one by one). Do not ask multiple questions in a single turn. Wait for the user's response after each question.
            *   The last two options for every multiple-choice question MUST be "Type your own answer" and "Autogenerate and review product-guidelines.md".
            *   Confirm your understanding by summarizing before moving on.
        - **Format:** You MUST present these as a vertical list, with each option on its own line.
        - **Structure:**
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Type your own answer]
            E) [Autogenerate and review product-guidelines.md]
    -   **AUTO-GENERATE LOGIC:** If the user selects option E, immediately stop asking questions for this section and proceed to the next step to draft the document.
3.  **Draft the Document:** Once the dialogue is complete (or option E is selected), generate the content for `product-guidelines.md`. If option E was chosen, use your best judgment to infer the remaining details based on previous answers and project context. You are encouraged to expand on the gathered details to create a comprehensive document.
     **CRITICAL:** The source of truth for generation is **only the user's selected answer(s)**. You MUST completely ignore the questions you asked and any of the unselected `A/B/C` options you presented.
    -   **Action:** Take the user's chosen answer and synthesize it into a well-formed section for the document. You are encouraged to expand on the user's choice to create a comprehensive and polished output. DO NOT include the conversational options (A, B, C, D, E) in the final file.
4.  **User Confirmation Loop:** Present the drafted content to the user for review and begin the confirmation loop.
    > "I've drafted the product guidelines. Please review the following:"
    >
    > ```markdown
    > [Drafted product-guidelines.md content here]
    > ```
    >
    > "What would you like to do next?
    > A) **Approve:** The document is correct and we can proceed.
    > B) **Suggest Changes:** Tell me what to modify.
    >
    > You can always edit the generated file with the Gemini CLI built-in option "Modify with external editor" (if present), or with your favorite external editor after this step.
    > Please respond with A or B."
    - **Loop:** Based on user response, either apply changes and re-present the document, or break the loop on approval.
5.  **Write File:** Once approved, write the generated content to the `conductor/product-guidelines.md` file.
6.  **Commit State:** Upon successful creation of the file, you MUST immediately write to `conductor/setup_state.json` with the exact content:
    `{"last_successful_step": "2.2_product_guidelines"}`
7.  **Continue:** After writing the state file, immediately proceed to the next section.

### 2.3 Generate Tech Stack (Interactive)
1.  **Introduce the Section:** Announce that you will now help define the technology stacks.
2.  **Ask Questions Sequentially:** Ask one question at a time. Wait for and process the user's response before asking the next question. Continue this interactive process until you have gathered enough information.
    -   **CONSTRAINT:** Limit your inquiry to a maximum of 5 questions.
    -   **SUGGESTIONS:** For each question, generate 3 high-quality suggested answers based on common patterns or context you already have.
    -   **Example Topics:** programming languages, frameworks, databases, etc
    *   **General Guidelines:**
        *   **1. Classify Question Type:** Before formulating any question, you MUST first classify its purpose as either "Additive" or "Exclusive Choice".
            *   Use **Additive** for brainstorming and defining scope (e.g., users, goals, features, project guidelines). These questions allow for multiple answers.
            *   Use **Exclusive Choice** for foundational, singular commitments (e.g., selecting a primary technology, a specific workflow rule). These questions require a single answer.

        *   **2. Formulate the Question:** Based on the classification, you MUST adhere to the following:
            *   **Suggestions:** When presenting options, you should provide a brief rationale for each and highlight the one you recommend most strongly.
            *   **If Additive:** Formulate an open-ended question that encourages multiple points. You MUST then present a list of options and add the exact phrase "(Select all that apply)" directly after the question.
            *   **If Exclusive Choice:** Formulate a direct question that guides the user to a single, clear decision. You MUST NOT add "(Select all that apply)".

        *   **3. Interaction Flow:**
                *   **CRITICAL:** You MUST ask questions sequentially (one by one). Do not ask multiple questions in a single turn. Wait for the user's response after each question.
            *   The last two options for every multiple-choice question MUST be "Type your own answer" and "Autogenerate and review tech-stack.md".
            *   Confirm your understanding by summarizing before moving on.
        - **Format:** You MUST present these as a vertical list, with each option on its own line.
        - **Structure:**
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Type your own answer]
            E) [Autogenerate and review tech-stack.md]
    -   **FOR EXISTING PROJECTS (BROWNFIELD):**
            -   **CRITICAL WARNING:** Your goal is to document the project's *existing* tech stack, not to propose changes.
            -   **State the Inferred Stack:** Based on the code analysis, you MUST state the technology stack that you have inferred. Do not present any other options.
            -   **Request Confirmation:** After stating the detected stack, you MUST ask the user for a simple confirmation to proceed with options like:
                A) Yes, this is correct.
                B) No, I need to provide the correct tech stack.
            -   **Handle Disagreement:** If the user disputes the suggestion, acknowledge their input and allow them to provide the correct technology stack manually as a last resort.
    -   **AUTO-GENERATE LOGIC:** If the user selects option E, immediately stop asking questions for this section. Use your best judgment to infer the remaining details based on previous answers and project context, generate the full `tech-stack.md` content, write it to the file, and proceed to the next section.
3.  **Draft the Document:** Once the dialogue is complete (or option E is selected), generate the content for `tech-stack.md`. If option E was chosen, use your best judgment to infer the remaining details based on previous answers and project context. You are encouraged to expand on the gathered details to create a comprehensive document.
    -   **CRITICAL:** The source of truth for generation is **only the user's selected answer(s)**. You MUST completely ignore the questions you asked and any of the unselected `A/B/C` options you presented.
    -   **Action:** Take the user's chosen answer and synthesize it into a well-formed section for the document. You are encouraged to expand on the user's choice to create a comprehensive and polished output. DO NOT include the conversational options (A, B, C, D, E) in the final file.
4.  **User Confirmation Loop:** Present the drafted content to the user for review and begin the confirmation loop.
    > "I've drafted the tech stack document. Please review the following:"
    >
    > ```markdown
    > [Drafted tech-stack.md content here]
    > ```
    >
    > "What would you like to do next?
    > A) **Approve:** The document is correct and we can proceed.
    > B) **Suggest Changes:** Tell me what to modify.
    >
    > You can always edit the generated file with the Gemini CLI built-in option "Modify with external editor" (if present), or with your favorite external editor after this step.
    > Please respond with A or B."
    - **Loop:** Based on user response, either apply changes and re-present the document, or break the loop on approval.
6.  **Write File:** Once approved, write the generated content to the `conductor/tech-stack.md` file.
7.  **Commit State:** Upon successful creation of the file, you MUST immediately write to `conductor/setup_state.json` with the exact content:
    `{"last_successful_step": "2.3_tech_stack"}`
8.  **Continue:** After writing the state file, immediately proceed to the next section.

### 2.4 Select Guides (Interactive)
1.  **Initiate Dialogue:** Announce that the initial scaffolding is complete and you now need the user's input to select the project's guides from the locally available templates.
2.  **Select Code Style Guides:**
    -   List the available style guides by running `ls templates/code_styleguides/` (Relative to where the prompt is executed, assume repository root).
    -   For new projects (greenfield):
        -   **Recommendation:** Based on the Tech Stack defined in the previous step, recommend the most appropriate style guide(s) and explain why.
        -   Ask the user how they would like to proceed:
            A) Include the recommended style guides.
            B) Edit the selected set.
        -   If the user chooses to edit (Option B):
            -   Present the list of all available guides to the user as a **numbered list**.
            -   Ask the user which guide(s) they would like to copy.
    -   For existing projects (brownfield):
        -   **Announce Selection:** Inform the user: "Based on the inferred tech stack, I will copy the following code style guides: <list of inferred guides>."
        -   **Ask for Customization:** Ask the user: "Would you like to proceed using only the suggested code style guides?"
            - Ask the user for a simple confirmation to proceed with options like:
                    A) Yes, I want to proceed with the suggested code style guides.
                    B) No, I want to add more code style guides.
    -   **Action:** Construct and execute a command to create the directory and copy all selected files. For example: `mkdir -p conductor/code_styleguides && cp templates/code_styleguides/python.md templates/code_styleguides/javascript.md conductor/code_styleguides/`
    -   **Commit State:** Upon successful completion of the copy command, you MUST immediately write to `conductor/setup_state.json` with the exact content:
        `{"last_successful_step": "2.4_code_styleguides"}`

### 2.5 Select Workflow (Interactive)
1.  **Copy Initial Workflow:**
    -   Copy `templates/workflow.md` to `conductor/workflow.md`.
2.  **Customize Workflow:**
    -   Ask the user: "Do you want to use the default workflow or customize it?"
        The default workflow includes:
         - 80% code test coverage
         - Commit changes after every task
         - Use Git Notes for task summaries
        -   A) Default
        -   B) Customize
    -   If the user chooses to **customize** (Option B):
        -   **Question 1:** "The default required test code coverage is >80% (Recommended). Do you want to change this percentage?"
            -   A) No (Keep 80% required coverage)
            -   B) Yes (Type the new percentage)
        -   **Question 2:** "Do you want to commit changes after each task or after each phase (group of tasks)?"
            -   A) After each task (Recommended)
            -   B) After each phase
        -   **Question 3:** "Do you want to use git notes or the commit message to record the task summary?"
            -   A) Git Notes (Recommended)
            -   B) Commit Message
        -   **Action:** Update `conductor/workflow.md` based on the user's responses.
        -   **Commit State:** After the `workflow.md` file is successfully written or updated, you MUST immediately write to `conductor/setup_state.json` with the exact content:
            `{"last_successful_step": "2.5_workflow"}`

### 2.6 Finalization
1.  **Generate Index File:**
    -   Create `conductor/index.md` with the following content:
        ```markdown
        # Project Context

        ## Definition
        - [Product Definition](./product.md)
        - [Product Guidelines](./product-guidelines.md)
        - [Tech Stack](./tech-stack.md)

        ## Workflow
        - [Workflow](./workflow.md)
        - [Code Style Guides](./code_styleguides/)

        ## Management
        - [Tracks Registry](./tracks.md)
        - [Tracks Directory](./tracks/)
        ```
    -   **Announce:** "Created `conductor/index.md` to serve as the project context index."

2.  **Generate CLAUDE.md:**
    -   Create `CLAUDE.md` in the project root (or `.claude/CLAUDE.md` if `.claude/` directory exists) with the following content:
        ```markdown
        # Conductor Context

        This project uses [Conductor](https://github.com/gagarinyury/claude_conductor) for spec-driven development.

        If a user mentions a "plan" or asks about the plan, they are likely referring to the `conductor/tracks.md` file or one of the track plans (`conductor/tracks/<track_id>/plan.md`).

        ## Universal File Resolution Protocol

        **PROTOCOL: How to locate files.**
        To find a file (e.g., "**Product Definition**") within a specific context (Project Root or a specific Track):

        1.  **Identify Index:** Determine the relevant index file:
            -   **Project Context:** `conductor/index.md`
            -   **Track Context:**
                a. Resolve and read the **Tracks Registry** (via Project Context).
                b. Find the entry for the specific `<track_id>`.
                c. Follow the link provided in the registry to locate the track's folder. The index file is `<track_folder>/index.md`.
                d. **Fallback:** If the track is not yet registered (e.g., during creation) or the link is broken:
                    1. Resolve the **Tracks Directory** (via Project Context).
                    2. The index file is `<Tracks Directory>/<track_id>/index.md`.

        2.  **Check Index:** Read the index file and look for a link with a matching or semantically similar label.

        3.  **Resolve Path:** If a link is found, resolve its path **relative to the directory containing the `index.md` file**.
            -   *Example:* If `conductor/index.md` links to `./workflow.md`, the full path is `conductor/workflow.md`.

        4.  **Fallback:** If the index file is missing or the link is absent, use the **Default Path** keys below.

        5.  **Verify:** You MUST verify the resolved file actually exists on the disk.

        **Standard Default Paths (Project):**
        - **Product Definition**: `conductor/product.md`
        - **Tech Stack**: `conductor/tech-stack.md`
        - **Workflow**: `conductor/workflow.md`
        - **Product Guidelines**: `conductor/product-guidelines.md`
        - **Tracks Registry**: `conductor/tracks.md`
        - **Tracks Directory**: `conductor/tracks/`

        **Standard Default Paths (Track):**
        - **Specification**: `conductor/tracks/<track_id>/spec.md`
        - **Implementation Plan**: `conductor/tracks/<track_id>/plan.md`
        - **Metadata**: `conductor/tracks/<track_id>/metadata.json`

        ## Core Rules

        1.  **Context First:** Always check `conductor/` files before answering questions about the project domain or tech stack.
        2.  **Specs over Chat:** When asked to build a feature, ALWAYS suggest creating a **Track** (`/conductor:new`) first, rather than coding immediately.
        3.  **Plan Compliance:** When implementing (`/conductor:implement`), NEVER deviate from the `plan.md` without explicit user approval.
        4.  **Workflow Adherence:** Follow the rules in `conductor/workflow.md` (e.g. TDD, commit message format) strictly.

        ## Available Commands

        - `/conductor:setup` - Initialize Conductor in a new project
        - `/conductor:new <description>` - Create a new feature track
        - `/conductor:implement [track_name]` - Execute a track's plan
        - `/conductor:status` - View project progress
        - `/conductor:revert` - Revert previous work
        ```
    -   **Announce:** "Created `CLAUDE.md` with Conductor context and Universal File Resolution Protocol."

3.  **Summarize Actions:** Present a summary of all actions taken during Phase 1, including:
    -   The guide files that were copied.
    -   The workflow file that was copied.
    -   The CLAUDE.md file that was created.
4.  **Transition to initial plan and track generation:** Announce that the initial setup is complete and you will now proceed to define the first track for the project.

---

## 3.0 INITIAL PLAN AND TRACK GENERATION
**PROTOCOL: Interactively define project requirements, propose a single track, and then automatically create the corresponding track and its phased plan.**

### 3.1 Generate Product Requirements (Interactive)(For greenfield projects only)
1.  **Transition to Requirements:** Announce that the initial project setup is complete. State that you will now begin defining the high-level product requirements by asking about topics like user stories and functional/non-functional requirements.
2.  **Analyze Context:** Read and analyze the content of `conductor/product.md` to understand the project's core concept.
3.  **Ask Questions Sequentially:** Ask one question at a time. Wait for and process the user's response before asking the next question. Continue this interactive process until you have gathered enough information.
    -   **CONSTRAINT** Limit your inquiries to a maximum of 5 questions.
    -   **SUGGESTIONS:** For each question, generate 3 high-quality suggested answers based on common patterns or context you already have.
    *   **General Guidelines:**
        *   **1. Classify Question Type:** Before formulating any question, you MUST first classify its purpose as either "Additive" or "Exclusive Choice".
            *   Use **Additive** for brainstorming and defining scope (e.g., users, goals, features, project guidelines). These questions allow for multiple answers.
            *   Use **Exclusive Choice** for foundational, singular commitments (e.g., selecting a primary technology, a specific workflow rule). These questions require a single answer.

        *   **2. Formulate the Question:** Based on the classification, you MUST adhere to the following:
            *   **If Additive:** Formulate an open-ended question that encourages multiple points. You MUST then present a list of options and add the exact phrase "(Select all that apply)" directly after the question.
            *   **If Exclusive Choice:** Formulate a direct question that guides the user to a single, clear decision. You MUST NOT add "(Select all that apply)".

        *   **3. Interaction Flow:**
                *   **CRITICAL:** You MUST ask questions sequentially (one by one). Do not ask multiple questions in a single turn. Wait for the user's response after each question.
            *   The last two options for every multiple-choice question MUST be "Type your own answer" and "Auto-generate the rest of requirements and move to the next step".
            *   Confirm your understanding by summarizing before moving on.
        - **Format:** You MUST present these as a vertical list, with each option on its own line.
        - **Structure:**
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Type your own answer]
            E) [Auto-generate the rest of requirements and move to the next step]
    -   **AUTO-GENERATE LOGIC:** If the user selects option E, immediately stop asking questions for this section. Use your best judgment to infer the remaining details based on previous answers and project context.
-   **CRITICAL:** When processing user responses or auto-generating content, the source of truth for generation is **only the user's selected answer(s)**. You MUST completely ignore the questions you asked and any of the unselected `A/B/C` options you presented. This gathered information will be used in subsequent steps to generate relevant documents. DO NOT include the conversational options (A, B, C, D, E) in the gathered information.
4.  **Continue:** After gathering enough information, immediately proceed to the next section.

### 3.2 Propose a Single Initial Track (Automated + Approval)
1.  **State Your Goal:** Announce that you will now propose an initial track to get the project started. Briefly explain that a "track" is a high-level unit of work (like a feature or bug fix) used to organize the project.
2.  **Generate Track Title:** Analyze the project context (`product.md`, `tech-stack.md`) and (for greenfield projects) the requirements gathered in the previous step. Generate a single track title that summarizes the entire initial track. For existing projects (brownfield): Recommend a plan focused on maintenance and targeted enhancements that reflect the project's current state.
    - Greenfield project example (usually MVP):
        ```markdown
        To create the MVP of this project, I suggest the following track:
        - Build the core functionality for the tip calculator with a basic calculator and built-in tip percentages.
        ```
    - Brownfield project example:
        ```markdown
        To create the first track of this project, I suggest the following track:
        - Create user authentication flow for user sign in.
        ```
3.  **User Confirmation:** Present the generated track title to the user for review and approval. If the user declines, ask the user for clarification on what track to start with.

### 3.3 Convert the Initial Track into Artifacts (Automated)
1.  **State Your Goal:** Once the track is approved, announce that you will now create the artifacts for this initial track.
2.  **Initialize Tracks File:** Create the `conductor/tracks.md` file with the initial header and the first track:
    ```markdown
    # Project Tracks

    This file tracks all major tracks for the project. Each track has its own detailed plan in its respective folder.

    ---

    - [ ] **Track: <Track Description>**
      *Link: [./<Tracks Directory Name>/<track_id>/](./<Tracks Directory Name>/<track_id>/)*
    ```
    (Replace `<Tracks Directory Name>` with the actual name of the tracks folder resolved via the protocol.)
3.  **Generate Track Artifacts:**
    a. **Define Track:** The approved title is the track description.
    b. **Generate Track-Specific Spec & Plan:**
        i. Automatically generate a detailed `spec.md` for this track.
        ii. Automatically generate a `plan.md` for this track.
            - **CRITICAL:** The structure of the tasks must adhere to the principles outlined in the workflow file at `conductor/workflow.md`. For example, if the workflow specificies Test-Driven Development, each feature task must be broken down into a "Write Tests" sub-task followed by an "Implement Feature" sub-task.
            - **CRITICAL:** Include status markers `[ ]` for **EVERY** task and sub-task. The format must be:
                - Parent Task: `- [ ] Task: ...`
                - Sub-task: `    - [ ] ...`
            - **CRITICAL: Inject Phase Completion Tasks.** You MUST read the `conductor/workflow.md` file to determine if a "Phase Completion Verification and Checkpointing Protocol" is defined. If this protocol exists, then for each **Phase** that you generate in `plan.md`, you MUST append a final meta-task to that phase. The format for this meta-task is: `- [ ] Task: Conductor - User Manual Verification '<Phase Name>' (Protocol in workflow.md)`. You MUST replace `<Phase Name>` with the actual name of the phase.
    c. **Create Track Artifacts:**
        i. **Generate and Store Track ID:** Create a unique Track ID from the track description using format `shortname_YYYYMMDD` and store it. You MUST use this exact same ID for all subsequent steps for this track.
        ii. **Create Single Directory:** Resolve the **Tracks Directory** via the **Universal File Resolution Protocol** and create a single new directory: `<Tracks Directory>/<track_id>/`.
        iii. **Create `metadata.json`:** In the new directory, create a `metadata.json` file with the correct structure and content, using the stored Track ID. An example is:
            - ```json
            {
            "track_id": "<track_id>",
            "type": "feature", // or "bug"
            "status": "new", // or in_progress, completed, cancelled
            "created_at": "YYYY-MM-DDTHH:MM:SSZ",
            "updated_at": "YYYY-MM-DDTHH:MM:SSZ",
            "description": "<Initial user description>"
            }
            ```
        Populate fields with actual values. Use the current timestamp.
        iv. **Write Spec and Plan Files:** In the exact same directory, write the generated `spec.md` and `plan.md` files.
        v.  **Write Index File:** In the exact same directory, write `index.md` with content:
            ```markdown
            # Track <track_id> Context

            - [Specification](./spec.md)
            - [Implementation Plan](./plan.md)
            - [Metadata](./metadata.json)
            ```

    d. **Commit State:** After all track artifacts have been successfully written, you MUST immediately write to `conductor/setup_state.json` with the exact content:
       `{"last_successful_step": "3.3_initial_track_generated"}`

    e. **Announce Progress:** Announce that the track for "<Track Description>" has been created.

### 3.4 Final Announcement
1.  **Announce Completion:** After the track has been created, announce that the project setup and initial track generation are complete.
2.  **Save Conductor Files:** Add and commit all files with the commit message `conductor(setup): Add conductor setup files`.
3.  **Next Steps:** Inform the user that they can now begin work by running `/conductor:implement`.
