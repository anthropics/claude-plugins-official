"""plugins.turkey — the executable Turkey country plugin.

Layers (each a subpackage, each with a single responsibility):

    config/     Country Config      -- typed view of countries/tr/country.config.yaml
    parser/     File parsing         -- YAML / markdown -> plain Python values
    sources/    Legal Source Registry -- catalog of TR legal authorities
    citations/  Citation logic       -- formatting + risk classification
    adapters/   External systems     -- one class per Turkish legal-info system
    mcp/        MCP bindings         -- concrete connector config + client seam
    providers/  Provider contracts   -- Citation/Search/Document Provider impls
    tools/      Tool Registry        -- Provider capabilities exposed as callables
    rag/        Local retrieval      -- keyword search over knowledge/*.md
    prompts/    Prompt assembly      -- composes retrieval + citations into text
    workflow/   Orchestration        -- top-level use cases wiring everything together

Plus, at this level:

    paths.py          -- where on disk this package reads its data from
    manifest.py        -- Plugin Manifest (this code package's own identity)
    registration.py     -- Plugin Registration (wires this plugin into the engine)

See README.md in this directory for the full architecture write-up and
SOLID-principle notes per layer.
"""
