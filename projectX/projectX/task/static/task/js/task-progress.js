function resultsEqual(actual, expected) {
    if (actual === expected) return true;
    if (actual === null || expected === null || typeof actual !== 'object' || typeof expected !== 'object') return false;
    if (Array.isArray(actual) !== Array.isArray(expected)) return false;
    const actualKeys = Object.keys(actual);
    const expectedKeys = Object.keys(expected);
    return actualKeys.length === expectedKeys.length && actualKeys.every(key =>
        Object.prototype.hasOwnProperty.call(expected, key) && resultsEqual(actual[key], expected[key])
    );
}

function updateLevelCompletion(result) {
    const completedIds = new Set(result.completed_task_ids.map(String));
    // Two exercise checks may finish in a different order than their requests.
    document.querySelectorAll('.sidebar-task.is-completed').forEach(link => completedIds.add(link.dataset.taskLink));
    const completedCount = completedIds.size;
    const isCompleted = result.total_tasks > 0 && completedCount === result.total_tasks;
    document.querySelectorAll('[data-task-link]').forEach(link => {
        const completed = completedIds.has(link.dataset.taskLink);
        link.classList.toggle('is-completed', completed);
        const status = link.querySelector('[data-task-status]');
        status.textContent = completed ? '✓' : '○';
        status.setAttribute('aria-label', completed ? 'Выполнено' : 'Не выполнено');
    });
    document.getElementById('level-completed-count').textContent = completedCount;
    document.querySelectorAll('[data-task-badge], [data-task-summary]').forEach(label => {
        const completed = completedIds.has(label.dataset.taskBadge || label.dataset.taskSummary);
        label.textContent = completed ? '✓ Выполнено' : 'Ещё не выполнено';
        label.classList.toggle('completed', completed);
    });
    document.getElementById('level-total-count').textContent = result.total_tasks;
    const summary = document.getElementById('level-completion-status');
    summary.textContent = isCompleted
        ? '✓ Уровень завершён'
        : 'Выполни все задания, чтобы завершить уровень.';
    summary.classList.toggle('completed', isCompleted);
}
