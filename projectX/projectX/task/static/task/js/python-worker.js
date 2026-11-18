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

    const { code, input, functionName = "" } = event.data;

    try {
        pyodide.globals.set("USER_CODE", code);
        pyodide.globals.set("TEST_INPUT", input);
        pyodide.globals.set("FUNCTION_NAME", functionName);

        const output = await pyodide.runPythonAsync(`
import sys
import io
import contextlib
import json

input_stream = io.StringIO(TEST_INPUT)
output_stream = io.StringIO()

old_stdin = sys.stdin
function_result = None

try:
    sys.stdin = input_stream

    with contextlib.redirect_stdout(output_stream):
        namespace = {"__name__": "__main__"}
        exec(
            compile(USER_CODE, "<solution>", "exec"),
            namespace
        )
        if FUNCTION_NAME:
            arguments = json.loads(TEST_INPUT)
            if not isinstance(arguments, list):
                raise ValueError("Аргументы функции должны быть JSON-массивом, например [2, 3]")
            function = namespace.get(FUNCTION_NAME)
            if not callable(function):
                raise ValueError("Не найдена функция " + FUNCTION_NAME)
            function_result = json.dumps(function(*arguments), ensure_ascii=False, sort_keys=True, allow_nan=False)
finally:
    sys.stdin = old_stdin

function_result if FUNCTION_NAME else output_stream.getvalue()
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
