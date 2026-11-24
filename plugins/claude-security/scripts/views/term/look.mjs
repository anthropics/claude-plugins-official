import { BOLD, CHIP, ink, on } from './canvas.mjs';
import { whole } from './numbers.mjs';
import { ASH, CLAY, ERROR, HAIRLINE, IVORY, PAPER, PEACH, SLATE, STONE } from './palette.mjs';
import { lowerAscii } from './text.mjs';
export const TEXT = ink(IVORY);
export const SOFT = ink(STONE);
export const DIM = ink(ASH);
export const FAINT = ink(SLATE);
export const STRONG = TEXT + BOLD;
export const LIVE = ink(CLAY);
export const RULE = ink(HAIRLINE);
export const PLACE = ink(PEACH);
export const FAULT = ink(ERROR);
export const ELBOW = ['  ⎿  ', FAINT];
const icon = (nerd, plain = '') => ({ nerd, plain });
export const SANDBOXED = icon('\uf510 ');
export const OPEN = icon('\uea6c ');
export const BRANCH = icon('\uf418 ');
export const COMMIT = icon(' \ueafc ', ' @ ');
export const CLOCK = icon('\uf43a ');
export const SEARCH = icon('\uea6d ', 'Search ');
export const LINK = icon('\ueb14 ');
export const TARGET = icon('\uebf8 ');
export const MAP = icon('\uec05 ');
export const TEAM = icon('\uea7e ');
export const LAYERS = icon('\uebd2 ');
export const SCALES = icon('\ueb12 ');
export const NOTE = icon('\ueb26 ');
export const SHIELD = icon('\ueb53 ');
export const BOOK = icon('\ueaa4 ');
const CAP_LEFT = icon('\ue0b6', '▐');
const CAP_RIGHT = icon('\ue0b4', '▌');
const ANY_FILE = icon('\uea7b ');
const KINDS = new Map([
	['\ue606 ', 'py pyi python'],
	['\ue628 ', 'ts mts typescript'],
	['\ue60c ', 'js mjs cjs javascript'],
	['\ue625 ', 'tsx jsx'],
	['\ue627 ', 'go'],
	['\ue649 ', 'c h'],
	['\ue646 ', 'cc cpp cxx hpp c++'],
	['\ue68b ', 'rs rust'],
	['\ue66d ', 'java'],
	['\ue634 ', 'kt kts kotlin'],
	['\ue648 ', 'cs c#'],
	['\ue605 ', 'rb ruby'],
	['\ue608 ', 'php'],
	['\ue699 ', 'swift'],
	['\ue68e ', 'scala'],
	['\ue620 ', 'lua'],
	['\ue64c ', 'dart'],
	['\ue62d ', 'ex exs elixir'],
	['\ue6a0 ', 'vue'],
	['\ue69a ', 'tf hcl terraform'],
	['\ue691 ', 'sh bash zsh shell'],
	['\ue64d ', 'sql'],
	['\ue60e ', 'html'],
	['\ue614 ', 'css scss'],
	['\ue609 ', 'md markdown'],
	['\ue6a8 ', 'yml yaml'],
	['\ue619 ', 'xml'],
	['\ue615 ', 'toml ini json cfg conf'],
	['\ue650 ', 'dockerfile'],
	['\ue673 ', 'makefile'],
].flatMap(([glyph, names]) => names.split(' ').map(name => [name, icon(glyph)])));
const RAMP = '·✢✳✶✻✽✽✻✶✳✢·';
const STILL = {
	waiting: [icon('\uebb5', '○'), FAINT],
	done: [icon('\uebb3', '●'), SOFT],
	failed: [icon('\uea87', '✕'), FAULT],
	skipped: [icon('\ueabd', '-'), FAINT],
};
export const VOTE = { pending: '○', confirm: '●', refute: '✕', abstain: '-' };
export const kind = (name) => KINDS.get(lowerAscii(name.replace(/^.*[/.]/s, ''))) ?? ANY_FILE;
export const spinner = (beat, agent) => beat === undefined ? '✻' : RAMP[whole((beat + agent * 0.37) / 0.12) % RAMP.length];
export const state = (of, beat, agent) => of === 'running' ? [spinner(beat, agent), LIVE] : STILL[of];
export function pill(ground, letters, ...texts) {
	const pen = on(letters, ground) + BOLD + (letters === PAPER ? CHIP : 0);
	return [[CAP_LEFT, ink(ground)], ...texts.map((text) => [text, pen]), [CAP_RIGHT, ink(ground)]];
}
