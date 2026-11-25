import { BOLD, CHIP, colourOf, Grid, ITALIC, paperOf, styled } from './canvas.mjs';
import { clamp, nearest, sum } from './numbers.mjs';
import { PAPER } from './palette.mjs';
import { cell, REST, SPACE, spelled } from './text.mjs';
const SHORT_GAP = 5;
const URGENT = 1000;
const KEY_COST = 8000;
const OWN_TEXT = 39;
const OWN_PAPER = 49;
const GREY = 90;
const INK_BYTES = 16;
const RUN_BYTES = 24;
const CELL_BYTES = 2;
const UNKNOWN = 1;
const DARKEST = 39;
const LIGHTEST = 495;
const MIDDLE = 2100;
const PALE_ENDS = 380;
const NEAR_WHITE_ENDS = 425;
const TINT_SPAN = 20;
const TINT_ENDS = 200;
const ON_TINT = 0.7;
const CUBE = [0, 95, 135, 175, 215, 255];
const HUES = [
	[0.07, 91],
	[0.17, 33],
	[0.42, 32],
	[0.53, 36],
	[0.66, 34],
	[0.9, 35],
];
const TO_BLOCKS = ['✻✽✶✳✢╭╮╰╯━╸▎⎿✕●○◆…•', '****+┌┐└┘══│└x■·■.·', ' ░░░▒▒▒▓▓'];
const TO_ASCII = ['✻✽✶✳✢·╭╮╰╯├┤┬┴┼─━╸│▎▐▌⎿✕●○◆…•→↑↓', '****+.+++++++++-==||[]Lx#o!.*>^v', ' ...:::++'];
const SOMETIMES_WIDE = '✽·╭╮╰╯├┤┬┴┼─━│▎▌●○◆…•→↑↓';
export const Colour = { None: 0, Basic: 1, Indexed: 2, True: 3 };
export const Glyphs = { Ascii: 0, Blocks: 1, Braille: 2, Nerd: 3 };
function swap([from, to, shades], ch) {
	const dots = cell(ch) - 0x2800;
	return dots >= 0 && dots < 256 ? shades[dots.toString(2).replaceAll('0', '').length] : to[from.indexOf(ch)];
}
export function spell(held, { glyphs, wide }) {
	if (held === REST)
		return glyphs === Glyphs.Ascii ? ' ' : '';
	const [ch, ...marks] = spelled(held);
	if (glyphs === Glyphs.Ascii)
		return ch < '\x80' ? ch : (swap(TO_ASCII, ch) ?? '?');
	const shown = glyphs === Glyphs.Blocks ? (swap(TO_BLOCKS, ch) ?? ch) : ch;
	const narrow = wide && SOMETIMES_WIDE.includes(shown) ? swap(TO_ASCII, shown) : undefined;
	return (narrow ?? shown) + marks.join('');
}
const ascii = (held) => held > REST && held < 0x80;
const channels = (colour) => [colour >> 16, (colour >> 8) & 255, colour & 255];
function forLight(rgb) {
	const high = Math.max(...rgb);
	const low = Math.min(...rgb);
	const ends = high + low;
	const tint = ends > PALE_ENDS && ends < NEAR_WHITE_ENDS && high - low > TINT_SPAN;
	if (tint)
		return rgb.map(c => clamp(TINT_ENDS / 2 + 2 * c - ends, 0, 255));
	const shift = nearest((DARKEST + LIGHTEST) / 2 - ends - ((ends - DARKEST) * (LIGHTEST - ends)) / MIDDLE);
	return rgb.map(c => clamp(c + shift, 0, 255));
}
function indexed(rgb) {
	const steps = rgb.map(c => CUBE.reduce((best, v, n) => (Math.abs(v - c) < Math.abs(CUBE[best] - c) ? n : best), 0));
	const grey = clamp(nearest((sum(rgb) / 3 - 8) / 10), 0, 23);
	const cubeMiss = sum(rgb.map((c, n) => (CUBE[steps[n]] - c) ** 2));
	const greyMiss = sum(rgb.map(c => (8 + 10 * grey - c) ** 2));
	return greyMiss < cubeMiss ? 232 + grey : 16 + 36 * steps[0] + 6 * steps[1] + steps[2];
}
function basic(colour) {
	const [r, g, b] = channels(colour);
	const high = Math.max(r, g, b);
	const spread = high - Math.min(r, g, b);
	if (spread < 53)
		return high > 150 ? OWN_TEXT : GREY;
	let sixths = 4 + (r - g) / spread;
	if (high === r)
		sixths = (g - b) / spread;
	else if (high === g)
		sixths = 2 + (b - r) / spread;
	const hue = sixths < 0 ? sixths / 6 + 1 : sixths / 6;
	return HUES.find(([limit]) => hue <= limit)?.[1] ?? 31;
}
function codesOf(pen, { colour, light }) {
	const text = colourOf(pen);
	const paper = paperOf(pen);
	const bold = styled(pen, BOLD);
	if (colour > Colour.Basic) {
		const shown = (of) => (light ? forLight(channels(of)) : channels(of));
		const code = (rgb) => (colour === Colour.True ? `2;${rgb.join(';')}` : `5;${indexed(rgb)}`);
		const tinted = light && paper !== PAPER && sum(channels(text)) > sum(channels(paper));
		const letters = tinted ? shown(text).map(c => nearest(c * ON_TINT)) : shown(text);
		const styles = `0;${bold ? '1;' : ''}${styled(pen, ITALIC) ? '3;' : ''}`;
		return { styles, reverse: false, text: `38;${code(letters)}`, paper: `48;${code(shown(paper))}` };
	}
	const reverse = styled(pen, CHIP);
	const own = (weight, code) => ({
		styles: `0;${weight}${reverse ? '7;' : ''}`,
		reverse,
		text: String(code),
		paper: String(OWN_PAPER),
	});
	if (colour === Colour.Basic)
		return own(bold ? '1;' : '', basic(reverse ? paper : text));
	const hue = bold || reverse ? OWN_TEXT : basic(text);
	if (hue === GREY)
		return own('2;', OWN_TEXT);
	return own(bold || hue !== OWN_TEXT ? '1;' : '', OWN_TEXT);
}
function sameOn(a, b, held) {
	if (a.paper !== b.paper)
		return false;
	return (a.text === b.text && a.styles === b.styles) || (held === SPACE && !a.reverse && !b.reverse);
}
function change(last, to) {
	if (last?.styles !== to.styles)
		return `\x1b[${to.styles}${to.text};${to.paper}m`;
	if (last.text === to.text)
		return `\x1b[${to.paper}m`;
	return last.paper === to.paper ? `\x1b[${to.text}m` : `\x1b[${to.text};${to.paper}m`;
}
function costOf(runs, inks) {
	let cost = 0;
	for (const { start, end } of runs) {
		cost += RUN_BYTES + CELL_BYTES * (end - start);
		for (let at = start + 1; at < end; at++)
			if (inks[at] !== inks[at - 1])
				cost += INK_BYTES;
	}
	return cost;
}
function rowDiffers(a, b, y) {
	for (let at = y * a.cols; at < (y + 1) * a.cols; at++) {
		if (a.text[at] !== b.text[at] || a.inks[at] !== b.inks[at])
			return true;
	}
	return false;
}
const sameSize = (a, b) => a.cols === b.cols && a.rows === b.rows;
export class Painter {
	caps;
	shown = new Grid(0, 0);
	wanted = new Grid(0, 0);
	waited = new Map();
	coded = new Map();
	spellings = new Map();
	constructor(caps) {
		this.caps = caps;
	}
	get behind() {
		return this.waited.size > 0;
	}
	forget() {
		this.shown = new Grid(0, 0);
	}
	smudge() {
		const { cols, rows, text } = this.shown;
		text.fill(UNKNOWN, (rows >> 1) * cols, ((rows >> 1) + 4) * cols);
	}
	diff(frame, budget, urgent) {
		const { cols, rows, text, inks } = frame;
		if (urgent && sameSize(frame, this.wanted)) {
			for (let y = 0; y < rows; y++) {
				if (rowDiffers(frame, this.wanted, y))
					this.waited.set(y, (this.waited.get(y) ?? 0) + URGENT);
			}
		}
		let out = '';
		if (!sameSize(frame, this.shown)) {
			this.shown = new Grid(cols, rows);
			if (this.caps.colour > Colour.Basic)
				this.shown.text.fill(UNKNOWN);
			out = '\x1b[0m\x1b[2J';
		}
		let pen;
		for (const { y, runs } of this.affordable(this.stale(frame), budget)) {
			for (const { start, end } of runs) {
				out += `\x1b[${y + 1};${start - y * cols + 1}H`;
				let codes = this.codes(inks[start]);
				for (let at = start; at < end; at++) {
					if (at > start && inks[at] !== inks[at - 1])
						codes = this.codes(inks[at]);
					if (codes !== pen && !(pen && sameOn(codes, pen, text[at]))) {
						out += change(pen, codes);
						pen = codes;
					}
					if (this.caps.wide && at > start && ascii(text[at]) && !ascii(text[at - 1])) {
						out += `\x1b[${at - y * cols + 1}G`;
					}
					out += this.spelling(text[at]);
				}
			}
			this.shown.take(frame, y * cols, y * cols, cols);
		}
		this.wanted = frame;
		return out && `\x1b[?2026h${out}\x1b[?2026l`;
	}
	codes(pen) {
		let codes = this.coded.get(pen);
		if (!codes) {
			codes = codesOf(pen, this.caps);
			this.coded.set(pen, codes);
		}
		return codes;
	}
	spelling(held) {
		if (ascii(held))
			return String.fromCharCode(held);
		let text = this.spellings.get(held);
		if (text === undefined) {
			text = spell(held, this.caps);
			this.spellings.set(held, text);
		}
		return text;
	}
	affordable(stale, budget) {
		const waits = (row) => this.waited.get(row.y) ?? 0;
		const rank = (row) => row.cost / (1 + waits(row));
		stale.sort((a, b) => rank(a) - rank(b));
		const urgent = sum(stale.filter(row => waits(row) >= URGENT).map(row => row.cost));
		const most = Math.max(budget, Math.min(urgent, KEY_COST));
		let spent = 0;
		const over = stale.findIndex(row => {
			spent += row.cost;
			return spent > most;
		});
		const waiting = over < 0 ? [] : stale.splice(Math.max(over, 1));
		this.waited = new Map(waiting.map(row => [row.y, waits(row) + 1]));
		return stale.sort((a, b) => a.y - b.y);
	}
	stale({ cols, rows, text, inks }) {
		const { shown } = this;
		const stale = [];
		for (let y = 0; y < rows; y++) {
			const runs = [];
			let last;
			for (let at = y * cols; at < (y + 1) * cols; at++) {
				if (text[at] === shown.text[at]) {
					if (inks[at] === shown.inks[at])
						continue;
					if (sameOn(this.codes(inks[at]), this.codes(shown.inks[at]), text[at]))
						continue;
				}
				if (last && at - last.end <= SHORT_GAP)
					last.end = at + 1;
				else {
					last = { start: text[at] === REST ? at - 1 : at, end: at + 1 };
					runs.push(last);
				}
			}
			if (last)
				stale.push({ y, runs, cost: costOf(runs, inks) });
		}
		return stale;
	}
}
