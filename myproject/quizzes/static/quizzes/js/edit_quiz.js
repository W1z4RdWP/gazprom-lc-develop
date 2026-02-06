document.addEventListener('DOMContentLoaded', function () {

    const toastEl = document.getElementById('eq-toast');
    const container = document.getElementById('questions-container');
    const addQuestionBtn = document.getElementById('add-question-btn');
    const emptyState = document.getElementById('empty-state');
    const countBadge = document.getElementById('questions-count');

    /* ============ Утилиты ============ */

    function apiCall(url, body) {
        return fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF,
            },
            body: JSON.stringify(body),
        }).then(r => {
            if (!r.ok) return r.json().then(d => Promise.reject(d));
            return r.json();
        });
    }

    function toast(msg, type) {
        toastEl.textContent = msg;
        toastEl.className = 'eq-toast ' + type + ' show';
        clearTimeout(toastEl._t);
        toastEl._t = setTimeout(() => toastEl.classList.remove('show'), 2500);
    }

    function updateNumbers() {
        const cards = container.querySelectorAll('.eq-question-card');
        cards.forEach((c, i) => {
            c.querySelector('.eq-question-number').textContent = i + 1;
        });
        countBadge.textContent = cards.length;
        // показать / скрыть пустое состояние
        if (emptyState) {
            emptyState.style.display = cards.length ? 'none' : '';
        }
    }

    /* ============ Шаблоны ============ */

    function createAnswerRow(id, text, isCorrect, questionType, questionId) {
        const row = document.createElement('div');
        row.className = 'eq-answer-row';
        row.dataset.answerId = id;
        const inputType = questionType === 'multiple' ? 'checkbox' : 'radio';
        const nameAttr = questionType === 'single' ? `name="question_${questionId}"` : '';
        row.innerHTML = `
            <input type="${inputType}" class="eq-correct-toggle js-answer-correct"
                   ${nameAttr} ${isCorrect ? 'checked' : ''} title="Правильный ответ">
            <input type="text" class="eq-answer-input js-answer-text"
                   value="${escHtml(text)}" data-original="${escHtml(text)}" placeholder="Текст ответа...">
            <button class="eq-icon-btn eq-save js-save-answer" title="Сохранить ответ">
                <i class="bi bi-check-lg"></i>
            </button>
            <button class="eq-icon-btn eq-delete js-delete-answer" title="Удалить ответ">
                <i class="bi bi-x-lg"></i>
            </button>
        `;
        return row;
    }

    function createQuestionCard(id, text, type, num) {
        const card = document.createElement('div');
        card.className = 'eq-question-card';
        card.dataset.questionId = id;
        card.dataset.questionType = type;
        card.innerHTML = `
            <div class="eq-question-header">
                <div class="eq-question-number">${num}</div>
                <div class="eq-question-body">
                    <input type="text" class="eq-inline-input js-question-text"
                           value="${escHtml(text)}" data-original="${escHtml(text)}" placeholder="Текст вопроса...">
                    <div class="mt-1">
                        <select class="eq-type-select js-question-type" data-original="${type}">
                            <option value="single" ${type === 'single' ? 'selected' : ''}>Один правильный ответ</option>
                            <option value="multiple" ${type === 'multiple' ? 'selected' : ''}>Несколько правильных ответов</option>
                        </select>
                    </div>
                </div>
                <div class="eq-question-actions">
                    <button class="eq-icon-btn eq-save js-save-question" title="Сохранить вопрос">
                        <i class="bi bi-check-lg"></i>
                    </button>
                    <button class="eq-icon-btn eq-delete js-delete-question" title="Удалить вопрос">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
            <div class="eq-answers-section js-answers-container">
                <button class="eq-add-answer-btn js-add-answer">
                    <i class="bi bi-plus-circle"></i> Добавить ответ
                </button>
            </div>
        `;
        return card;
    }

    function escHtml(s) {
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    /* ============ Добавление вопроса ============ */

    addQuestionBtn.addEventListener('click', function () {
        const num = container.querySelectorAll('.eq-question-card').length + 1;
        const url = `/quizzes/${QUIZ_ID}/api/question/add/`;
        apiCall(url, { text: 'Новый вопрос', question_type: 'single' })
            .then(data => {
                if (emptyState) emptyState.style.display = 'none';
                const card = createQuestionCard(data.id, data.text, data.question_type, num);
                // Вставляем перед пустым состоянием или в конец
                if (emptyState) {
                    container.insertBefore(card, emptyState);
                } else {
                    container.appendChild(card);
                }
                updateNumbers();
                // Фокус на текст нового вопроса
                const inp = card.querySelector('.js-question-text');
                inp.focus();
                inp.select();
                toast('Вопрос добавлен', 'success');
            })
            .catch(e => toast(e.error || 'Ошибка при добавлении вопроса', 'error'));
    });

    /* ============ Делегирование событий ============ */

    container.addEventListener('click', function (e) {
        const btn = e.target.closest('button');
        if (!btn) return;

        // --- Сохранить вопрос ---
        if (btn.classList.contains('js-save-question')) {
            const card = btn.closest('.eq-question-card');
            const qId = card.dataset.questionId;
            const textInp = card.querySelector('.js-question-text');
            const typeInp = card.querySelector('.js-question-type');
            const oldType = card.dataset.questionType;
            const newType = typeInp.value;
            apiCall(`/quizzes/${QUIZ_ID}/api/question/${qId}/update/`, {
                text: textInp.value,
                question_type: newType,
            }).then(data => {
                textInp.dataset.original = data.text;
                typeInp.dataset.original = data.question_type;
                card.dataset.questionType = data.question_type;
                // Если тип вопроса изменился, перерисовываем все ответы
                if (oldType !== newType) {
                    const answersContainer = card.querySelector('.js-answers-container');
                    const answerRows = answersContainer.querySelectorAll('.eq-answer-row');
                    let firstCorrectFound = false;
                    
                    // Если переключаемся на single, оставляем только первый правильный ответ
                    if (newType === 'single' && oldType === 'multiple') {
                        answerRows.forEach((row, index) => {
                            const correctInp = row.querySelector('.js-answer-correct');
                            if (correctInp.checked && !firstCorrectFound) {
                                firstCorrectFound = true;
                            } else if (correctInp.checked && firstCorrectFound) {
                                // Снимаем отметку с остальных правильных ответов
                                correctInp.checked = false;
                                const aId = row.dataset.answerId;
                                const textInp = row.querySelector('.js-answer-text');
                                apiCall(`/quizzes/${QUIZ_ID}/api/answer/${aId}/update/`, {
                                    text: textInp.value,
                                    is_correct: false,
                                }).catch(() => {});
                            }
                        });
                    }
                    
                    // Перерисовываем все ответы с новым типом input
                    answerRows.forEach(row => {
                        const aId = row.dataset.answerId;
                        const textInp = row.querySelector('.js-answer-text');
                        const correctInp = row.querySelector('.js-answer-correct');
                        const isCorrect = correctInp.checked;
                        const newRow = createAnswerRow(aId, textInp.value, isCorrect, newType, qId);
                        row.replaceWith(newRow);
                    });
                }
                toast('Вопрос сохранён', 'success');
            }).catch(e => toast(e.error || 'Ошибка сохранения', 'error'));
        }

        // --- Удалить вопрос ---
        if (btn.classList.contains('js-delete-question')) {
            const card = btn.closest('.eq-question-card');
            const qId = card.dataset.questionId;
            if (!confirm('Удалить вопрос и все его ответы?')) return;
            apiCall(`/quizzes/${QUIZ_ID}/api/question/${qId}/delete/`, {})
                .then(() => {
                    card.remove();
                    updateNumbers();
                    toast('Вопрос удалён', 'success');
                })
                .catch(e => toast(e.error || 'Ошибка удаления', 'error'));
        }

        // --- Добавить ответ ---
        if (btn.classList.contains('js-add-answer')) {
            const card = btn.closest('.eq-question-card');
            const qId = card.dataset.questionId;
            const questionType = card.dataset.questionType || 'single';
            const answersContainer = card.querySelector('.js-answers-container');
            apiCall(`/quizzes/${QUIZ_ID}/api/question/${qId}/answer/add/`, {
                text: 'Новый ответ',
                is_correct: false,
            }).then(data => {
                const row = createAnswerRow(data.id, data.text, data.is_correct, questionType, qId);
                answersContainer.insertBefore(row, btn);
                const inp = row.querySelector('.js-answer-text');
                inp.focus();
                inp.select();
                toast('Ответ добавлен', 'success');
            }).catch(e => toast(e.error || 'Ошибка добавления ответа', 'error'));
        }

        // --- Сохранить ответ ---
        if (btn.classList.contains('js-save-answer')) {
            const row = btn.closest('.eq-answer-row');
            const aId = row.dataset.answerId;
            const textInp = row.querySelector('.js-answer-text');
            const correctInp = row.querySelector('.js-answer-correct');
            apiCall(`/quizzes/${QUIZ_ID}/api/answer/${aId}/update/`, {
                text: textInp.value,
                is_correct: correctInp.checked,
            }).then(data => {
                textInp.dataset.original = data.text;
                toast('Ответ сохранён', 'success');
            }).catch(e => toast(e.error || 'Ошибка сохранения ответа', 'error'));
        }

        // --- Удалить ответ ---
        if (btn.classList.contains('js-delete-answer')) {
            const row = btn.closest('.eq-answer-row');
            const aId = row.dataset.answerId;
            if (!confirm('Удалить этот ответ?')) return;
            apiCall(`/quizzes/${QUIZ_ID}/api/answer/${aId}/delete/`, {})
                .then(() => {
                    row.remove();
                    toast('Ответ удалён', 'success');
                })
                .catch(e => toast(e.error || 'Ошибка удаления ответа', 'error'));
        }
    });

    /* ============ Сохранение по Enter / потере фокуса ============ */

    container.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        const inp = e.target;

        // Сохранить вопрос по Enter
        if (inp.classList.contains('js-question-text')) {
            e.preventDefault();
            const btn = inp.closest('.eq-question-card').querySelector('.js-save-question');
            btn.click();
        }

        // Сохранить ответ по Enter
        if (inp.classList.contains('js-answer-text')) {
            e.preventDefault();
            const btn = inp.closest('.eq-answer-row').querySelector('.js-save-answer');
            btn.click();
        }
    });

    /* Автосохранение при потере фокуса (blur) */
    container.addEventListener('focusout', function (e) {
        const inp = e.target;

        if (inp.classList.contains('js-question-text') && inp.value !== inp.dataset.original) {
            const btn = inp.closest('.eq-question-card').querySelector('.js-save-question');
            btn.click();
        }

        if (inp.classList.contains('js-answer-text') && inp.value !== inp.dataset.original) {
            const btn = inp.closest('.eq-answer-row').querySelector('.js-save-answer');
            btn.click();
        }
    });

    /* Автосохранение при смене типа вопроса */
    container.addEventListener('change', function (e) {
        if (e.target.classList.contains('js-question-type')) {
            const sel = e.target;
            if (sel.value !== sel.dataset.original) {
                const btn = sel.closest('.eq-question-card').querySelector('.js-save-question');
                btn.click();
            }
        }
        /* Автосохранение при переключении правильности ответа */
        if (e.target.classList.contains('js-answer-correct')) {
            const correctInp = e.target;
            const row = correctInp.closest('.eq-answer-row');
            const card = correctInp.closest('.eq-question-card');
            const questionType = card.dataset.questionType || 'single';
            
            // Если это radio и выбрали новый ответ, снимаем выбор с остальных
            if (questionType === 'single' && correctInp.type === 'radio' && correctInp.checked) {
                const allRadios = card.querySelectorAll('.js-answer-correct[type="radio"]');
                allRadios.forEach(radio => {
                    if (radio !== correctInp && radio.checked) {
                        radio.checked = false;
                        // Сохраняем ответ, с которого сняли выбор
                        const otherRow = radio.closest('.eq-answer-row');
                        const otherBtn = otherRow.querySelector('.js-save-answer');
                        const otherTextInp = otherRow.querySelector('.js-answer-text');
                        const otherAId = otherRow.dataset.answerId;
                        apiCall(`/quizzes/${QUIZ_ID}/api/answer/${otherAId}/update/`, {
                            text: otherTextInp.value,
                            is_correct: false,
                        }).catch(() => {});
                    }
                });
            }
            
            const btn = row.querySelector('.js-save-answer');
            btn.click();
        }
    });

    /* Первичная нумерация */
    updateNumbers();
});