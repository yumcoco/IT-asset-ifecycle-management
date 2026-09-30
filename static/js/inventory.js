// static/js/inventory.js

document.addEventListener('DOMContentLoaded', function() {
   // Load inventory data
   fetchInventoryData();

   // Set up add device button
   const addDeviceBtn = document.getElementById('add-device-btn');
   if (addDeviceBtn) {
       addDeviceBtn.addEventListener('click', showAddDeviceModal);
   }

   // Set up filter button
   const filterBtn = document.getElementById('filter-btn');
   if (filterBtn) {
       filterBtn.addEventListener('click', applyFilters);
   }

   // Listen for localStorage changes for cross-page communication
   window.addEventListener('storage', function(e) {
       if (e.key === 'assetEvent') {
           try {
               const event = JSON.parse(e.newValue);
               // Only process events that are recent (within the last 10 seconds)
               if (event && event.timestamp && (new Date().getTime() - event.timestamp < 10000)) {
                   console.log('Asset state changed in another page, refreshing inventory data...', event);
                   fetchInventoryData();
               }
           } catch (error) {
               console.error('Error parsing asset event:', error);
           }
       }
   });

   // If there's a refresh button on the page, add event listener
   const refreshBtn = document.getElementById('refresh-btn');
   if (refreshBtn) {
       refreshBtn.addEventListener('click', function() {
           fetchInventoryData();
           showAlert('Data refreshed', 'info');
       });
   }
});

// Store original data for front-end filtering
let allInventoryData = [];

function fetchInventoryData() {
   fetch('/api/inventory')
       .then(response => response.json())
       .then(data => {
           // Save original data for front-end filtering
           allInventoryData = data.data;

           updateInventorySummary(data);
           populateInventoryTable(data.data);
           loadDeviceTypes(data.data);
       })
       .catch(error => {
           console.error('Error fetching inventory data:', error);
           showAlert('Failed to load inventory data', 'danger');
       });
}

function updateInventorySummary(data) {
   // Check if API provided summary data
   if (data.summary) {
       document.getElementById('total-devices').textContent = data.summary.total;
       document.getElementById('available-devices').textContent = data.summary.available;
       document.getElementById('assigned-devices').textContent = data.summary.assigned;
       document.getElementById('inventory-value').textContent = formatCurrency(
           data.data.reduce((sum, device) => sum + (device.price_per_unit || 0), 0)
       );
       return;
   }

   // If no summary provided, calculate it manually
   const devices = data.data || [];
   const totalDevices = devices.length;
   const availableDevices = devices.filter(device => device.is_available || device.quantity > 0).length;
   const assignedDevices = totalDevices - availableDevices;

   // Update DOM elements
   document.getElementById('total-devices').textContent = totalDevices;
   document.getElementById('available-devices').textContent = availableDevices;
   document.getElementById('assigned-devices').textContent = assignedDevices;
   document.getElementById('inventory-value').textContent = formatCurrency(
       devices.reduce((sum, device) => sum + (device.price_per_unit || 0), 0)
   );
}

function loadDeviceTypes(devices) {
   const typeSelect = document.getElementById('device-type-filter');
   if (!typeSelect) return;

   // Remove existing options except the first one (All)
   while (typeSelect.options.length > 1) {
       typeSelect.options.remove(1);
   }

   // Get unique device types
   const deviceTypes = [...new Set(devices.map(device => device.device_type))];

   // Add options for each device type
   deviceTypes.forEach(type => {
       if (type) { // Skip null/undefined values
           const option = document.createElement('option');
           option.value = type;
           option.textContent = type;
           typeSelect.appendChild(option);
       }
   });
}

