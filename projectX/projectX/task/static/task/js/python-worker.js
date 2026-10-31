importScripts(
    "https://cdn.jsdelivr.net/pyodide/v0.29.5/full/pyodide.js"
);

let pyodide;

async function init() {
    try {
        pyodide = await loadPyodide();

        self.postMessage({
            type: "ready"
        });
    } catch (error) {
        self.postMessage({
            type: "error",
            message: String(error)
        });
    }
}

self.onmessage = async function (event) {
    if (event.data.type !== "run" || !pyodide) {
        return;
    }

    const { code, input } = event.data;

    try {
        pyodide.globals.set("USER_CODE", code);
        pyodide.globals.set("TEST_INPUT", input);

        const output = await pyodide.runPythonAsync(`
import sys
import io
import contextlib

input_stream = io.StringIO(TEST_INPUT)
output_stream = io.StringIO()

old_stdin = sys.stdin

try:
    sys.stdin = input_stream

    with contextlib.redirect_stdout(output_stream):
        exec(
            compile(USER_CODE, "<solution>", "exec"),
            {"__name__": "__main__"}
        )
finally:
    sys.stdin = old_stdin

output_stream.getvalue()
        `);

        self.postMessage({
            type: "result",
            output: output
        });

    } catch (error) {
        self.postMessage({
            type: "error",
            message: String(error)
        });
    }
};

init();