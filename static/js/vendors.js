// static/js/vendors.js

document.addEventListener('DOMContentLoaded', function() {
    fetchVendorData();

    const addVendorBtn = document.getElementById('add-vendor-btn');
    if (addVendorBtn) {
        addVendorBtn.addEventListener('click', function() {
            console.log('Add vendor button clicked');
        });
    }
});

function fetchVendorData() {
    console.log('Fetching vendor data...');

    Promise.all([
        fetch('/api/suppliers').then(res => res.json()),
        fetch('/api/performance').then(res => res.json())
    ])
    .then(([suppliersData, performanceData]) => {
        console.log('Data received:', suppliersData, performanceData);

        displaySupplierTable(suppliersData.data || []);
        createSupplierCharts(performanceData);
    })
    .catch(error => {
        console.error('Error fetching vendor data:', error);
        const errorMessage = document.createElement('div');
        errorMessage.className = 'alert alert-danger mt-3';
        errorMessage.textContent = 'Failed to load vendor data. Please try refreshing the page.';
        document.querySelector('.container').prepend(errorMessage);
    });
}

function displaySupplierTable(suppliers) {
    const tableBody = document.getElementById('vendor-table-body');
    if (!tableBody) {
        console.error('Vendor table body not found');
        return;
    }

    tableBody.innerHTML = '';

    if (!Array.isArray(suppliers) || suppliers.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No vendor data available</td></tr>';
        return;
    }

    suppliers.sort((a, b) => b.reliability_score - a.reliability_score);

    suppliers.forEach(supplier => {
        const row = document.createElement('tr');

        const reliabilityStars = createStarRating(supplier.reliability_score);
        const qualityStars = createStarRating(supplier.quality_score);

        row.innerHTML = `
            <td>${supplier.name}</td>
            <td>${supplier.country}</td>
            <td>${reliabilityStars} (${supplier.reliability_score.toFixed(1)})</td>
            <td>${qualityStars} (${supplier.quality_score.toFixed(1)})</td>
            <td>${supplier.total_orders || 0}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary view-vendor-btn" data-id="${supplier.id}">
                    <i class="bi bi-eye"></i> Details
                </button>
            </td>
        `;

        const viewBtn = row.querySelector('.view-vendor-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', function() {
                viewVendorDetails(supplier.id);
            });
        }

        tableBody.appendChild(row);
    });
}

function createSupplierCharts(performanceData) {
    console.log('Creating supplier charts with data:', performanceData);

    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded');
        return;
    }

    if (!performanceData || !performanceData.top_suppliers || !performanceData.order_trends) {
        console.warn('Performance data is missing required properties:', performanceData);
        return;
    }

    try {
        destroyChartIfExists('reliabilityChart');
        destroyChartIfExists('qualityChart');
        destroyChartIfExists('orderVolumeChart');

        createReliabilityChart(performanceData.top_suppliers);
        createQualityChart(performanceData.top_suppliers);
        createOrderVolumeChart(performanceData.order_trends);
    } catch (error) {
        console.error('Error creating charts:', error);
    }
}

function destroyChartIfExists(chartId) {
    const chartInstance = Chart.getChart(chartId);
    if (chartInstance) {
        chartInstance.destroy();
    }
}

function createReliabilityChart(suppliers) {
    const canvas = document.getElementById('reliabilityChart');
    if (!canvas) {
        console.error('Reliability chart canvas not found');
        return;
    }

    if (!Array.isArray(suppliers) || suppliers.length === 0) {
        showNoDataMessage(canvas, 'No supplier data available');
        return;
    }

    const topSuppliers = suppliers.slice(0, 5);

    const labels = topSuppliers.map(s => s.name);
    const data = topSuppliers.map(s => s.reliability_score);

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Reliability Score (0-5)',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
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
                    max: 5
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Top Vendors by Reliability'
                }
            }
        }
    });
}

function createQualityChart(suppliers) {
    const canvas = document.getElementById('qualityChart');
    if (!canvas) {
        console.error('Quality chart canvas not found');
        return;
    }

    // 确保有数据
    if (!Array.isArray(suppliers) || suppliers.length === 0) {
        showNoDataMessage(canvas, 'No supplier data available');
        return;
    }

    // 取前5名供应商
    const topSuppliers = suppliers.slice(0, 5);

    // 提取数据
    const labels = topSuppliers.map(s => s.name);
    const data = topSuppliers.map(s => s.quality_score);

    // 创建图表
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Quality Score (0-5)',
                data: data,
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 5
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Top Vendors by Quality'
                }
            }
        }
    });
}

function createOrderVolumeChart(orderTrends) {
    const canvas = document.getElementById('orderVolumeChart');
    if (!canvas) {
        console.error('Order volume chart canvas not found');
        return;
    }

    if (!Array.isArray(orderTrends) || orderTrends.length === 0) {
        showNoDataMessage(canvas, 'No order trend data available');
        return;
    }

    const labels = orderTrends.map(t => t.month);
    const orderCounts = orderTrends.map(t => t.order_count);
    const orderValues = orderTrends.map(t => t.total_spend);

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Order Count',
                    data: orderCounts,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    yAxisID: 'y'
                },
                {
                    label: 'Order Value ($)',
                    data: orderValues,
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 2,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Order Count'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Order Value ($)'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Order Volume Trends'
                }
            }
        }
    });
}

function showNoDataMessage(canvas, message) {
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = '16px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#666';
    ctx.fillText(message, canvas.width / 2, canvas.height / 2);
}

function viewVendorDetails(vendorId) {
    fetch(`/api/suppliers/${vendorId}`)
        .then(response => response.json())
        .then(data => {
            const vendor = data.data;

            document.getElementById('vendor-detail-name').textContent = vendor.name;
            document.getElementById('vendor-detail-country').textContent = vendor.country;

            document.getElementById('vendor-detail-reliability').innerHTML =
                `${createStarRating(vendor.reliability_score)} (${vendor.reliability_score.toFixed(1)})`;
            document.getElementById('vendor-detail-quality').innerHTML =
                `${createStarRating(vendor.quality_score)} (${vendor.quality_score.toFixed(1)})`;

            document.getElementById('vendor-detail-orders').textContent = vendor.total_orders || 0;
            document.getElementById('vendor-detail-spend').textContent = formatCurrency(vendor.total_spend || 0);

            const modal = new bootstrap.Modal(document.getElementById('vendor-details-modal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error fetching vendor details:', error);
        });
}

function createStarRating(score) {
    const fullStars = Math.floor(score);
    const halfStar = score % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);

    let starsHtml = '';

    for (let i = 0; i < fullStars; i++) {
        starsHtml += '<i class="bi bi-star-fill text-warning"></i>';
    }

    if (halfStar) {
        starsHtml += '<i class="bi bi-star-half text-warning"></i>';
    }

    for (let i = 0; i < emptyStars; i++) {
        starsHtml += '<i class="bi bi-star text-warning"></i>';
    }

    return starsHtml;
}

function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}