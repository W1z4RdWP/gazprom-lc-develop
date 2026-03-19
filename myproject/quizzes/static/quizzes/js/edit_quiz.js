document.addEventListener('DOMContentLoaded', function () {

    const container = document.getElementById('questions-container');
    const addQuestionBtn = document.getElementById('add-question-btn');
    const questionsCountInput = document.getElementById('questions-count-input');
    const countBadge = document.getElementById('questions-count');
    const emptyState = document.getElementById('empty-state');

    /* ============ Переиндексация ============
     * Вызывается после каждого добавления / удаления вопроса или ответа.
     * Обновляет все атрибуты name, порядковые номера и счётчики. */
    function reindex() {
        const cards = container.querySelectorAll('.eq-question-card');
        const count = cards.length;
        questionsCountInput.value = count;
        countBadge.textContent = count;
        if (emptyState) emptyState.style.display = count ? 'none' : '';

        cards.forEach((card, qi) => {
            card.dataset.questionIndex = qi;
            card.querySelector('.eq-question-number').textContent = qi + 1;

            setName(card, 'input[name^="q_id_"]',       `q_id_${qi}`);
            setName(card, 'input[name^="q_text_"]',     `q_text_${qi}`);
            setName(card, 'select[name^="q_type_"]',    `q_type_${qi}`);

            const answersCountInput = card.querySelector('input[name^="answers_count_"]');
            answersCountInput.name = `answers_count_${qi}`;

            const rows = card.querySelectorAll('.eq-answer-row');
            answersCountInput.value = rows.length;

            rows.forEach((row, ai) => {
                setName(row, 'input[name^="a_id_"]',      `a_id_${qi}_${ai}`);
                setName(row, 'input[name^="a_text_"]',    `a_text_${qi}_${ai}`);
                setName(row, 'input[name^="a_correct_"]', `a_correct_${qi}_${ai}`);
            });
        });
    }

    function setName(scope, selector, newName) {
        const el = scope.querySelector(selector);
        if (el) el.name = newName;
    }

    /* ============ Создание новой строки ответа ============ */
    function createAnswerRow(qi, ai, questionType) {
        const row = document.createElement('div');
        row.className = 'eq-answer-row';
        row.innerHTML = `
            <input type="hidden" name="a_id_${qi}_${ai}" value="">
            <input type="checkbox" class="eq-correct-toggle js-answer-correct"
                   name="a_correct_${qi}_${ai}" title="Правильный ответ">
            <input type="text" class="eq-answer-input"
                   name="a_text_${qi}_${ai}" value="" placeholder="Текст ответа...">
            <button type="button" class="eq-icon-btn eq-delete js-delete-answer" title="Удалить ответ">
                <i class="bi bi-x-lg"></i>
            </button>
        `;
        return row;
    }

    /* ============ Создание новой карточки вопроса ============ */
    function createQuestionCard(qi) {
        const card = document.createElement('div');
        card.className = 'eq-question-card';
        card.dataset.questionIndex = qi;
        card.dataset.questionType = 'single';
        card.innerHTML = `
            <input type="hidden" name="q_id_${qi}" value="">
            <div class="eq-question-header">
                <div class="eq-question-number">${qi + 1}</div>
                <div class="eq-question-body">
                    <input type="text" class="eq-inline-input"
                           name="q_text_${qi}" value="" placeholder="Текст вопроса..." required>
                    <div class="mt-1">
                        <select class="eq-type-select js-question-type" name="q_type_${qi}">
                            <option value="single" selected>Один правильный ответ</option>
                            <option value="multiple">Несколько правильных ответов</option>
                        </select>
                    </div>
                </div>
                <div class="eq-question-actions">
                    <button type="button" class="eq-icon-btn eq-delete js-delete-question" title="Удалить вопрос">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
            <div class="eq-answers-section js-answers-container">
                <input type="hidden" name="answers_count_${qi}" value="0">
                <button type="button" class="eq-add-answer-btn js-add-answer">
                    <i class="bi bi-plus-circle"></i> Добавить ответ
                </button>
            </div>
        `;
        return card;
    }

    /* ============ Добавление вопроса ============ */
    addQuestionBtn.addEventListener('click', function () {
        if (emptyState) emptyState.style.display = 'none';
        const qi = container.querySelectorAll('.eq-question-card').length;
        const card = createQuestionCard(qi);
        if (emptyState && emptyState.parentNode === container) {
            container.insertBefore(card, emptyState);
        } else {
            container.appendChild(card);
        }
        reindex();
        card.querySelector('input[name^="q_text_"]').focus();
    });

    /* ============ Делегирование кликов ============ */
    container.addEventListener('click', function (e) {
        const btn = e.target.closest('button');
        if (!btn) return;

        if (btn.classList.contains('js-delete-question')) {
            if (!confirm('Удалить вопрос и все его ответы?')) return;
            btn.closest('.eq-question-card').remove();
            reindex();
        }

        if (btn.classList.contains('js-add-answer')) {
            const card = btn.closest('.eq-question-card');
            const qi = parseInt(card.dataset.questionIndex);
            const questionType = card.dataset.questionType || 'single';
            const answersContainer = card.querySelector('.js-answers-container');
            const ai = answersContainer.querySelectorAll('.eq-answer-row').length;
            const row = createAnswerRow(qi, ai, questionType);
            answersContainer.insertBefore(row, btn);
            reindex();
            row.querySelector('input[name^="a_text_"]').focus();
        }

        if (btn.classList.contains('js-delete-answer')) {
            btn.closest('.eq-answer-row').remove();
            reindex();
        }
    });

    /* ============ Смена типа вопроса ============ */
    container.addEventListener('change', function (e) {
        if (e.target.classList.contains('js-question-type')) {
            const card = e.target.closest('.eq-question-card');
            const newType = e.target.value;
            card.dataset.questionType = newType;

            // Для single-типа снимаем все отметки кроме первой выбранной
            if (newType === 'single') {
                let found = false;
                card.querySelectorAll('.js-answer-correct').forEach(inp => {
                    if (inp.checked && !found) {
                        found = true;
                    } else {
                        inp.checked = false;
                    }
                });
            }
        }

        // Для single-вопросов — поведение как у radio (только один выбранный ответ)
        if (e.target.classList.contains('js-answer-correct')) {
            const card = e.target.closest('.eq-question-card');
            if ((card.dataset.questionType || 'single') === 'single' && e.target.checked) {
                card.querySelectorAll('.js-answer-correct').forEach(inp => {
                    if (inp !== e.target) inp.checked = false;
                });
            }
        }
    });

    /* Первичная нумерация */
    reindex();
});
