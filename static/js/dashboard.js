// Dashboard stats loading
document.addEventListener('DOMContentLoaded', function () {
    loadDashboardStats();
    initPriceChart();
});

function loadDashboardStats() {
    fetch('/api/dashboard/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-products').textContent = data.total_products || 0;
            document.getElementById('products-with-prices').textContent = data.products_with_prices || 0;
            document.getElementById('avg-price').textContent = data.avg_price ? data.avg_price.toFixed(2) + ' ₽' : '0 ₽';
            document.getElementById('total-stores').textContent = data.total_stores || 0;
        })
        .catch(error => {
            console.error('Error loading stats:', error);
            document.getElementById('total-products').textContent = 'Ошибка';
            document.getElementById('products-with-prices').textContent = 'Ошибка';
            document.getElementById('avg-price').textContent = 'Ошибка';
            document.getElementById('total-stores').textContent = 'Ошибка';
        });
}

function initPriceChart() {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Загрузка...'],
            datasets: [{
                label: 'Средняя цена по магазинам',
                data: [0],
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return value + ' ₽';
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + context.parsed.y + ' ₽';
                        }
                    }
                }
            }
        }
    });
}
