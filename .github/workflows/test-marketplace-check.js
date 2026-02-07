#!/usr/bin/env node

/**
 * Test script for marketplace.json PR validation logic.
 * Run with: node .github/workflows/test-marketplace-check.js
 */

function checkMarketplaceViolations(mainPlugins, prPlugins) {
  const mainSourceByName = new Map(
    mainPlugins.map(p => [p.name, JSON.stringify(p.source)])
  );

  const violations = [];
  for (const plugin of prPlugins) {
    if (!mainSourceByName.has(plugin.name)) {
      violations.push(`- Adding new plugin: \`${plugin.name}\``);
    } else if (mainSourceByName.get(plugin.name) !== JSON.stringify(plugin.source)) {
      violations.push(`- Changing source for plugin: \`${plugin.name}\``);
    }
  }

  return violations;
}

// Test cases
const tests = [
  {
    name: "No changes - should allow",
    main: [
      { name: "foo", source: "./plugins/foo", description: "Foo plugin" }
    ],
    pr: [
      { name: "foo", source: "./plugins/foo", description: "Foo plugin" }
    ],
    expectBlocked: false
  },
  {
    name: "Description change only - should allow",
    main: [
      { name: "foo", source: "./plugins/foo", description: "Old description" }
    ],
    pr: [
      { name: "foo", source: "./plugins/foo", description: "New description" }
    ],
    expectBlocked: false
  },
  {
    name: "Version/category change - should allow",
    main: [
      { name: "foo", source: "./plugins/foo", version: "1.0.0", category: "dev" }
    ],
    pr: [
      { name: "foo", source: "./plugins/foo", version: "2.0.0", category: "productivity" }
    ],
    expectBlocked: false
  },
  {
    name: "New plugin added - should block",
    main: [
      { name: "foo", source: "./plugins/foo" }
    ],
    pr: [
      { name: "foo", source: "./plugins/foo" },
      { name: "bar", source: "./plugins/bar" }
    ],
    expectBlocked: true,
    expectedViolation: "Adding new plugin: `bar`"
  },
  {
    name: "Source changed (string) - should block",
    main: [
      { name: "foo", source: "./plugins/foo" }
    ],
    pr: [
      { name: "foo", source: "./plugins/evil" }
    ],
    expectBlocked: true,
    expectedViolation: "Changing source for plugin: `foo`"
  },
  {
    name: "Source changed (string to object) - should block",
    main: [
      { name: "foo", source: "./plugins/foo" }
    ],
    pr: [
      { name: "foo", source: { source: "url", url: "https://evil.com/repo.git" } }
    ],
    expectBlocked: true,
    expectedViolation: "Changing source for plugin: `foo`"
  },
  {
    name: "Source changed (object URL) - should block",
    main: [
      { name: "foo", source: { source: "url", url: "https://github.com/good/repo.git" } }
    ],
    pr: [
      { name: "foo", source: { source: "url", url: "https://github.com/evil/repo.git" } }
    ],
    expectBlocked: true,
    expectedViolation: "Changing source for plugin: `foo`"
  },
  {
    name: "Plugin removed - should allow",
    main: [
      { name: "foo", source: "./plugins/foo" },
      { name: "bar", source: "./plugins/bar" }
    ],
    pr: [
      { name: "foo", source: "./plugins/foo" }
    ],
    expectBlocked: false
  },
  {
    name: "Multiple violations - should block with all listed",
    main: [
      { name: "foo", source: "./plugins/foo" }
    ],
    pr: [
      { name: "foo", source: "./plugins/evil" },
      { name: "bar", source: "./plugins/bar" }
    ],
    expectBlocked: true,
    expectedViolationCount: 2
  },
  {
    name: "Object source unchanged - should allow",
    main: [
      { name: "foo", source: { source: "url", url: "https://github.com/org/repo.git" } }
    ],
    pr: [
      { name: "foo", source: { source: "url", url: "https://github.com/org/repo.git" }, description: "Updated" }
    ],
    expectBlocked: false
  }
];

// Run tests
console.log("Running marketplace.json validation tests\n");
console.log("=".repeat(50));

let passed = 0;
let failed = 0;

for (const test of tests) {
  const violations = checkMarketplaceViolations(test.main, test.pr);
  const blocked = violations.length > 0;

  let success = blocked === test.expectBlocked;

  if (success && test.expectedViolation) {
    success = violations.some(v => v.includes(test.expectedViolation));
  }

  if (success && test.expectedViolationCount) {
    success = violations.length === test.expectedViolationCount;
  }

  if (success) {
    console.log(`✓ ${test.name}`);
    passed++;
  } else {
    console.log(`✗ ${test.name}`);
    console.log(`  Expected blocked: ${test.expectBlocked}, got: ${blocked}`);
    if (violations.length > 0) {
      console.log(`  Violations: ${violations.join(", ")}`);
    }
    failed++;
  }
}

console.log("=".repeat(50));
console.log(`\nResults: ${passed} passed, ${failed} failed`);

process.exit(failed > 0 ? 1 : 0);
