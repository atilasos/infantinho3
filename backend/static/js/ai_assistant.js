(function () {
  'use strict';

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function initAssistant(container) {
    const openBtn = container.querySelector('[data-ai-open-chat]');
    const panel = container.querySelector('[data-ai-panel]');
    const closeBtn = container.querySelector('[data-ai-close]');
    const messagesBox = container.querySelector('[data-ai-messages]');
    const input = container.querySelector('[data-ai-input]');
    const sendBtn = container.querySelector('[data-ai-send]');
    const feedbackWrapper = container.querySelector('[data-ai-feedback-wrapper]');
    const feedbackButtons = container.querySelectorAll('[data-ai-feedback]');
    const errorBox = container.querySelector('[data-ai-error]');

    if (!openBtn || !panel || !messagesBox || !input || !sendBtn) {
      return;
    }

    let sessionId = container.dataset.aiSessionId || null;
    let requestId = null;
    let history = [];
    let isBusy = false;

    function togglePanel(open) {
      if (open) {
        panel.classList.remove('d-none');
        input.focus();
      } else {
        panel.classList.add('d-none');
      }
    }

    function setBusy(busy) {
      isBusy = busy;
      sendBtn.disabled = busy;
      input.disabled = busy;
    }

    function showStatus(message, variant) {
      if (!errorBox) return;
      errorBox.textContent = message;
      errorBox.classList.remove('d-none');
      errorBox.classList.remove('text-danger', 'text-success', 'text-muted');
      const tone = variant === 'success' ? 'text-success' : variant === 'muted' ? 'text-muted' : 'text-danger';
      errorBox.classList.add(tone);
    }

    function clearStatus() {
      if (!errorBox) return;
      errorBox.classList.add('d-none');
      errorBox.textContent = '';
      errorBox.classList.remove('text-danger', 'text-success', 'text-muted');
    }

    function scrollToBottom() {
      messagesBox.scrollTop = messagesBox.scrollHeight;
    }

    function appendMessage(role, content) {
      const wrapper = document.createElement('div');
      wrapper.classList.add('mb-2', 'w-100', 'd-flex');
      if (role === 'user') {
        wrapper.classList.add('justify-content-end');
      } else {
        wrapper.classList.add('justify-content-start');
      }

      const bubble = document.createElement('div');
      bubble.classList.add('px-3', 'py-2', 'rounded-3', 'shadow-sm');
      if (role === 'user') {
        bubble.classList.add('bg-primary', 'text-white');
      } else {
        bubble.classList.add('bg-light');
      }
      const html = escapeHtml(content).replace(/\n/g, '<br>');
      bubble.innerHTML = html;
      wrapper.appendChild(bubble);
      messagesBox.appendChild(wrapper);
      scrollToBottom();
    }

    function payloadHistory() {
      const sliceStart = Math.max(history.length - 6, 0);
      return history.slice(sliceStart);
    }

    function buildExtras() {
      const extras = {};
      const descriptor = container.dataset.aiContext || '';
      if (descriptor) {
        extras.context_descriptor = descriptor;
      }
      const source = container.dataset.aiSource || '';
      if (source) {
        extras.source_element = source;
      }
      return extras;
    }

    function handleSend() {
      if (isBusy) {
        return;
      }
      const message = input.value.trim();
      if (!message) {
        return;
      }
      const endpoint = container.dataset.aiEndpoint;
      if (!endpoint) {
        showStatus('Endpoint IA indisponível.', 'danger');
        return;
      }

      clearStatus();
      appendMessage('user', message);
      const historyPayload = payloadHistory();
      history.push({ role: 'user', content: message });
      input.value = '';
      if (feedbackWrapper) {
        feedbackWrapper.classList.add('d-none');
      }

      setBusy(true);
      const body = {
        message,
        origin_app: container.dataset.aiOrigin || 'portal',
        class_id: container.dataset.aiClassId || null,
        session_id: sessionId,
        history: historyPayload,
        extras: buildExtras(),
      };

      fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify(body),
      })
        .then((res) => {
          if (!res.ok) {
            return res.json().then((data) => {
              throw data;
            });
          }
          return res.json();
        })
        .then((data) => {
          sessionId = data.session_id || sessionId;
          requestId = data.request_id || null;
          const responseText = data.response || '';
          appendMessage('assistant', responseText);
          history.push({ role: 'assistant', content: responseText });
          if (feedbackWrapper && requestId) {
            feedbackWrapper.classList.remove('d-none');
          }
        })
        .catch((error) => {
          if (history.length && history[history.length - 1].role === 'user') {
            // keep user message in history; allow retry
          }
          const messageText = error && error.error ? error.error : 'Não foi possível obter resposta da IA.';
          showStatus(messageText, 'danger');
        })
        .finally(() => {
          setBusy(false);
          input.focus();
        });
    }

    openBtn.addEventListener('click', () => togglePanel(true));
    if (closeBtn) {
      closeBtn.addEventListener('click', () => togglePanel(false));
    }
    sendBtn.addEventListener('click', handleSend);
    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSend();
      }
    });

    if (feedbackWrapper) {
      feedbackButtons.forEach((button) => {
        button.addEventListener('click', () => {
          if (!requestId) {
            return;
          }
          const feedbackEndpoint = container.dataset.aiFeedbackEndpoint;
          if (!feedbackEndpoint) {
            return;
          }
          const payload = {
            request_id: requestId,
            feedback: button.dataset.aiFeedback,
          };
          fetch(feedbackEndpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(payload),
          })
            .then((res) => {
              if (!res.ok) {
                throw new Error('feedback');
              }
              const label = button.dataset.aiFeedbackLabel || 'Obrigado!';
              showStatus(label, 'success');
              feedbackWrapper.classList.add('d-none');
            })
            .catch(() => {
              showStatus('Não foi possível registar o feedback.', 'danger');
            });
        });
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-ai-assistant]').forEach(initAssistant);
  });
})();
