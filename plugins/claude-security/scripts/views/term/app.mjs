import { readAtlas } from './atlas.mjs';
import { RULE_CELL } from './canvas.mjs';
import { read } from './keys.mjs';
import { clamp } from './numbers.mjs';
import { CATCH_UP, Motion, Pace } from './pace.mjs';
import { Colour, Painter, spell } from './paint.mjs';
import { fields, index, Scan, text } from './scan.mjs';
import { View } from './view.mjs';
const ASK = '\x1b[5n';
const STILL_AFTER = 8;
const LARGEST_SIDE = 1000;
const TIERS = 4;
const TIMES_BYTES = 24;
const HEAD_BYTES = 9;
const NOTHING = Buffer.alloc(0);
function parsed(body) {
	const json = body.toString();
	try {
		return fields(JSON.parse(json));
	}
	catch {
		return undefined;
	}
}
function mostMotion(facts) {
	if (facts.motion !== true)
		return Motion.Still;
	return facts.relayed === true ? Motion.Reduced : Motion.Full;
}
class Screen {
	caps;
	view;
	painter;
	pace;
	written;
	due = 0;
	stirred = 0;
	pressed = false;
	measuring = false;
	constructor(facts) {
		const colour = (index(facts.colour, TIERS) ?? 0);
		const glyphs = (index(facts.glyphs, TIERS) ?? 0);
		this.caps = { colour, glyphs, wide: false, light: facts.light === true };
		this.view = new View(text(facts.url), glyphs);
		this.painter = new Painter(this.caps);
		this.pace = new Pace(mostMotion(facts), facts.remote === true, facts.asks === true);
	}
	answer(scan, kind, body) {
		if (body.length < TIMES_BYTES)
			return NOTHING;
		const now = body.readDoubleLE(0);
		const rest = body.subarray(TIMES_BYTES);
		if (this.written !== undefined)
			this.pace.sent(this.written, body.readDoubleLE(8), body.readDoubleLE(16));
		this.written = undefined;
		if (kind === 'K')
			return this.reply(now, '', this.typed(scan, rest.toString(), now));
		if (kind === 'R')
			return this.reply(now, this.taken(now));
		if (kind !== 'T' || rest.length < 4)
			return NOTHING;
		const side = (at) => clamp(rest.readUInt16LE(at), 1, LARGEST_SIDE);
		return this.reply(now, this.frame(scan, side(0), side(2), now));
	}
	reply(now, out, quit = false) {
		const answer = Buffer.allocUnsafe(HEAD_BYTES + Buffer.byteLength(out));
		answer[0] = Number(quit);
		answer.writeDoubleLE(this.due > now ? this.due - now : 0, 1);
		answer.write(out, HEAD_BYTES);
		return answer;
	}
	typed(scan, typed, now) {
		let quit = false;
		for (const key of read(typed)) {
			switch (key.kind) {
				case 'status':
					this.pace.answered(now);
					break;
				case 'cursor':
					this.pace.answered(now);
					if (this.measuring && key.wide) {
						this.caps = { ...this.caps, wide: true };
						this.renewPainter();
					}
					this.measuring = false;
					break;
				default:
					if (key.kind === 'repaint')
						this.painter.forget();
					else if (this.view.press(scan, key))
						quit = true;
					this.pressed = true;
					this.stir(now);
			}
		}
		return quit;
	}
	stir(now) {
		this.due = now;
		this.stirred = now;
	}
	taken(now) {
		this.painter.forget();
		this.pace.restart();
		this.stir(now);
		this.pressed ||= this.view.asking;
		if (!this.pace.asks)
			return '';
		this.written = 0;
		this.measuring = true;
		return `\x1b[H\x1b[8m${spell(RULE_CELL, { ...this.caps, wide: false })}\x1b[0m\x1b[6n`;
	}
	renewPainter() {
		const few = this.caps.colour > Colour.Basic && this.pace.motion === Motion.Bare;
		this.painter = new Painter(few ? { ...this.caps, colour: Colour.Basic } : this.caps);
	}
	frame(scan, cols, rows, now) {
		const { pace } = this;
		const allowed = pace.budget(now);
		const budget = this.view.asking && (this.pressed || this.painter.behind) ? Infinity : allowed;
		if (budget === 0) {
			this.due = now + 0.01;
			return '';
		}
		const { motion } = pace;
		const grid = this.view.draw(scan, { cols, rows, now, motion, slow: pace.slowed });
		if (pace.claimTrial(now))
			this.painter.smudge();
		let out = this.painter.diff(grid, budget, this.pressed);
		this.pressed = false;
		if (out) {
			this.written = Buffer.byteLength(out);
			if (pace.asks)
				out += ASK;
		}
		if (pace.claimPing(now))
			out = ASK + out;
		pace.settle(cols * rows, now);
		if ((pace.motion === Motion.Bare) !== (motion === Motion.Bare))
			this.renewPainter();
		if (scan.running || this.painter.behind)
			this.stirred = now;
		const pause = now - this.stirred < STILL_AFTER ? pace.pause : 0.5;
		this.due = now + (this.painter.behind ? Math.min(pause, CATCH_UP) : pause);
		return out;
	}
}
export class App {
	scan = new Scan([]);
	screen;
	answer(message) {
		const kind = message.toString('utf8', 0, 1);
		const body = message.subarray(1);
		switch (kind) {
			case 'A':
				this.scan = new Scan(readAtlas(body));
				return NOTHING;
			case 'C':
				this.screen = new Screen(parsed(body) ?? {});
				return NOTHING;
			case 'D': {
				const delta = parsed(body);
				if (delta)
					this.scan.apply(delta);
				return NOTHING;
			}
			default:
				return this.screen?.answer(this.scan, kind, body) ?? NOTHING;
		}
	}
}
