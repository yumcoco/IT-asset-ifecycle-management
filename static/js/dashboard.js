// static/js/dashboard.js

document.addEventListener('DOMContentLoaded', function() {
    // Load dashboard data
    fetchDashboardData();

    // Set up refresh button event handler
    const refreshBtn = document.getElementById('refresh-data');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchDashboardData);
    }
});

function fetchDashboardData() {
    fetch('/api/dashboard-summary')
        .then(response => response.json())
        .then(data => {
            updateDashboardCards(data);
            createDepartmentChart(data.department_distribution);
            createStatusChart(data.status_distribution);
            populateRecentAssignments(data.recent_assignments);
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
        });
}

function updateDashboardCards(data) {
    // Update KPI cards
    document.getElementById('total-inventory').textContent = data.total_assets;
    document.getElementById('low-stock').textContent = data.available_devices;
    document.getElementById('top-supplier').textContent = data.pending_requests;
    document.getElementById('inventory-value').textContent = formatCurrency(data.total_value);
}

function createDepartmentChart(departmentData) {
    // Create department distribution chart
    const ctx = document.getElementById('orderTrendsChart').getContext('2d');

    // Convert data to Chart.js format
    const labels = Object.keys(departmentData);
    const values = Object.values(departmentData);

    // Generate random colors
    const colors = labels.map(() => getRandomColor());

    // Create chart
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Assigned Devices',
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(color => adjustColorBrightness(color, -0.2)),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    display: false
                },
                title: {
                    display: true,
                    text: 'Asset Assignment by Department'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Devices'
                    }
                }
            }
        }
    });
}

function createStatusChart(statusData) {
    // Create device status chart
    const ctx = document.getElementById('deviceDistributionChart').getContext('2d');

    // Convert data to Chart.js format
    const labels = Object.keys(statusData);
    const values = Object.values(statusData);

    // Status color mapping
    const statusColors = {
        'active': '#28a745',
        'pending_return': '#ffc107',
        'returned': '#17a2b8',
        'lost': '#dc3545',
        'damaged': '#fd7e14'
    };

    // Get colors for each status
    const colors = labels.map(status => statusColors[status] || getRandomColor());

    // Create chart
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels.map(formatStatusLabel),
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: colors.map(color => adjustColorBrightness(color, -0.2)),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Device Lifecycle Status'
                }
            }
        }
    });
}

function populateRecentAssignments(assignments) {
    // Populate recent assignments table
    const tableBody = document.getElementById('top-suppliers-table');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    assignments.forEach(assignment => {
        const row = document.createElement('tr');

        // Set color for status badge
        let statusBadgeClass = 'bg-secondary';
        switch (assignment.status) {
            case 'active': statusBadgeClass = 'bg-success'; break;
            case 'pending_return': statusBadgeClass = 'bg-warning'; break;
            case 'returned': statusBadgeClass = 'bg-info'; break;
            case 'lost': statusBadgeClass = 'bg-danger'; break;
            case 'damaged': statusBadgeClass = 'bg-danger'; break;
        }

        row.innerHTML = `
            <td>${assignment.employee_name}</td>
            <td>${assignment.department}</td>
            <td>${assignment.device_name}</td>
            <td>${assignment.assignment_date}</td>
            <td><span class="badge ${statusBadgeClass}">${formatStatusLabel(assignment.status)}</span></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-outline-primary view-btn" data-id="${assignment.id}">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button type="button" class="btn btn-outline-secondary edit-btn" data-id="${assignment.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                </div>
            </td>
        `;

        // Add event listeners to buttons
        const viewBtn = row.querySelector('.view-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', function() {
                viewAssetDetails(assignment.id);
            });
        }

        const editBtn = row.querySelector('.edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', function() {
                editAssetAssignment(assignment.id);
            });
        }

        tableBody.appendChild(row);
    });
}

function viewAssetDetails(id) {
    // Redirect to employee assets page with the selected asset ID
    window.location.href = `/employee-assets?asset_id=${id}`;
}

function editAssetAssignment(id) {
    // Show modal for editing asset assignment
    // This would typically open a modal dialog
    console.log(`Edit asset assignment ${id}`);
    // Implementation depends on your UI framework/approach
}

// Utility Functions

function formatCurrency(value) {
    // Format number as currency
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatStatusLabel(status) {
    // Convert status_code to user-friendly text
    switch(status) {
        case 'active': return 'Active';
        case 'pending_return': return 'Pending Return';
        case 'returned': return 'Returned';
        case 'lost': return 'Lost';
        case 'damaged': return 'Damaged';
        default: return status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ');
    }
}

function getRandomColor() {
    // Generate random colors for charts
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

function adjustColorBrightness(hex, factor) {
    // Adjust color brightness (for borders)
    const r = parseInt(hex.substring(1, 3), 16);
    const g = parseInt(hex.substring(3, 5), 16);
    const b = parseInt(hex.substring(5, 7), 16);

    const adjustedR = Math.max(0, Math.min(255, Math.round(r + (factor * 255))));
    const adjustedG = Math.max(0, Math.min(255, Math.round(g + (factor * 255))));
    const adjustedB = Math.max(0, Math.min(255, Math.round(b + (factor * 255))));

    return `#${adjustedR.toString(16).padStart(2, '0')}${adjustedG.toString(16).padStart(2, '0')}${adjustedB.toString(16).padStart(2, '0')}`;
}