---
name: imagine
description: Use this skill when the user asks to generate images, videos, vector graphics (SVG), or lottie animations; edit an existing image; enhance a prompt; browse past generations; manage assets; or estimate generation costs. Covers all Vanikya Imagine tools.
version: 1.0.0
---

# Vanikya Imagine

Generate images, videos, vectors, and lottie animations using the user's Vanikya credits.

## Output Types

| Type | Description | Model type filter |
|---|---|---|
| Raster image | Standard image (PNG/JPG) | (default, omit type) |
| Video | Short video clip | `"video"` |
| Vector | SVG graphic | `"vector"` |
| Lottie | Animated lottie JSON | `"lottie"` |

## Available Tools

| Tool | Purpose |
|---|---|
| `imagine_list_models` | List available models — pass `type` for video/vector/lottie |
| `imagine_generate_image` | Generate raster image, vector, or lottie |
| `imagine_generate_video` | Generate a video |
| `imagine_edit_generation` | Edit an existing image generation |
| `imagine_enhance_prompt` | Expand a short prompt into a detailed generation prompt |
| `imagine_estimate_credits` | Estimate credit cost before generating |
| `imagine_get_generation` | Poll a generation's status |
| `imagine_list_generations` | List past generations (filterable by format) |
| `imagine_update_generation_tags` | Add tags to a generation |
| `imagine_list_assets` | List reusable assets |
| `imagine_get_asset` | Get a specific asset |
| `imagine_import_asset_from_url` | Import an external image URL as a reusable asset |

## Working with Assets

Assets are reusable images stored in the user's Vanikya account (imported or saved from generations).

- `imagine_list_assets` — Browse assets, filter by format (`"image"`, `"vector"`, `"lottie"`, `"video"`)
- `imagine_get_asset` — Fetch a specific asset by ID
- `imagine_import_asset_from_url` — Save an external image URL as a reusable asset (useful before editing)

Use assets as reference images in generation or editing workflows.

## Mandatory Workflow — Follow This Order

### Generating an image (raster)

1. **List available models** to get valid model IDs:
   ```
   imagine_list_models()
   ```
   Pick a model ID from the result (e.g. `img_r3t8w5n1` for GPT-Image-1.5, `img_d4h1y9f7` for Flux 2).
2. **Enhance the prompt** (always, unless user provides a detailed prompt):
   ```
   imagine_enhance_prompt({ prompt: "<user's raw prompt>" })
   ```
3. **Estimate credits** and confirm with the user:
   ```
   imagine_estimate_credits({ prompt: "<enhanced prompt>", models: ["<model_id>"] })
   ```
   If the user declines, stop — do not proceed with generation. Ask if they'd like to choose a cheaper model or adjust the prompt.
4. **Generate**:
   ```
   imagine_generate_image({ prompt: "<enhanced prompt>", models: ["<model_id>"] })
   ```
5. **Poll until complete** — call `imagine_get_generation` repeatedly until `status` changes from `"pending"`:
   ```
   imagine_get_generation({ id: "<generation_id>" })
   ```
   Repeat until `status` is `"completed"` or `"failed"`. Stop after 5 retries. If still pending, inform the user the generation may be stuck and suggest checking the Vanikya dashboard.

### Generating a video

1. **Always fetch video models first** (video models are not in the default list):
   ```
   imagine_list_models({ type: "video" })
   ```
2. Pick a model ID from the result.
3. Estimate credits and confirm with the user. If the user declines, stop — do not proceed with generation. Ask if they'd like to choose a cheaper model or adjust the prompt.
4. Call `imagine_generate_video`.
5. Poll `imagine_get_generation` until complete. Stop after 5 retries. If still pending, inform the user the generation may be stuck and suggest checking the Vanikya dashboard.

### Generating a vector (SVG)

1. Fetch vector models:
   ```
   imagine_list_models({ type: "vector" })
   ```
2. Enhance prompt, estimate credits and confirm with the user. If the user declines, stop — do not proceed with generation. Ask if they'd like to choose a cheaper model or adjust the prompt.
3. Call `imagine_generate_image` with a model ID from the `imagine_list_models({ type: "vector" })` result — do NOT use a raster model ID.
4. Poll until complete. Stop after 5 retries. If still pending, inform the user the generation may be stuck and suggest checking the Vanikya dashboard.

### Generating a lottie animation

1. Fetch lottie models:
   ```
   imagine_list_models({ type: "lottie" })
   ```
2. Enhance prompt, estimate credits and confirm with the user. If the user declines, stop — do not proceed with generation. Ask if they'd like to choose a cheaper model or adjust the prompt.
3. Call `imagine_generate_image` with a model ID from the `imagine_list_models({ type: "lottie" })` result — do NOT use a raster model ID.
4. Poll until complete. Stop after 5 retries. If still pending, inform the user the generation may be stuck and suggest checking the Vanikya dashboard.
5. **Note:** Editing lottie generations is not supported. If the user wants changes, regenerate with a revised prompt.

### Editing an image

1. Call `imagine_edit_generation` with the generation `id` and an edit prompt.
2. Poll until complete.
3. **Lottie editing is not supported** — inform the user and offer to regenerate.

## Rules

- **Always** call `imagine_list_models` before generating to get valid model IDs — never guess a model ID.
- **Always** call `imagine_enhance_prompt` before generating unless the user's prompt is already detailed (over 50 words).
- **Always** call `imagine_estimate_credits` and show the user the cost before generating.
- **Always** poll `imagine_get_generation` after any generation call — it is async and returns `status: "pending"` immediately.
- **Never** skip credit estimation — generations can be expensive and the user must consent.
- For video, vector, and lottie output types, **always** call `imagine_list_models` with the correct `type` parameter — do NOT use model IDs from a different type.