function populateInventoryTable(devices) {
    const tableBody = document.querySelector('.inventory-table tbody');
    if (!tableBody) return;

    tableBody.innerHTML = '';

    if (devices.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="8" class="text-center">No devices found</td>';
        tableBody.appendChild(row);
        return;
    }

    devices.forEach(device => {
        const row = document.createElement('tr');

        // Simplified status logic - only available and assigned statuses
        let statusBadge, assignmentInfo;
        let isAvailable = device.is_available || device.quantity > 0;

        if (isAvailable) {
            statusBadge = '<span class="badge bg-success">Available</span>';
            assignmentInfo = 'Available';
            row.classList.add('table-success'); // Green background for available
        } else {
            statusBadge = '<span class="badge bg-warning">Assigned</span>';
            assignmentInfo = 'Assigned';
            row.classList.add('table-warning'); // Yellow background for assigned
        }

        row.innerHTML = `
            <td>${device.device_name}</td>
            <td>${device.device_type}</td>
            <td>${device.location || 'Headquarters'}</td>
            <td>${statusBadge}</td>
            <td>${assignmentInfo}</td>
            <td>${device.last_updated ? new Date(device.last_updated).toLocaleDateString() : '-'}</td>
            <td>${formatCurrency(device.price_per_unit)}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-outline-primary view-btn" data-id="${device.id}">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button type="button" class="btn btn-outline-secondary edit-btn" data-id="${device.id}">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ${isAvailable ? `
                    <button type="button" class="btn btn-outline-success assign-btn" data-id="${device.id}">
                        <i class="bi bi-person-plus"></i>
                    </button>
                    ` : ''}
                </div>
            </td>
        `;

        // Add event listeners to buttons
        const viewBtn = row.querySelector('.view-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', function() {
                viewDeviceDetails(device.id);
            });
        }

        const editBtn = row.querySelector('.edit-btn');
        if (editBtn) {
            editBtn.addEventListener('click', function() {
                editDevice(device.id);
            });
        }

        const assignBtn = row.querySelector('.assign-btn');
        if (assignBtn) {
            assignBtn.addEventListener('click', function(event) {
                event.preventDefault();
                assignDevice(device);
            });
        }

        tableBody.appendChild(row);
    });
}

function viewDeviceDetails(deviceId) {
   // Get device details from API
   fetch(`/api/inventory/${deviceId}`)
       .then(response => response.json())
       .then(data => {
           const device = data.data;

           // Check if device is available using simplified logic
           const isAvailable = device.is_available || device.quantity > 0;

           // Populate modal
           document.getElementById('device-detail-name').textContent = device.device_name;
           document.getElementById('device-detail-type').textContent = device.device_type;
           document.getElementById('device-detail-location').textContent = device.location || 'Headquarters';

           // Set status with simplified logic
           let statusHtml = isAvailable
               ? '<span class="badge bg-success">Available</span>'
               : '<span class="badge bg-warning">Assigned</span>';

           document.getElementById('device-detail-status').innerHTML = statusHtml;

           // Set other fields
           document.getElementById('device-detail-price').textContent = formatCurrency(device.price_per_unit);
           document.getElementById('device-detail-purchase-date').textContent =
               device.last_updated ? new Date(device.last_updated).toLocaleDateString() : 'Unknown';
           document.getElementById('device-detail-notes').textContent = device.notes || 'No notes available';

           // Assignment info with simplified logic
           let assignmentText = isAvailable ? 'Available for assignment' : 'Currently assigned';
           document.getElementById('device-detail-assignment').textContent = assignmentText;

           // Control "Assign to Employee" button based on device status
           const assignBtn = document.querySelector('.assign-device-btn');
           if (assignBtn) {
               assignBtn.style.display = isAvailable ? 'inline-block' : 'none';
               if (isAvailable) {
                   assignBtn.onclick = function() {
                       assignDevice(device);
                   };
               }
           }

           // Show modal
           const modal = new bootstrap.Modal(document.getElementById('device-details-modal'));
           modal.show();
       })
       .catch(error => {
           console.error('Error fetching device details:', error);
           showAlert('Failed to load device details', 'danger');
       });
}

function editDevice(deviceId) {
   // Fetch device details from API
   fetch(`/api/inventory/${deviceId}`)
       .then(response => response.json())
       .then(data => {
           const device = data.data;

           // Populate edit form
           const modal = new bootstrap.Modal(document.getElementById('edit-device-modal'));

           // Fill form fields with device data
           document.getElementById('edit-device-name').value = device.device_name;
           document.getElementById('edit-device-type').value = device.device_type;
           document.getElementById('edit-device-location').value = device.location || 'Headquarters';
           document.getElementById('edit-device-price').value = device.price_per_unit;

           // Set the device ID as a data attribute on the form for submission
           const form = document.getElementById('edit-device-form');
           if (form) {
               form.dataset.deviceId = deviceId;
               form.onsubmit = function(event) {
                   event.preventDefault();
                   saveDeviceChanges(form);
               };
           }

           // Show the modal
           modal.show();
       })
       .catch(error => {
           console.error('Error fetching device details:', error);
           showAlert('Failed to load device details for editing', 'danger');
       });
}

