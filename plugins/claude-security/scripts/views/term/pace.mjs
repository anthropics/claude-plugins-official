import { whole } from './numbers.mjs';
export const CATCH_UP = 0.15;
const FIRST_BYTES = 2000;
const LEAST_BYTES = 250;
const TELLING_BYTES = 200;
const NOISE = 0.012;
const SILENCE = 1.5;
const LOST_AFTER = 5;
const STEADY_FOR_MORE = 4;
const STEADY_FOR_LESS = 0.6;
const LONGEST_WAIT = 60;
const MARGIN = 1.5;
const TRIAL_EVERY = 5;
const REMEMBERED = 40;
const REMEMBERED_FOR = 4;
const LATENCY_HOLDS = 12;
const PING_EVERY = 2.5;
const FIRST_WINDOW = 2;
const MOST_AHEAD = 5;
const TRUST = 6;
export const Motion = { Bare: 0, Still: 1, Reduced: 2, Full: 3 };
const BYTES_A_CELL = [0, 0.5, 2.5, 12];
const FRAMES_A_SECOND = [2, 2, 8, 20];
export function beatOf({ now, motion }) {
	if (motion === Motion.Full)
		return now;
	return motion === Motion.Reduced ? Math.floor(now * 3) / 3 : undefined;
}
export class Pace {
	most;
	motion;
	answers;
	flying = [];
	trips = [];
	train = { began: 0, size: 0 };
	seen = [];
	wait = STEADY_FOR_MORE;
	tried = 0;
	pinged = 0;
	quick = false;
	leaning;
	constructor(most, remote, asks) {
		this.most = most;
		this.motion = remote && most > Motion.Reduced ? Motion.Reduced : most;
		this.answers = asks ? 'unknown' : 'never';
		this.leaning = { motion: this.motion, since: 0 };
	}
	get slowed() {
		return this.leaning.motion < this.most && this.seen.length > 0;
	}
	get pause() {
		return 1 / FRAMES_A_SECOND[this.motion];
	}
	get asks() {
		return this.answers !== 'never';
	}
	budget(now) {
		const waited = () => now - (this.flying[0]?.began ?? now);
		if (this.answers === 'yes' && waited() > LOST_AFTER) {
			this.flying = [];
			this.answers = 'unknown';
		}
		if (this.answers === 'unknown' && waited() > SILENCE)
			this.answers = 'never';
		if (!this.asks)
			return Infinity;
		const best = this.best();
		if (!best)
			return this.flying.length < FIRST_WINDOW ? FIRST_BYTES : 0;
		const trips = whole(this.latency / Math.min(this.pause, CATCH_UP));
		const share = Math.max((best.quick ? best.rate * TRUST : best.rate) * CATCH_UP, LEAST_BYTES);
		return this.flying.length < 1 + Math.min(trips, MOST_AHEAD) ? share : 0;
	}
	claimTrial(now) {
		const due = this.quick && this.motion < this.most && now - this.tried > TRIAL_EVERY;
		if (due)
			this.tried = now;
		return due;
	}
	claimPing(now) {
		const due = this.answers === 'yes' && now - this.pinged > PING_EVERY;
		if (due) {
			this.pinged = now;
			this.flying.push({ began: now, size: 0 });
		}
		return due;
	}
	sent(size, began, ended) {
		if (this.asks)
			this.flying.push({ began, size });
		else
			this.learn(size, began, ended);
	}
	answered(now) {
		const frame = this.flying.shift();
		if (!frame)
			return;
		const took = now - frame.began;
		const arrived = this.trips.at(-1)?.at ?? 0;
		this.answers = 'yes';
		this.trips = this.trips.filter(trip => trip.took < took && now - trip.at < LATENCY_HOLDS);
		this.trips.push({ took, at: now });
		if (frame.began + this.latency > arrived)
			this.train = { began: frame.began + this.latency, size: 0 };
		this.train.size += frame.size;
		this.learn(this.train.size, this.train.began, now);
	}
	restart() {
		this.flying = [];
	}
	settle(cells, now) {
		const best = this.best();
		if (!best)
			return;
		const wanted = this.wanted(best, cells);
		if (wanted !== this.leaning.motion)
			this.leaning = { motion: wanted, since: now };
		if (now - this.leaning.since >= (wanted > this.motion ? this.wait : STEADY_FOR_LESS)) {
			if (wanted < this.motion)
				this.wait = Math.min(2 * this.wait, LONGEST_WAIT);
			this.motion = wanted;
		}
	}
	wanted({ rate, quick }, cells) {
		const carried = BYTES_A_CELL.filter(bytes => rate >= cells * bytes).length - 1;
		if (carried < this.motion && !quick)
			return Math.max(carried, Motion.Bare);
		const more = Math.min(this.motion + 1, this.most);
		if (rate > cells * BYTES_A_CELL[more] * MARGIN)
			return more;
		return quick && this.leaning.motion > this.motion ? this.leaning.motion : this.motion;
	}
	get latency() {
		return this.trips[0]?.took ?? Infinity;
	}
	best() {
		return this.seen.reduce((best, one) => (best && best.rate > one.rate ? best : one), undefined);
	}
	learn(size, began, ended) {
		this.quick = ended - began < NOISE;
		if (size < TELLING_BYTES)
			return;
		const recent = this.seen.filter(seen => ended - seen.ended < REMEMBERED_FOR);
		recent.push({ rate: size / Math.max(ended - began, NOISE), quick: this.quick, ended });
		this.seen = recent.slice(-REMEMBERED);
	}
}
