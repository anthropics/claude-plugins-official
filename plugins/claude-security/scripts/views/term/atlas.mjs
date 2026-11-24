import { sum } from './numbers.mjs';
const AREA_EXPONENT = 0.7;
export function plotOf(path, lines, outline) {
	return { path, lines, outline, weight: Math.max(lines, 4) ** AREA_EXPONENT };
}
export function readAtlas(bytes) {
	const count = bytes.length < 4 ? 0 : bytes.readUInt32LE(0);
	const plots = [];
	let at = 4;
	while (plots.length < count && at + 2 <= bytes.length) {
		const named = at + 2 + bytes.readUInt16LE(at);
		if (named + 6 > bytes.length)
			break;
		const end = named + 6 + 2 * bytes.readUInt16LE(named + 4);
		if (end > bytes.length)
			break;
		plots.push(plotOf(bytes.toString('utf8', at + 2, named), bytes.readUInt32LE(named), bytes.subarray(named + 6, end)));
		at = end;
	}
	return plots;
}
function inset({ x, y, w, h }, most) {
	const pad = Math.min(most, w / 8, h / 8);
	return { x: x + pad, y: y + pad, w: w - 2 * pad, h: h - 2 * pad };
}
function tree(plots, chosen) {
	const root = { weight: 0, folders: new Map(), files: [] };
	for (const plot of chosen) {
		const { path, weight } = plots[plot];
		let folder = root;
		folder.weight += weight;
		for (const name of path.split('/').slice(0, -1)) {
			const inner = folder.folders.get(name) ?? { weight: 0, folders: new Map(), files: [] };
			folder.folders.set(name, inner);
			folder = inner;
			folder.weight += weight;
		}
		folder.files.push({ weight, plot });
	}
	return root;
}
export function layout(plots, chosen, w, h, pad) {
	const tiles = [];
	const stack = [[tree(plots, chosen), { x: 0, y: 0, w, h }]];
	for (let top = stack.pop(); top; top = stack.pop()) {
		const [item, area] = top;
		if ('plot' in item) {
			tiles.push([item.plot, area]);
			continue;
		}
		const items = [...item.folders.values(), ...item.files].sort((a, b) => b.weight - a.weight);
		const areas = divide(items.map(inner => inner.weight), inset(area, pad));
		for (let n = items.length - 1; n >= 0; n--)
			stack.push([items[n], areas[n]]);
	}
	return tiles;
}
export function divide(weights, area) {
	let { x, y, w, h } = area;
	const total = sum(weights);
	if (!(total > 0 && w > 0 && h > 0))
		return weights.map(() => ({ x, y, w: 0, h: 0 }));
	const scale = (w * h) / total;
	const pieces = weights.map(weight => weight * scale);
	const out = [];
	let start = 0;
	while (start < pieces.length) {
		const side = Math.min(w, h);
		const largest = pieces[start];
		let row = largest;
		let end = start + 1;
		while (end < pieces.length &&
			worst(row + pieces[end], largest, pieces[end], side) <= worst(row, largest, pieces[end - 1], side)) {
			row += pieces[end];
			end++;
		}
		const depth = side === 0 ? 0 : row / side;
		let offset = 0;
		for (let n = start; n < end; n++) {
			const length = depth === 0 ? 0 : pieces[n] / depth;
			out.push(w >= h ? { x, y: y + offset, w: depth, h: length } : { x: x + offset, y, w: length, h: depth });
			offset += length;
		}
		if (w >= h) {
			x += depth;
			w -= depth;
		}
		else {
			y += depth;
			h -= depth;
		}
		start = end;
	}
	return out;
}
function worst(total, largest, least, side) {
	return Math.max((side * side * largest) / (total * total), (total * total) / (side * side * least));
}