// Add this new function to handle saving changes
function saveDeviceChanges(form) {
   const deviceId = form.dataset.deviceId;
   const formData = new FormData(form);

   // Prepare data for API
   const data = {
       device_name: formData.get('device_name'),
       device_type: formData.get('device_type'),
       location: formData.get('location') || 'Headquarters',
       price_per_unit: parseFloat(formData.get('price_per_unit')),
       notes: formData.get('notes') || ''
   };

   // Send update request
   fetch(`/api/inventory/${deviceId}`, {
       method: 'PUT',
       headers: {
           'Content-Type': 'application/json'
       },
       body: JSON.stringify(data)
   })
   .then(response => response.json())
   .then(result => {
       if (result.success) {
           // Close modal
           const modal = bootstrap.Modal.getInstance(document.getElementById('edit-device-modal'));
           modal.hide();

           // Show success message
           showAlert('Device updated successfully', 'success');

           // Refresh inventory data
           fetchInventoryData();

           // Publish event for cross-page communication
           const event = {
               name: 'deviceUpdated',
               data: {
                   deviceId: deviceId
               },
               timestamp: new Date().getTime()
           };
           localStorage.setItem('assetEvent', JSON.stringify(event));
       } else {
           showAlert(`Error: ${result.error}`, 'danger');
       }
   })
   .catch(error => {
       console.error('Error updating device:', error);
       showAlert('An error occurred while updating the device', 'danger');
   });
}

