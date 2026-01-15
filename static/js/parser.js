// Parser control page JavaScript
document.addEventListener('DOMContentLoaded', function () {
    const startBtn = document.getElementById('start-parser-btn');
    const updateDbBtn = document.getElementById('update-db-btn');
    const statusText = document.getElementById('status-text');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const logOutput = document.getElementById('log-output');

    // Start parser button
    startBtn.addEventListener('click', function () {
        if (confirm('Запустить парсер принудительно?')) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Запуск...';

            fetch('/api/parser/start', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showSuccess('Парсер запущен!');
                        statusText.textContent = 'Запущен';
                        statusText.parentElement.className = 'alert alert-success';
                        progressContainer.style.display = 'block';
                        startMonitoring();
                    } else {
                        showError('Ошибка: ' + data.message);
                    }
                })
                .catch(error => {
                    showError('Ошибка запуска: ' + error);
                })
                .finally(() => {
                    startBtn.disabled = false;
                    startBtn.innerHTML = '<i class="bi bi-play-fill"></i> Запустить парсер принудительно';
                });
        }
    });

    // Update database button
    updateDbBtn.addEventListener('click', function () {
        if (confirm('Обновить базу данных из Google Sheets?')) {
            updateDbBtn.disabled = true;
            updateDbBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Обновление...';

            fetch('/api/database/update', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showSuccess('База данных обновлена!');
                    } else {
                        showError('Ошибка: ' + data.message);
                    }
                })
                .catch(error => {
                    showError('Ошибка обновления: ' + error);
                })
                .finally(() => {
                    updateDbBtn.disabled = false;
                    updateDbBtn.innerHTML = '<i class="bi bi-arrow-repeat"></i> Обновить БД из Google Sheets';
                });
        }
    });

    function startMonitoring() {
        const interval = setInterval(() => {
            fetch('/api/parser/status')
                .then(response => response.json())
                .then(data => {
                    if (data.running) {
                        const progress = data.progress || 0;
                        progressBar.style.width = progress + '%';
                        progressBar.textContent = progress + '%';
                        progressBar.setAttribute('aria-valuenow', progress);
                        progressText.textContent = data.message || 'Обработка...';

                        if (data.log) {
                            logOutput.textContent = data.log;
                        }
                    } else {
                        clearInterval(interval);
                        statusText.textContent = 'Завершён';
                        statusText.parentElement.className = 'alert alert-info';
                        progressBar.style.width = '100%';
                        progressBar.textContent = '100%';
                        progressText.textContent = 'Парсинг завершён!';
                    }
                })
                .catch(error => {
                    console.error('Error monitoring status:', error);
                });
        }, 2000); // Check every 2 seconds
    }

    function showSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 end-0 m-3';
        alert.style.zIndex = '9999';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }

    function showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 end-0 m-3';
        alert.style.zIndex = '9999';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alert);
        setTimeout(() => alert.remove(), 5000);
    }
});
