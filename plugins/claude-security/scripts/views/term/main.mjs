import { readSync, writeSync } from 'node:fs';
import { App } from './app.mjs';
const LENGTH_BYTES = 4;
function move(step, fd, bytes) {
	for (let at = 0; at < bytes.length;) {
		const moved = step(fd, bytes, at, bytes.length - at, null);
		if (!moved)
			process.exit(0);
		at += moved;
	}
	return bytes;
}
const app = new App();
for (;;) {
	const size = move(readSync, 0, Buffer.allocUnsafe(LENGTH_BYTES)).readUInt32LE(0);
	const answer = app.answer(move(readSync, 0, Buffer.allocUnsafe(size)));
	const framed = Buffer.allocUnsafe(LENGTH_BYTES + answer.length);
	framed.writeUInt32LE(answer.length, 0);
	framed.set(answer, LENGTH_BYTES);
	move(writeSync, 1, framed);
}