// 修改这个函数，确保事件监听器只添加一次
function assignDevice(device) {
    // Fetch employees list
    fetch('/api/employees')
        .then(response => response.json())
        .then(employeesResponse => {
            // Populate employee dropdown
            const employeeSelect = document.getElementById('assign-device-employee');
            if (employeeSelect) {
                employeeSelect.innerHTML = '<option value="">Select Employee</option>';

                employeesResponse.data.forEach(employee => {
                    const option = document.createElement('option');
                    option.value = employee.id;
                    option.textContent = `${employee.name} (${employee.department})`;
                    employeeSelect.appendChild(option);
                });
            }

            // Set device in the device dropdown
            const deviceSelect = document.getElementById('assign-device-device');
            if (deviceSelect) {
                deviceSelect.innerHTML = '';
                const option = document.createElement('option');
                option.value = device.id;
                option.textContent = `✓ ${device.device_name} (${device.device_type})`;
                option.selected = true;
                deviceSelect.appendChild(option);
            }

            // Set today as default assignment date
            const dateInput = document.getElementById('assign-device-date');
            if (dateInput) {
                dateInput.value = new Date().toISOString().split('T')[0];
            }

            // Store device info for later use
            const form = document.getElementById('assign-device-form');
            if (form) {
                form.dataset.deviceId = device.id;
            }

            // 移除旧的事件监听器(如果有)
            const confirmBtn = document.getElementById('confirm-assign-btn');
            if (confirmBtn) {
                const newConfirmBtn = confirmBtn.cloneNode(true);
                confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

                // 添加新的事件监听器
                newConfirmBtn.addEventListener('click', function() {
                    console.log('Confirm button clicked'); // 调试用
                    createDeviceAssignment();
                });
            }

            // Initialize and show the modal
            const modal = new bootstrap.Modal(document.getElementById('assign-device-modal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error loading employees:', error);
            showAlert('Failed to load employee data for assignment', 'danger');
        });
}

// 改进createDeviceAssignment函数，添加更多调试信息
function createDeviceAssignment() {
    console.log('createDeviceAssignment function called'); // 调试用

    const form = document.getElementById('assign-device-form');
    if (!form) {
        console.error('Assignment form not found');
        showAlert('Form not found', 'danger');
        return;
    }

    const deviceId = form.dataset.deviceId;
    if (!deviceId) {
        console.error('Device ID not found in form data');
        showAlert('Device information missing', 'danger');
        return;
    }

    // Get form values
    const employeeSelect = document.getElementById('assign-device-employee');
    const employeeId = employeeSelect ? employeeSelect.value : null;

    const assignmentDateInput = document.getElementById('assign-device-date');
    const assignmentDate = assignmentDateInput ? assignmentDateInput.value : null;

    const notesInput = document.getElementById('assign-device-notes');
    const notes = notesInput ? notesInput.value : '';

    console.log('Form data:', { deviceId, employeeId, assignmentDate, notes }); // 调试用

    // Validate required fields
    if (!employeeId) {
        showAlert('Please select an employee', 'warning');
        return;
    }

    if (!assignmentDate) {
        showAlert('Please select an assignment date', 'warning');
        return;
    }

    // Prepare data for API
    const data = {
        employee_id: parseInt(employeeId),
        inventory_id: parseInt(deviceId),
        assignment_date: assignmentDate,
        notes: notes || `Device assigned on ${new Date().toLocaleDateString()}`,
        status: 'active'
    };

    console.log('Sending data to API:', data); // 调试用

    // Send create request
    fetch('/api/employee-assets', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log('API response status:', response.status); // 调试用
        return response.json();
    })
    .then(result => {
        console.log('API response:', result); // 调试用

        if (result.success) {
            // Close modal
            const modalElement = document.getElementById('assign-device-modal');
            if (modalElement) {
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                } else {
                    console.warn('Modal instance not found');
                    modalElement.classList.remove('show');
                    document.body.classList.remove('modal-open');
                    const backdrop = document.querySelector('.modal-backdrop');
                    if (backdrop) backdrop.remove();
                }
            }

            // Show success message
            showAlert('Device assigned successfully', 'success');

            // Publish asset assignment event
            const event = {
                name: 'assetAssigned',
                data: {
                    inventoryId: data.inventory_id,
                    employeeId: data.employee_id,
                    status: 'active'
                },
                timestamp: new Date().getTime()
            };
            localStorage.setItem('assetEvent', JSON.stringify(event));

            // Refresh inventory data
            fetchInventoryData();
        } else {
            showAlert(`Error: ${result.error || 'Unknown error'}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error assigning device:', error);
        showAlert('An error occurred while assigning the device', 'danger');
    });
}

function showAddDeviceModal() {
   // Reset form
   const form = document.getElementById('add-device-form');
   if (form) form.reset();

   // Set today as default purchase date
   const dateInput = document.getElementById('device-purchase-date');
   if (dateInput) {
       const today = new Date();
       const formattedDate = today.toISOString().split('T')[0];
       dateInput.value = formattedDate;
   }

   // Show modal
   const modal = new bootstrap.Modal(document.getElementById('add-device-modal'));
   modal.show();

   // Set form submit handler
   if (form) {
       form.onsubmit = function(event) {
           event.preventDefault();
           addDevice(form);
       };
   }
}

function addDevice(form) {
   // Get form data
   const formData = new FormData(form);
   const data = {
       device_name: formData.get('device_name'),
       device_type: formData.get('device_type'),
       location: formData.get('location') || 'Headquarters',
       price_per_unit: parseFloat(formData.get('price_per_unit')),
       quantity: 1, // New devices default to quantity 1
       last_updated: formData.get('purchase_date'),
       notes: formData.get('notes') || ''
   };

   // Send to server
   fetch('/api/inventory', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json'
       },
       body: JSON.stringify(data)
   })
   .then(response => response.json())
   .then(result => {
       if (result.success) {
           // Hide modal
           const modal = bootstrap.Modal.getInstance(document.getElementById('add-device-modal'));
           modal.hide();

           // Show success message
           showAlert('Device added successfully', 'success');

           // Refresh data
           fetchInventoryData();

           // Publish device added event for cross-page communication
           const event = {
               name: 'deviceAdded',
               data: {
                   deviceId: result.data?.id || null
               },
               timestamp: new Date().getTime()
           };
           localStorage.setItem('assetEvent', JSON.stringify(event));
       } else {
           showAlert(`Error: ${result.error}`, 'danger');
       }
   })
   .catch(error => {
       console.error('Error adding device:', error);
       showAlert('An error occurred while adding the device', 'danger');
   });
}

function applyFilters() {
   // Get filter values
   const typeFilter = document.getElementById('device-type-filter');
   const statusFilter = document.getElementById('status-filter');
   const searchInput = document.getElementById('search-input');

   // Build query parameters
   const params = new URLSearchParams();

   if (typeFilter && typeFilter.value !== 'All') {
       params.append('device_type', typeFilter.value);
   }

   // Handle simplified status filter
   if (statusFilter && statusFilter.value !== 'All') {
       params.append('status', statusFilter.value);
   }

   if (searchInput && searchInput.value.trim()) {
       params.append('search', searchInput.value.trim());
   }

   // Send filtered request to API
   fetch(`/api/inventory?${params.toString()}`)
       .then(response => response.json())
       .then(data => {
           // Display filtered devices
           populateInventoryTable(data.data);
           // Update summary information
           updateInventorySummary(data);
       })
       .catch(error => {
           console.error('Error fetching filtered inventory data:', error);
       });
}

function updateFilteredSummary(summary) {
   document.getElementById('total-devices').textContent = summary.total || '-';
   document.getElementById('available-devices').textContent = summary.available || '-';
   document.getElementById('assigned-devices').textContent = summary.assigned || '-';
}

function showAlert(message, type = 'info') {
   const alertContainer = document.getElementById('alert-container');
   if (!alertContainer) return;

   const alert = document.createElement('div');
   alert.className = `alert alert-${type} alert-dismissible fade show`;
   alert.innerHTML = `
       ${message}
       <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
   `;

   alertContainer.appendChild(alert);

   // Auto-close after 5 seconds
   setTimeout(() => {
       alert.classList.remove('show');
       setTimeout(() => {
           if (alertContainer.contains(alert)) {
               alertContainer.removeChild(alert);
           }
       }, 150);
   }, 5000);
}

function formatCurrency(value) {
   return new Intl.NumberFormat('en-US', {
       style: 'currency',
       currency: 'USD',
       minimumFractionDigits: 0,
       maximumFractionDigits: 0
   }).format(value || 0);
}