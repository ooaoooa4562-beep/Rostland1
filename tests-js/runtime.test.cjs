const assert = require("node:assert/strict");
require("../launcher-web/runtime.js");
function run(source) {
  const output = [];
  const runtime = new globalThis.RostRuntime({ print: value => output.push(value) });
  runtime.run(source);
  return output;
}
assert.deepEqual(run('make x = 6 * 7\nsay x'), ["42"]);
assert.deepEqual(run('when 5 > 2 {\n say "yes"\n} otherwise {\n say "no"\n}'), ["yes"]);
assert.deepEqual(run('repeat 2 {\n say "go"\n}'), ["go", "go"]);
assert.deepEqual(run('action add(a, b) {\n return a + b\n}\nsay add(4, 5)'), ["9"]);
assert.deepEqual(run('make xs = ["a"]\ncall append(xs, "b")\nsay xs[1]'), ["b"]);
assert.deepEqual(run('make i = 0\nwhile i < 3 {\n say i\n change i = i + 1\n}'), ["0", "1", "2"]);
assert.deepEqual(run('for item in [1, 2, 3] {\n print(item)\n}'), ["1", "2", "3"]);
console.log("RostLang JS smoke tests passed.");
