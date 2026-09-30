// static/js/employees.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter controls
    initFilters();

    // Load employee asset data
    loadEmployeeAssets();

    // Set up new assignment button
    const newAssignmentBtn = document.querySelector('.new-assignment-btn');
    if (newAssignmentBtn) {
        newAssignmentBtn.addEventListener('click', showNewAssignmentModal);
    }

    // Set up filter button
    const filterBtn = document.getElementById('filter-btn');
    if (filterBtn) {
        filterBtn.addEventListener('click', applyFilters);
    }
    // search
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function() {
            applyFilters();
        }, 300));

        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                applyFilters();
            }
        });
    }
});

function debounce(func, wait) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            func.apply(context, args);
        }, wait);
    };
}
function initFilters() {
    // Load departments for filter dropdown
    fetch('/api/employees?departments=true')
        .then(response => response.json())
        .then(data => {
            const departmentSelect = document.getElementById('department-filter');
            if (departmentSelect && data.departments) {
                departmentSelect.innerHTML = '';

                // Add "All Departments" option
                const allOption = document.createElement('option');
                allOption.value = 'All';
                allOption.textContent = 'All Departments';
                departmentSelect.appendChild(allOption);

                // Add department options
                data.departments.forEach(dept => {
                    if (dept === 'All') return; // Skip "All" as we already added it

                    const option = document.createElement('option');
                    option.value = dept;
                    option.textContent = dept;
                    departmentSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading departments:', error);
        });

    // Load statuses for filter dropdown
    fetch('/api/employee-assets?statuses=true')
        .then(response => response.json())
        .then(data => {
            const statusSelect = document.getElementById('status-filter');
            if (statusSelect && data.statuses) {
                statusSelect.innerHTML = '';

                data.statuses.forEach(status => {
                    const option = document.createElement('option');
                    option.value = status;
                    option.textContent = formatStatusLabel(status);
                    statusSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading statuses:', error);
        });
}

function loadEmployeeAssets(filters = {}) {
    // Build query string from filters
    const queryParams = new URLSearchParams();

    if (filters.employee_id) queryParams.append('employee_id', filters.employee_id);
    if (filters.department && filters.department !== 'All') queryParams.append('department', filters.department);
    if (filters.status && filters.status !== 'All') queryParams.append('status', filters.status);
    if (filters.search && filters.search.trim() !== '') {
        queryParams.append('search', filters.search.trim());
    }
    // Check for asset_id in URL (for direct linking)
    const urlParams = new URLSearchParams(window.location.search);
    const assetId = urlParams.get('asset_id');
    if (assetId) queryParams.append('asset_id', assetId);

    // Fetch employee assets with filters
    fetch(`/api/employee-assets?${queryParams.toString()}`)
        .then(response => response.json())
        .then(data => {
            populateAssetsTable(data.data);
            updateFilterCounts(data.data);

            // If specific asset_id was requested, show its details
            if (assetId) {
                const asset = data.data.find(a => a.id === parseInt(assetId));
                if (asset) {
                    showAssetDetails(asset);
                }
            }
        })
        .catch(error => {
            console.error('Error loading employee assets:', error);
        });
}

function populateAssetsTable(assets) {
    const tableBody = document.querySelector('.employee-assets-table tbody');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    if (assets.length === 0) {
        // Display no results message
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="8" class="text-center">No matching assets found</td>';
        tableBody.appendChild(row);
        return;
    }

    assets.forEach(asset => {
        const row = document.createElement('tr');

        // Set status badge class
        let statusBadgeClass = 'bg-secondary';
        switch (asset.status) {
            case 'active': statusBadgeClass = 'bg-success'; break;
            case 'pending_return': statusBadgeClass = 'bg-warning'; break;
            case 'returned': statusBadgeClass = 'bg-info'; break;
            case 'lost': statusBadgeClass = 'bg-danger'; break;
            case 'damaged': statusBadgeClass = 'bg-danger'; break;
        }

        row.innerHTML = `
            <td>${asset.employee_name}</td>
            <td>${asset.department}</td>
            <td>${asset.device_type}</td>
            <td>${asset.device_name}</td>
            <td>${asset.assignment_date}</td>
            <td><span class="badge ${statusBadgeClass}">${formatStatusLabel(asset.status)}</span></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-outline-primary view-btn" data-id="${asset.id}">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button type="button" class="btn btn-outline-secondary edit-btn" data-id="${asset.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button" class="btn btn-outline-danger return-btn" data-id="${asset.id}" 
                        ${asset.status !== 'active' ? 'style="display:none"' : ''}>
                        <i class="bi bi-box-arrow-in-left"></i>
                    </button>
                </div>
            </td>
        `;

        // Add event listeners to buttons
        const viewBtn = row.querySelector('.view-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', function() {
                // Find the asset in our data
                showAssetDetails(asset);
            });
        }

        const editBtn = row.querySelector('.edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', function() {
                editAssetAssignment(asset);
            });
        }

        const returnBtn = row.querySelector('.return-btn');
        if (returnBtn) {
            returnBtn.addEventListener('click', function() {
                initiateDeviceReturn(asset);
            });
        }

        tableBody.appendChild(row);
    });
}

function updateFilterCounts(assets) {
    // Update filter count badges
    const countElement = document.getElementById('asset-count');
    if (countElement) {
        countElement.textContent = assets.length;
    }

    // Could add more count summaries here (e.g., by status)
}

function applyFilters() {
    // Get filter values
    const departmentFilter = document.getElementById('department-filter');
    const statusFilter = document.getElementById('status-filter');
    const searchInput = document.getElementById('search-input');

    const filters = {
        department: departmentFilter ? departmentFilter.value : 'All',
        status: statusFilter ? statusFilter.value : 'All',
        search: searchInput ? searchInput.value : ''
    };

    // Apply filters by reloading data
    loadEmployeeAssets(filters);
}

function showAssetDetails(asset) {
    // Implement asset details view
    // This could be a modal or a details panel
    console.log('Showing details for asset:', asset);

    // Example implementation using Bootstrap modal
    const modal = new bootstrap.Modal(document.getElementById('asset-details-modal'));

    // Populate modal with asset details
    document.getElementById('asset-detail-employee').textContent = asset.employee_name;
    document.getElementById('asset-detail-department').textContent = asset.department;
    document.getElementById('asset-detail-device').textContent = `${asset.device_type} - ${asset.device_name}`;
    document.getElementById('asset-detail-assignment-date').textContent = asset.assignment_date;

    // Show expected return date if applicable
    const expectedReturnElement = document.getElementById('asset-detail-expected-return');
    if (expectedReturnElement) {
        expectedReturnElement.textContent = asset.expected_return_date || 'N/A';
    }

    // Show actual return date if applicable
    const actualReturnElement = document.getElementById('asset-detail-actual-return');
    if (actualReturnElement) {
        actualReturnElement.textContent = asset.actual_return_date || 'N/A';
    }

    // Set status badge
    const statusElement = document.getElementById('asset-detail-status');
    if (statusElement) {
        let statusBadgeClass = 'bg-secondary';
        switch (asset.status) {
            case 'active': statusBadgeClass = 'bg-success'; break;
            case 'pending_return': statusBadgeClass = 'bg-warning'; break;
            case 'returned': statusBadgeClass = 'bg-info'; break;
            case 'lost': statusBadgeClass = 'bg-danger'; break;
            case 'damaged': statusBadgeClass = 'bg-danger'; break;
        }

        statusElement.innerHTML = `<span class="badge ${statusBadgeClass}">${formatStatusLabel(asset.status)}</span>`;
    }

    // Set notes
    const notesElement = document.getElementById('asset-detail-notes');
    if (notesElement) {
        notesElement.textContent = asset.notes || 'No notes';
    }

    // Show the modal
    modal.show();
}

function editAssetAssignment(asset) {
    // Implement asset edit functionality
    // This would typically show a form in a modal
    console.log('Editing asset assignment:', asset);
    window.currentEditingAsset = asset;

    // Example implementation - fetch data and show modal
    const modal = new bootstrap.Modal(document.getElementById('edit-asset-modal'));

    // Populate form with asset data
    document.getElementById('edit-asset-employee').value = asset.employee_id;
    document.getElementById('edit-asset-device').value = asset.inventory_id;
    document.getElementById('edit-asset-status').value = asset.status;
    document.getElementById('edit-asset-notes').value = asset.notes || '';

    // Set form submission handler
    const form = document.getElementById('edit-asset-form');
    if (form) {
        form.onsubmit = function(event) {
            event.preventDefault();
            saveAssetChanges(asset.id, form);
        };
    }

    // Show the modal
    modal.show();
}

function saveAssetChanges(assetId, form) {
    // Get form data
    const formData = new FormData(form);
    const data = {
        status: formData.get('status'),
        notes: formData.get('notes')
    };

    // If status is changed to returned, set actual_return_date
    if (data.status === 'returned') {
        data.actual_return_date = new Date().toISOString().split('T')[0];
    }

    const assetBeforeUpdate = window.currentEditingAsset || {};

    // Send update request
    fetch(`/api/employee-assets/${assetId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Close modal and reload data
            const modal = bootstrap.Modal.getInstance(document.getElementById('edit-asset-modal'));
            modal.hide();

            // Show success message
            showAlert('Asset assignment updated successfully', 'success');

            // 发布资产状态变化事件，通知其他页面
            const event = {
                name: 'assetStatusChanged',
                data: {
                    assetId: assetId,
                    inventoryId: assetBeforeUpdate.inventory_id,
                    oldStatus: assetBeforeUpdate.status,
                    newStatus: data.status
                },
                timestamp: new Date().getTime()
            };
            localStorage.setItem('assetEvent', JSON.stringify(event));

            // Reload data
            loadEmployeeAssets();

        } else {
            showAlert(`Error: ${result.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating asset:', error);
        showAlert('An error occurred while updating the asset', 'danger');
    });
}

function initiateDeviceReturn(asset) {
    // Show device return confirmation dialog
    const confirmReturn = confirm(`Are you sure you want to mark this ${asset.device_type} as pending return from ${asset.employee_name}?`);

    if (confirmReturn) {
        // Update asset status
        fetch(`/api/employee-assets/${asset.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'pending_return',
                expected_return_date: new Date(Date.now() + 7*24*60*60*1000).toISOString().split('T')[0], // 7 days from now
                notes: asset.notes ? `${asset.notes}\nReturn initiated on ${new Date().toLocaleDateString()}` : `Return initiated on ${new Date().toLocaleDateString()}`
            })
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showAlert('Device marked for return successfully', 'success');

                const event = {
                    name: 'assetStatusChanged',
                    data: {
                        assetId: asset.id,
                        inventoryId: asset.inventory_id,
                        oldStatus: asset.status,
                        newStatus: 'pending_return'
                    },
                    timestamp: new Date().getTime()
                };
                localStorage.setItem('assetEvent', JSON.stringify(event));

                loadEmployeeAssets();
            } else {
                showAlert(`Error: ${result.error}`, 'danger');
            }
        })
        .catch(error => {
            console.error('Error initiating return:', error);
            showAlert('An error occurred while processing the return', 'danger');
        });
    }
}

function showNewAssignmentModal() {
    Promise.all([
        fetch('/api/employees').then(response => response.json()),
        fetch('/api/inventory').then(response => response.json())  // 获取所有设备
    ])
    .then(([employeesResponse, inventoryResponse]) => {
        // Populate employee dropdown
        const employeeSelect = document.getElementById('new-asset-employee');
        if (employeeSelect && employeesResponse.data) {
            employeeSelect.innerHTML = '<option value="">Select Employee</option>';

            employeesResponse.data.forEach(employee => {
                const option = document.createElement('option');
                option.value = employee.id;
                option.textContent = `${employee.name} (${employee.department})`;
                employeeSelect.appendChild(option);
            });
        }

        // Populate device dropdown
        const deviceSelect = document.getElementById('new-asset-device');
        if (deviceSelect && inventoryResponse.data) {
            deviceSelect.innerHTML = '<option value="">✓ Select Device</option>';

            const availableDevices = inventoryResponse.data.filter(device => {
                console.log('Device:', device.device_name, 'Quantity:', device.quantity, 'Status:', device.status);
                return device.quantity > 0 || device.status === 'returned';
            });

            console.log('Available devices count:', availableDevices.length);
            console.log('Available devices:', availableDevices);

            if (availableDevices.length === 0) {
                const option = document.createElement('option');
                option.disabled = true;
                option.textContent = 'No available devices';
                deviceSelect.appendChild(option);
            } else {
                // 先添加已归还的设备（标记为[Returned]）
                const returnedDevices = availableDevices.filter(device => device.status === 'returned');
                if (returnedDevices.length > 0) {
                    const returnedLabel = document.createElement('option');
                    returnedLabel.disabled = true;
                    returnedLabel.textContent = '---- Returned Devices ----';
                    deviceSelect.appendChild(returnedLabel);

                    returnedDevices.forEach(device => {
                        const option = document.createElement('option');
                        option.value = device.id;
                        option.textContent = `${device.device_name} [${device.device_type}] - Returned`;
                        deviceSelect.appendChild(option);
                    });
                }

                const inventoryDevices = availableDevices.filter(device => device.quantity > 0);
                if (inventoryDevices.length > 0) {
                    const inventoryLabel = document.createElement('option');
                    inventoryLabel.disabled = true;
                    inventoryLabel.textContent = '---- Available Inventory ----';
                    deviceSelect.appendChild(inventoryLabel);

                    const devicesByType = {};
                    inventoryDevices.forEach(device => {
                        if (!devicesByType[device.device_type]) {
                            devicesByType[device.device_type] = [];
                        }
                        devicesByType[device.device_type].push(device);
                    });

                    // 添加每种类型的设备
                    Object.keys(devicesByType).sort().forEach(type => {
                        const devices = devicesByType[type];

                        devices.forEach(device => {
                            const option = document.createElement('option');
                            option.value = device.id;
                            option.textContent = `${device.device_name} [${device.device_type}]`;
                            deviceSelect.appendChild(option);
                        });
                    });
                }
            }
        }

        // Set today as default assignment date
        const dateInput = document.getElementById('new-asset-date');
        if (dateInput) {
            dateInput.value = new Date().toISOString().split('T')[0];
        }

        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('new-assignment-modal'));
        modal.show();
    })
    .catch(error => {
        console.error('Error loading data for new assignment:', error);
        showAlert('Failed to load employee or device data', 'danger');
    });

    // Set form submission handler
    const form = document.getElementById('new-assignment-form');
    if (form) {
        form.onsubmit = function(event) {
            event.preventDefault();
            createNewAssignment(form);
        };
    }
}

function createNewAssignment(form) {
    // Get form data
    const formData = new FormData(form);
    const data = {
        employee_id: parseInt(formData.get('employee_id')),
        inventory_id: parseInt(formData.get('device_id')),
        assignment_date: formData.get('assignment_date'),
        notes: formData.get('notes') || '',
        status: 'active'
    };

    // Validate required fields
    if (!data.employee_id || !data.inventory_id || !data.assignment_date) {
        showAlert('Please fill in all required fields', 'warning');
        return;
    }

    const deviceSelect = document.getElementById('new-asset-device');
    const selectedOption = deviceSelect.options[deviceSelect.selectedIndex];
    const isReturnedDevice = selectedOption.textContent.includes('Returned');

    if (isReturnedDevice) {
        data.was_returned = true;
    }

    // Send create request
    fetch('/api/employee-assets', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Close modal and reload data
            const modal = bootstrap.Modal.getInstance(document.getElementById('new-assignment-modal'));
            modal.hide();

            // Show success message
            showAlert('New device assignment created successfully', 'success');

            // Reset form
            form.reset();

            const event = {
                name: 'assetAssigned',
                data: {
                    inventoryId: data.inventory_id,
                    employeeId: data.employee_id,
                    status: 'active',
                    wasReturned: isReturnedDevice
                },
                timestamp: new Date().getTime()
            };
            localStorage.setItem('assetEvent', JSON.stringify(event));

            // Reload data
            loadEmployeeAssets();
        } else {
            showAlert(`Error: ${result.error}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error creating assignment:', error);
        showAlert('An error occurred while creating the assignment', 'danger');
    });
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to container
    alertContainer.appendChild(alert);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alertContainer.removeChild(alert);
        }, 150);
    }, 5000);
}

// Utility function
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