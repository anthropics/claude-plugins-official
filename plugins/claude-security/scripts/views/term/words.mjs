import { nearest, whole } from './numbers.mjs';
import { lowerAscii } from './text.mjs';
export const lens = (name) => lowerAscii(name.split('-')[0]).replace(/^[a-z]/, letter => letter.toUpperCase());
export function short(severity) {
	if (severity === 'CRITICAL')
		return 'CRIT';
	return severity === 'MEDIUM' ? 'MED' : severity;
}
export const listed = (parts, gap) => parts.filter(Boolean).join(gap);
export const noun = (n, many) => (n === 1 ? many.replace(/s$/, '') : many);
const two = (n) => String(n).padStart(2, '0');
export function clock(seconds) {
	const minutes = whole(whole(seconds) / 60);
	const rest = two(whole(seconds) % 60);
	return minutes >= 60 ? `${whole(minutes / 60)}:${two(minutes % 60)}:${rest}` : `${minutes}:${rest}`;
}
export const grouped = (n) => String(n).replace(/\B(?=(\d{3})+$)/g, ',');
function threeFigures(value, unit) {
	const places = [99.95, 9.995].filter(limit => value < limit).length;
	const tie = (value * 2 ** (places + 1)) % 2 === 1;
	return (tie ? nearest(value * 10 ** places) / 10 ** places : value).toFixed(places) + unit;
}
export function count(n) {
	if (n < 100_000)
		return grouped(n);
	if (n < 999_500)
		return threeFigures(n / 1e3, 'k');
	return n < 999_500_000 ? threeFigures(n / 1e6, 'M') : threeFigures(n / 1e9, 'B');
}
export const percent = (read, lines) => lines === 0 ? '' : `${Math.min(whole((100 * read) / lines), 100)}%`;
