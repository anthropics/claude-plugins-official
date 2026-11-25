const FAR = 9999;
const ONE_KEY = /\x1b\[[^@-~\x1b]*[@-~]?|\x1b\][ -~]*(?:\x07|\x1b\\)?|\x1bO[^\x1b]?|à[^\x1b]?|./gsu;
const SPELLINGS = [
	[{ kind: 'step', rows: -1 }, '\x1b[A', '\x1bOA', 'àH', '\x1b[D', '\x1bOD', 'àK', 'k'],
	[{ kind: 'step', rows: 1 }, '\x1b[B', '\x1bOB', 'àP', '\x1b[C', '\x1bOC', 'àM', 'j'],
	[{ kind: 'step', rows: -FAR }, '\x1b[H', '\x1bOH', '\x1b[1~', '\x1b[7~', 'àG'],
	[{ kind: 'step', rows: FAR }, '\x1b[F', '\x1bOF', '\x1b[4~', '\x1b[8~', 'àO'],
	[{ kind: 'page', pages: -1 }, '\x1b[5~', 'àI'],
	[{ kind: 'page', pages: 1 }, '\x1b[6~', 'àQ', ' '],
	[{ kind: 'tab', forward: true }, '\t'],
	[{ kind: 'tab', forward: false }, '\x1b[Z'],
	[{ kind: 'enter' }, '\r', '\n'],
	[{ kind: 'esc' }, '\x1b'],
	[{ kind: 'interrupt' }, '\x03'],
	[{ kind: 'repaint' }, '\x0c'],
	[{ kind: 'status' }, '\x1b[0n'],
	[{ kind: 'cursor', wide: false }, '\x1b[1;1R', '\x1b[1;2R'],
	[{ kind: 'cursor', wide: true }, '\x1b[1;3R'],
];
const NAMED = new Map(SPELLINGS.flatMap(([key, ...spellings]) => spellings.map(typed => [typed, key])));
function named(typed) {
	const letter = /^\P{Cc}/u.exec(typed)?.[0];
	return NAMED.get(typed) ?? (letter === undefined ? [] : { kind: 'letter', letter });
}
export const read = (typed) => (typed.match(ONE_KEY) ?? []).flatMap(named);
