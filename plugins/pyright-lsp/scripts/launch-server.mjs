#!/usr/bin/env node
// launch-server.mjs: start an npm-installed language server without tripping
// over Windows shim files.
//
// WHY THIS EXISTS
// Runtimes that spawn language servers without a shell (libuv uv_spawn on
// Windows) resolve only `.exe` when the command has no extension. npm installs
// Node-based servers as an extensionless sh script plus `.cmd` and `.ps1`
// wrappers, never as a `.exe`, so a bare `typescript-language-server` command
// fails with ENOENT on Windows while working everywhere else. Pointing the
// command at the `.cmd` is fragile: it is overwritten on plugin update, breaks
// under pnpm, and Node 18+ refuses to spawn `.cmd` without a shell anyway.
//
// WHAT IT DOES
// Resolves `<npm-package>/<cli-relative-path>` under the global npm root and
// execs it with the current Node binary, passing stdio straight through. The
// runtime spawns `node` (a real `.exe`, always resolvable) with this script and
// the plugin-relative arguments, so no per-machine absolute path is needed:
//
//   "command": "node",
//   "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/launch-server.mjs",
//            "typescript-language-server", "lib/cli.mjs", "--stdio"]
//
// PLATFORM BEHAVIOR
// The resolution is identical on every OS. On Linux and macOS the same lookup
// succeeds and the behavior matches spawning the server directly, so this adds
// no Windows-only branch to any plugin config. stdio is inherited untouched:
// this process never parses a frame, so it cannot corrupt or truncate one.
//
// USAGE
//   node launch-server.mjs <npm-package> <cli-relative-path> [server args...]
//
// EXIT CODES
//   0 on normal server exit (forwards the server exit code), 1 with a stderr
//   line when the server cannot be found.

import { spawn, spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

function fail(message) {
	process.stderr.write("launch-server: " + message + "\n");
	process.exit(1);
}

const [, , npmPackage, cliRel, ...serverArgs] = process.argv;

if (!npmPackage || !cliRel) {
	fail(
		"usage: node launch-server.mjs <npm-package> <cli-relative-path> [server args...]",
	);
}

// The global npm root is where `npm install -g` puts packages. `npm` itself is a
// `.cmd` on Windows, so this one call uses a shell; everything after it is
// shell-free.
function globalNpmRoot() {
	const npmCmd = process.platform === "win32" ? "npm.cmd" : "npm";
	try {
		const r = spawnSync(npmCmd, ["root", "-g"], {
			encoding: "utf8",
			shell: process.platform === "win32",
			timeout: 15000,
			windowsHide: true,
		});
		const out = (r.stdout || "").trim();
		if (r.status === 0 && out) return out;
	} catch {
		/* fall through to PATH probing */
	}
	return null;
}

// A bare command that resolves to a real executable (not a shim) is usable
// directly. On Windows `.cmd`, `.bat`, `.ps1` and the extensionless sh script
// are all excluded, because none of them can be spawned without a shell.
function findOnPath(command) {
	const pathEnv = process.env.PATH || "";
	const exts = process.platform === "win32" ? [".exe"] : [""];
	for (const dir of pathEnv.split(path.delimiter)) {
		if (!dir) continue;
		for (const ext of exts) {
			const candidate = path.join(dir, command + ext);
			try {
				if (fs.statSync(candidate).isFile()) return candidate;
			} catch {
				/* keep scanning */
			}
		}
	}
	return null;
}

let cliPath = null;

const npmRoot = globalNpmRoot();
if (npmRoot) {
	const candidate = path.join(npmRoot, npmPackage, cliRel);
	try {
		if (fs.statSync(candidate).isFile()) cliPath = candidate;
	} catch {
		/* not under the npm root; try PATH */
	}
}

// The server binary itself, when it is directly runnable.
let direct = null;
if (!cliPath) {
	// The npm package name and the binary name usually match (typescript-language-
	// server, pyright-langserver ships as pyright-langserver). Derive the guess
	// from the package name only as a last resort before failing loudly.
	direct = findOnPath(npmPackage);
}

let child;
if (cliPath) {
	child = spawn(process.execPath, [cliPath, ...serverArgs], {
		stdio: "inherit",
	});
} else if (direct) {
	child = spawn(direct, serverArgs, { stdio: "inherit" });
} else {
	fail(
		`cannot find ${npmPackage}/${cliRel} under the global npm root` +
			(npmRoot ? ` (${npmRoot})` : " (npm root lookup failed)") +
			" and no runnable binary on PATH. Install it with: npm install -g " +
			npmPackage,
	);
}

child.on("exit", (code, signal) => {
	// Forward the outcome so supervisors see the real result, not the wrapper's.
	if (signal) {
		try {
			process.kill(process.pid, signal);
		} catch {
			process.exit(1);
		}
		return;
	}
	process.exit(code === null ? 0 : code);
});

child.on("error", (err) => {
	fail("failed to start server: " + (err.message || err));
});
