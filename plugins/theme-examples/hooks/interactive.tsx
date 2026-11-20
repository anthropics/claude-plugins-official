import type { ElementConstructor, RenderElement, ShaderProps } from 'claude-code'

import type { ShaderScene } from './themes'

/**
 * Lays a theme's shader over its still Svg. A theme with no shader gets the Svg back unchanged.
 *
 * A new scene needs its name in `ShaderScene` and a case of its own here: the type checker refuses a name with no case,
 * and where no checker ran such a theme shows its Svg alone.
 * Claude Code finds shader files by reading this source, and takes only a `module` written as a string in an element
 * named `Shader`: a path from a list, or a renamed parameter, leaves the Svg showing alone.
 */
export function overShader(
  Shader: ElementConstructor<ShaderProps> | undefined,
  shader: ShaderScene | undefined,
  still: RenderElement,
): RenderElement {
  // A Claude Code from before shaders gives no Shader: the Svg is the whole scene.
  if (Shader === undefined || shader === undefined) {
    return still
  }

  switch (shader) {
    case 'duck-pond':
      return <Shader module="./scenes/duck-pond/scene.ts">{still}</Shader>
    case 'falling-sand':
      return <Shader module="./scenes/falling-sand/scene.ts">{still}</Shader>
    case 'field-lines':
      return <Shader module="./scenes/field-lines/scene.ts">{still}</Shader>
    case 'garden-beetles':
      return <Shader module="./scenes/garden-beetles/scene.ts">{still}</Shader>
    case 'koi-pond':
      return <Shader module="./scenes/koi-pond/scene.ts">{still}</Shader>
    case 'ripple-tank':
      return <Shader module="./scenes/ripple-tank/scene.ts">{still}</Shader>
    case 'sea-sparkle':
      return <Shader module="./scenes/sea-sparkle/scene.ts">{still}</Shader>
    case 'semicolony':
      return <Shader module="./scenes/semicolony/scene.ts">{still}</Shader>
    case 'star-chart':
      return <Shader module="./scenes/star-chart/scene.ts">{still}</Shader>
  }

  // Reached only by a name with no case above, which the type checker refuses on this line.
  shader satisfies never

  return still
}
