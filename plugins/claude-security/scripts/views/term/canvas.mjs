import { mix, PAPER } from './palette.mjs';
import { cell, REST, SPACE, times } from './text.mjs';
const PAPER_UNIT = 2 ** 24;
export const BOLD = 2 ** 48;
export const ITALIC = 2 * BOLD;
export const CHIP = 4 * BOLD;
export const on = (colour, paper) => colour + paper * PAPER_UNIT;
export const ink = (colour) => on(colour, PAPER);
export const colourOf = (pen) => pen & 0xffffff;
export const paperOf = (pen) => (pen / PAPER_UNIT) & 0xffffff;
export const styled = (pen, style) => ((pen / style) & 1) === 1;
export const RULE_CELL = cell('─');
const ELLIPSIS = cell('…');
export class Rect {
	x;
	y;
	w;
	h;
	constructor(x, y, w, h) {
		this.x = x;
		this.y = y;
		this.w = w;
		this.h = h;
	}
	get end() {
		return this.x + this.w;
	}
	inset(across, down) {
		return new Rect(this.x + across, this.y + down, this.w - 2 * across, this.h - 2 * down);
	}
	below(rows) {
		return new Rect(this.x, this.y + rows, this.w, this.h - rows);
	}
	high(h) {
		return new Rect(this.x, this.y, this.w, h);
	}
}
export class Grid {
	cols;
	rows;
	text;
	inks;
	constructor(cols, rows) {
		this.cols = cols;
		this.rows = rows;
		this.text = new Int32Array(cols * rows).fill(SPACE);
		this.inks = new Float64Array(cols * rows).fill(ink(PAPER));
	}
	take(other, from, to, count) {
		for (let n = 0; n < count; n++) {
			this.text[to + n] = other.text[from + n];
			this.inks[to + n] = other.inks[from + n];
		}
	}
	recolour(change) {
		const { inks } = this;
		const changed = new Map();
		let last = NaN;
		let pen = NaN;
		for (let at = 0; at < inks.length; at++) {
			if (inks[at] !== last) {
				last = inks[at];
				pen = changed.get(last) ?? change(last);
				changed.set(last, pen);
			}
			inks[at] = pen;
		}
	}
}
export class Canvas {
	grid;
	nerd;
	widths;
	constructor(grid, nerd, widths) {
		this.grid = grid;
		this.nerd = nerd;
		this.widths = widths;
	}
	cells(text) {
		return typeof text === 'string' ? this.widths.cells(text) : Array.from(this.nerd ? text.nerd : text.plain, cell);
	}
	measure(line) {
		let cells = 0;
		for (const [text] of line)
			cells += typeof text === 'string' ? this.widths.width(text) : this.cells(text).length;
		return cells;
	}
	spans(x, y, line, end) {
		let at = x;
		for (const [text, pen] of line)
			at = this.put(at, y, text, pen, end);
		return at;
	}
	put(x, y, text, pen, end = this.grid.cols) {
		const { cols, rows, text: cells, inks } = this.grid;
		const room = Math.min(end, cols) - x;
		if (y < 0 || y >= rows || x < 0 || room <= 0)
			return x;
		const found = this.cells(text);
		if (found.length === 0)
			return x;
		if (found.length > room) {
			const lost = found.some((held, n) => n >= room - 1 && held !== SPACE && held !== RULE_CELL);
			if (found[room - 1] === REST)
				found[room - 2] = SPACE;
			found[room - 1] = lost ? ELLIPSIS : found[found.length - 1];
			found.length = room;
		}
		const start = y * cols + x;
		const after = start + found.length;
		if (cells[start] === REST && x > 0)
			cells[start - 1] = SPACE;
		if (x + found.length < cols && cells[after] === REST)
			cells[after] = SPACE;
		for (let at = start; at < after; at++) {
			cells[at] = found[at - start];
			inks[at] = pen;
		}
		return x + found.length;
	}
	lines(area, rows) {
		rows.slice(0, Math.max(area.h, 0)).forEach((row, n) => this.spans(area.x, area.y + n, row, area.end));
	}
	whole(start, y, end, parts, gap = []) {
		return parts.reduce((x, part) => {
			const line = x > start ? [...gap, ...part] : part;
			return x + this.measure(line) <= end ? this.spans(x, y, line, end) : x;
		}, start);
	}
	frame(area, pen) {
		const line = times('─', area.w - 2);
		const gap = times(' ', area.w - 2);
		for (let y = area.y + 1; y < area.y + area.h - 1; y++)
			this.put(area.x, y, `│${gap}│`, pen);
		this.put(area.x, area.y, `╭${line}╮`, pen);
		this.put(area.x, area.y + area.h - 1, `╰${line}╯`, pen);
	}
	fade(share) {
		this.grid.recolour(pen => on(mix(colourOf(pen), PAPER, share), mix(paperOf(pen), PAPER, share)));
	}
}
