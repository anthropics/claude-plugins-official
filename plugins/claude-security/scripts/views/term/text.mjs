export const REST = 0;
export const SPACE = 32;
const MARKED = 0x110000;
const MOST_MARKS = 2;
const MOST_MARKED = 1 << 16;
const PRINTABLE_ASCII = /^[ -~]*$/;
const PLAIN_LINE = /^[!-~]+(?: [!-~]+)*$/;
const BLANK = /[\t-\r \x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+/;
const marked = [];
const numbered = new Map();
export const cell = (ch) => ch.codePointAt(0) ?? REST;
export const spelled = (held) => (held < MARKED ? String.fromCodePoint(held) : marked[held - MARKED]);
function withMark(held, mark) {
	const text = spelled(held) + mark;
	if (Array.from(text).length > 1 + MOST_MARKS)
		return held;
	let number = numbered.get(text);
	if (number === undefined) {
		if (marked.length === MOST_MARKED)
			return held;
		number = MARKED + marked.length;
		marked.push(text);
		numbered.set(text, number);
	}
	return number;
}
function unseen(ch) {
	return (ch < 0x20 ||
		(ch >= 0x7f && ch <= 0x9f) ||
		ch === 0xad ||
		ch === 0x34f ||
		ch === 0x61c ||
		ch === 0x115f ||
		(ch >= 0x180b && ch <= 0x180f) ||
		(ch >= 0x200b && ch <= 0x200f) ||
		(ch >= 0x2028 && ch <= 0x202e) ||
		(ch >= 0x2060 && ch <= 0x206f) ||
		ch === 0x3164 ||
		(ch >= 0xe000 && ch <= 0xf8ff) ||
		ch === 0xfeff ||
		ch === 0xffa0 ||
		(ch >= 0xfff9 && ch <= 0xfffb) ||
		ch >= 0xe0000);
}
const singleLine = (text, most) => text.split(BLANK, most).filter(Boolean).join(' ');
function trimmedEnd(text) {
	let end = text.length;
	while (end > 0 && BLANK.test(text[end - 1]))
		end--;
	return text.slice(0, end);
}
function joined(cells, start, end) {
	let out = '';
	for (let at = start; at < end; at++)
		if (cells[at] !== REST)
			out += spelled(cells[at]);
	return out;
}
export const first = (text, count) => Array.from(text.slice(0, 2 * Math.max(count, 0)))
	.slice(0, count)
	.join('');
export const times = (text, count) => text.repeat(Math.max(count, 0));
export const lowerAscii = (text) => text.replace(/[A-Z]+/g, letters => letters.toLowerCase());
export class Widths {
	wide = new Set();
	marks = new Set();
	learn(wide, marks) {
		for (const ch of wide)
			this.wide.add(cell(ch));
		for (const ch of marks)
			this.marks.add(cell(ch));
	}
	cells(text, most = Infinity) {
		const out = [];
		for (let next = 0; next < text.length && out.length <= most; next++) {
			const ch = text.codePointAt(next) ?? REST;
			if (ch > 0xffff)
				next++;
			if (ch >= SPACE && ch < 0x7f)
				out.push(ch);
			else if (ch === 9)
				out.push(SPACE);
			else if (unseen(ch))
				out.push(...Array.from(`\\u{${ch.toString(16)}}`, cell));
			else if (this.marks.has(ch)) {
				const at = out.length - (out.at(-1) === REST ? 2 : 1);
				if (at >= 0 && (ch < 0xfe00 || ch > 0xfe0f))
					out[at] = withMark(out[at], String.fromCodePoint(ch));
			}
			else if (this.wide.has(ch))
				out.push(ch, REST);
			else
				out.push(ch);
		}
		return out;
	}
	width(text) {
		return PRINTABLE_ASCII.test(text) ? text.length : this.cells(text).length;
	}
	fit(text, room) {
		if (text.length <= room && PLAIN_LINE.test(text))
			return text;
		const found = this.cells(singleLine(text, Math.max(room, 0) + 3), room);
		if (found.length <= room)
			return joined(found, 0, found.length);
		return room < 1 ? '' : joined(found, 0, room - (found[room - 1] === REST ? 2 : 1)) + '…';
	}
	fitEnd(text, room) {
		const found = this.cells(singleLine(text));
		if (found.length <= room)
			return joined(found, 0, found.length);
		return room < 1 ? '' : '…' + joined(found, found.length + 1 - room, found.length);
	}
	pad(text, room) {
		const fitted = this.fit(text, room);
		return fitted + times(' ', room - this.width(fitted));
	}
	wrap(text, room) {
		const most = Math.max(room, 2);
		const paragraphs = text.split('\n');
		if (paragraphs.at(-1) === '')
			paragraphs.pop();
		const lines = [];
		for (const paragraph of paragraphs) {
			const found = this.cells(trimmedEnd(paragraph));
			const plain = PRINTABLE_ASCII.test(paragraph);
			let start = 0;
			const take = (end) => lines.push(plain ? paragraph.slice(start, end) : joined(found, start, end));
			while (found.length - start > most) {
				let cut = start + most;
				while (cut > start + (most >> 1) && found[cut] !== SPACE)
					cut--;
				if (found[cut] !== SPACE || cut === start + (most >> 1)) {
					cut = start + most - Number(found[start + most] === REST);
				}
				take(cut);
				start = found[cut] === SPACE ? cut + 1 : cut;
			}
			take(found.length);
		}
		return lines;
	}
}
