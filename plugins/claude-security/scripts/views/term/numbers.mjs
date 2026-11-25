const LARGEST_INT = 2 ** 31 - 1;
export function nearest(value) {
	const up = Math.round(value);
	return up - value === 0.5 && up % 2 !== 0 ? up - 1 : up;
}
export const clamp = (value, low, high) => Math.min(Math.max(value, low), high);
export const round = (value) => clamp(nearest(value), -LARGEST_INT - 1, LARGEST_INT) | 0;
export const tenths = (value) => nearest(value * 10) / 10;
export const whole = (value) => (value > 0 ? Math.min(Math.floor(value), Number.MAX_SAFE_INTEGER) : 0);
export const div = (a, b) => (a / b) | 0;
export const sum = (values) => values.reduce((a, b) => a + b, 0);
export function partition(items, before) {
	let low = 0;
	let high = items.length;
	while (low < high) {
		const middle = (low + high) >> 1;
		if (before(items[middle]))
			low = middle + 1;
		else
			high = middle;
	}
	return low;
}
