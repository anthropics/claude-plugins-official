/**
 * Reading a test run off a shell command's output: how many cases executed,
 * failed and were skipped, for the runners a modernized module usually has.
 */

const RUNNER =
  /^(?:(?:\.\/)?mvnw?\b.*\b(?:test|verify|surefire:test)\b|(?:\.\/)?gradlew?\b.*\b(?:test|check)\b|pytest\b|py\.test\b|python3?\s+-m\s+(?:pytest|unittest)\b|(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?test\b|(?:npx\s+|bunx\s+)?(?:jest|vitest|mocha)\b|dotnet\s+test\b|go\s+test\b|cargo\s+test\b|(?:bundle\s+exec\s+)?rspec\b|prove\b|ctest\b|(?:\.\/vendor\/bin\/)?phpunit\b|make\s+(?:test|check)\b)/

/**
 * Whether a shell command runs a test suite: a runner in command position in
 * any of its segments, not a mere mention of one (`cat pytest.ini` is not).
 */
export function isTestCommand(command: string): boolean {
  return command
    .split(/&&|\|\||[;|\n(]/)
    .map(segment =>
      segment
        .trim()
        // Leading `VAR=value` assignments, `time`, `env`, `sudo`, `exec` do not change what runs.
        .replace(/^(?:(?:[A-Za-z_][A-Za-z0-9_]*=\S*|time|env|sudo|exec|nice|command)\s+)+/, ''),
    )
    .some(segment => RUNNER.test(segment))
}

/** Kept for callers that test a whole command string. */
export const TEST_COMMAND = { test: isTestCommand }

export type TestRun = { executed: number; failed: number; skipped: number }

const num = (value: string | undefined) => (value !== undefined ? Number(value) : 0)

/** The run's totals, or null when the output names none. */
export function readTestRun(output: string): TestRun | null {
  // Maven Surefire / Gradle: the last "Tests run:" line is the total.
  const maven = [...output.matchAll(/Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)/g)].at(-1)

  if (maven !== undefined) {
    const run = num(maven[1])
    const skipped = num(maven[4])

    return { executed: Math.max(0, run - skipped), failed: num(maven[2]) + num(maven[3]), skipped }
  }

  // pytest: "== 3 passed, 1 skipped, 2 failed in 0.12s ==" or "collected 0 items".
  const pytest = /=+\s*((?:\d+\s+\w+,?\s*)+)\s+in\s+[\d.]+s/.exec(output)

  if (pytest !== null) {
    const count = (word: string) => num(new RegExp(`(\\d+)\\s+${word}`).exec(pytest[1] ?? '')?.[1])
    const failed = count('failed') + count('error') + count('errors')

    return { executed: count('passed') + failed + count('xfailed') + count('xpassed'), failed, skipped: count('skipped') + count('deselected') }
  }

  if (/collected 0 items|no tests ran/i.test(output)) {
    return { executed: 0, failed: 0, skipped: 0 }
  }

  // Jest / Vitest: "Tests: 1 failed, 2 skipped, 9 passed, 12 total".
  const jest = /Tests:\s+([^\n]+?)\s+total/i.exec(output) ?? /Tests\s+([^\n]*\d+\s+passed[^\n]*)/i.exec(output)

  if (jest !== null) {
    const count = (word: string) => num(new RegExp(`(\\d+)\\s+${word}`).exec(jest[1] ?? '')?.[1])
    const failed = count('failed')

    return { executed: count('passed') + failed, failed, skipped: count('skipped') + count('todo') }
  }

  // dotnet test: "Passed!  - Failed: 0, Passed: 12, Skipped: 1, Total: 13".
  const dotnet = /Failed:\s*(\d+),\s*Passed:\s*(\d+),\s*Skipped:\s*(\d+),\s*Total:\s*(\d+)/.exec(output)

  if (dotnet !== null) {
    return { executed: num(dotnet[1]) + num(dotnet[2]), failed: num(dotnet[1]), skipped: num(dotnet[3]) }
  }

  // go test / cargo test.
  const cargo = /test result:[^\n]*?(\d+)\s+passed;\s*(\d+)\s+failed;\s*(\d+)\s+ignored/.exec(output)

  if (cargo !== null) {
    return { executed: num(cargo[1]) + num(cargo[2]), failed: num(cargo[2]), skipped: num(cargo[3]) }
  }

  if (/\bno test files\b|\[no tests to run\]/.test(output)) {
    return { executed: 0, failed: 0, skipped: 0 }
  }

  return null
}
