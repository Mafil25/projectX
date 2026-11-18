(() => {
    'use strict';
    const configs = JSON.parse(document.getElementById('level-task-data').textContent);
    const workerUrl = document.currentScript.dataset.workerUrl;
    const userId = document.body.dataset.userId;

    function waitForMessage(worker, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const timer = setTimeout(() => {
                cleanup();
                reject(new Error('Превышено время выполнения'));
            }, timeout);
            function cleanup() {
                clearTimeout(timer);
                worker.removeEventListener('message', onMessage);
                worker.removeEventListener('error', onError);
            }
            function onMessage(event) {
                cleanup();
                if (event.data.type === 'error') reject(new Error(event.data.message || 'Ошибка Python'));
                else resolve(event.data);
            }
            function onError(event) {
                cleanup();
                reject(new Error(event.message || 'Ошибка Python Worker'));
            }
            worker.addEventListener('message', onMessage);
            worker.addEventListener('error', onError);
        });
    }

    async function createWorker() {
        const worker = new Worker(workerUrl);
        try {
            const response = await waitForMessage(worker, 60000);
            if (response.type !== 'ready') throw new Error('Не удалось загрузить Python');
            return worker;
        } catch (error) {
            worker.terminate();
            throw error;
        }
    }

    async function execute(worker, code, input, functionName) {
        const responsePromise = waitForMessage(worker);
        worker.postMessage({type: 'run', code, input, functionName});
        const response = await responsePromise;
        if (response.type !== 'result') throw new Error('Неожиданный ответ Python');
        return response.output;
    }

    class TaskEditor {
        constructor(config) {
            this.config = config;
            this.root = document.getElementById(`task-${config.id}`);
            this.fallback = this.root.querySelector('[data-code-fallback]');
            this.container = this.root.querySelector('[data-code-editor]');
            this.input = this.root.querySelector('[data-python-input]');
            this.output = this.root.querySelector('[data-python-output]');
            this.status = this.root.querySelector('[data-test-status]');
            this.runButton = this.root.querySelector('[data-run]');
            this.checkButton = this.root.querySelector('[data-check]');
            this.editor = null;
            this.busy = false;
            this.draftKey = `projectx:code:${userId}:${config.id}`;
            let code = config.starterCode || '# Напишите решение здесь\n';
            try { code = sessionStorage.getItem(this.draftKey) ?? code; } catch (error) {}
            this.fallback.value = code;
            this.fallback.addEventListener('input', () => this.saveDraft(this.fallback.value));
            this.fallback.addEventListener('keydown', event => {
                if (event.key !== 'Tab' || event.shiftKey) return;
                event.preventDefault();
                this.fallback.setRangeText('    ', this.fallback.selectionStart, this.fallback.selectionEnd, 'end');
                this.saveDraft(this.fallback.value);
            });
            this.runButton.addEventListener('click', () => this.run());
            this.checkButton.addEventListener('click', () => this.check());
        }

        saveDraft(code) {
            try { sessionStorage.setItem(this.draftKey, code); } catch (error) {}
        }

        mountMonaco(monaco) {
            this.container.hidden = false;
            try {
                this.editor = monaco.editor.create(this.container, {
                    value: this.fallback.value, language: 'python', theme: 'vs-dark',
                    automaticLayout: true, minimap: {enabled: false}, fontSize: 15,
                    lineHeight: 24, tabSize: 4, insertSpaces: true, wordWrap: 'on',
                    fontFamily: "Consolas, 'Courier New', monospace",
                    scrollBeyondLastLine: false, padding: {top: 16, bottom: 16},
                });
                this.editor.onDidChangeModelContent(() => this.saveDraft(this.editor.getValue()));
                this.fallback.hidden = true;
                this.root.querySelector('[data-editor-state]').textContent = 'Monaco Editor · Python 3';
                this.root.querySelector('.editor-heading label').addEventListener('click', () => this.editor.focus());
            } catch (error) {
                this.editor = null;
                this.container.hidden = true;
            }
        }

        getCode() {
            return this.editor ? this.editor.getValue() : this.fallback.value;
        }

        setBusy(value) {
            this.busy = value;
            this.runButton.disabled = value;
            this.checkButton.disabled = value;
            this.root.setAttribute('aria-busy', String(value));
        }

        async run() {
            if (this.busy) return;
            this.setBusy(true);
            this.output.textContent = 'Загрузка Python...';
            const code = this.getCode();
            const input = this.input.value;
            let worker = null;
            try {
                worker = await createWorker();
                const output = await execute(worker, code, input, this.config.functionName);
                this.output.textContent = output || 'Программа завершилась без вывода.';
            } catch (error) {
                this.output.textContent = '❌ ' + error.message;
            } finally {
                if (worker) worker.terminate();
                this.setBusy(false);
            }
        }

        async check() {
            if (this.busy) return;
            this.setBusy(true);
            const code = this.getCode();
            const {tests, functionName, completeUrl} = this.config;
            this.status.textContent = 'Подготовка проверки...';
            try {
                if (!Array.isArray(tests) || !tests.length) throw new Error('Для задания не заданы тесты.');
                for (let index = 0; index < tests.length; index++) {
                    const test = tests[index];
                    const valid = test && (functionName
                        ? Array.isArray(test.input) && Object.prototype.hasOwnProperty.call(test, 'expected')
                        : typeof test.input === 'string' && typeof test.output === 'string');
                    if (!valid) throw new Error(`Неверный формат теста ${index + 1}`);
                    this.status.textContent = `Проверка ${index + 1}/${tests.length}...`;
                    let worker = null;
                    try {
                        worker = await createWorker();
                        const input = functionName ? JSON.stringify(test.input) : test.input;
                        const output = await execute(worker, code, input, functionName);
                        const actual = functionName ? JSON.parse(output) : output.trim();
                        const expected = functionName ? test.expected : test.output.trim();
                        if (!resultsEqual(actual, expected)) {
                            this.status.textContent = `❌ Тест ${index + 1} не пройден\nВход: ${input}\nОжидалось: ${JSON.stringify(expected)}\nПолучено: ${JSON.stringify(actual)}`;
                            return;
                        }
                    } catch (error) {
                        throw new Error(`Тест ${index + 1}: ${error.message}`);
                    } finally {
                        if (worker) worker.terminate();
                    }
                }
                this.status.textContent = `✓ Пройдено ${tests.length}/${tests.length} тестов. Сохранение...`;
                const response = await fetch(completeUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: JSON.stringify({passed: true}),
                });
                if (!response.ok) throw new Error('Тесты пройдены, но не удалось сохранить результат. Повтори проверку.');
                const result = await response.json();
                if (result.success !== true) throw new Error('Не удалось сохранить результат.');
                updateLevelCompletion(result);
                this.status.textContent = `✓ Пройдено ${tests.length}/${tests.length} тестов. Задание выполнено, результат сохранён!`;
                if (document.getElementById('level-completion-status').classList.contains('completed')) {
                    document.getElementById('level-summary').scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            } catch (error) {
                this.status.textContent = '❌ ' + error.message;
            } finally {
                this.setBusy(false);
            }
        }
    }

    function loadMonaco() {
        return new Promise(resolve => {
            const timer = setTimeout(() => resolve(null), 8000);
            function done(value) { clearTimeout(timer); resolve(value); }
            function initialize() {
                if (typeof window.require !== 'function') { done(null); return; }
                const base = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs';
                window.require.config({paths: {vs: base}});
                window.MonacoEnvironment = {
                    getWorkerUrl() {
                        const source = `self.MonacoEnvironment = {baseUrl: '${base}/'}; importScripts('${base}/base/worker/workerMain.js');`;
                        return URL.createObjectURL(new Blob([source], {type: 'text/javascript'}));
                    },
                };
                window.require(['vs/editor/editor.main'], () => done(window.monaco), () => done(null));
            }
            if (window.monaco) { done(window.monaco); return; }
            if (typeof window.require === 'function') { initialize(); return; }
            const loader = document.createElement('script');
            loader.src = 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.2/min/vs/loader.min.js';
            loader.onload = initialize;
            loader.onerror = () => done(null);
            document.head.appendChild(loader);
        });
    }

    const editors = configs.map(config => new TaskEditor(config));
    if (editors.length) {
        loadMonaco().then(monaco => {
            if (monaco) editors.forEach(editor => editor.mountMonaco(monaco));
        });
        const links = Array.from(document.querySelectorAll('[data-task-link]'));
        let scheduled = false;
        function highlightCurrentTask() {
            scheduled = false;
            let current = editors[0];
            for (const editor of editors) {
                if (editor.root.getBoundingClientRect().top <= Math.min(180, window.innerHeight * .3)) current = editor;
                else break;
            }
            links.forEach(link => {
                if (link.dataset.taskLink === String(current.config.id)) link.setAttribute('aria-current', 'location');
                else link.removeAttribute('aria-current');
            });
        }
        window.addEventListener('scroll', () => {
            if (!scheduled) { scheduled = true; requestAnimationFrame(highlightCurrentTask); }
        }, {passive: true});
        window.addEventListener('resize', highlightCurrentTask);
        highlightCurrentTask();
    }
})();
