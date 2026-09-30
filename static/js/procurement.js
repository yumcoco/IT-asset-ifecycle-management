// static/js/procurement.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize procurement page
    console.log("Procurement page initialized");

    // Load counts for KPI cards
    loadOrderCounts();

    // Initialize tab content - load the currently active tab
    const activeTab = document.querySelector('.nav-link.active');
    const initialTabType = activeTab ?
        activeTab.textContent.trim().toLowerCase().split(' ')[0] : 'all';

    loadTabContent(initialTabType);

    // Set up tab switching
    const orderTabs = document.querySelectorAll('.nav-link');
    orderTabs.forEach(tab => {
        tab.addEventListener('click', function(e) {
            // Don't prevent default - allow bootstrap tab behavior

            // Get tab type from text content
            const tabText = this.textContent.trim().toLowerCase();
            let tabType;

            if (tabText.includes('all')) {
                tabType = 'all';
            } else if (tabText.includes('pending')) {
                tabType = 'pending';
            } else if (tabText.includes('transit')) {
                tabType = 'in-transit';
            } else if (tabText.includes('completed')) {
                tabType = 'completed';
            } else {
                tabType = tabText.split(' ')[0];
            }

            console.log(`Tab clicked: ${tabText}, using type: ${tabType}`);

            // Load content for this tab
            loadTabContent(tabType);
        });
    });

    // Set up new purchase order button
    const createOrderBtn = document.querySelector('.btn-primary[data-id="new-purchase-order"], button:contains("New Purchase Order")');
    if (createOrderBtn) {
        createOrderBtn.addEventListener('click', function() {
            alert("This feature would create a new purchase order form");
            // In a real implementation, this would show a modal or redirect to a form
        });
    }

    // Function to load order counts for KPI cards
    function loadOrderCounts() {
        fetch('/api/orders/counts')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`API responded with status ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Order counts received:", data);
                updateOrderCountCards(data);
            })
            .catch(error => {
                console.error('Error fetching order counts:', error);
                // Use fallback values on error
                updateOrderCountCards({
                    open: 12,
                    pending: 3,
                    in_transit: 5,
                    completed: 45
                });
            });
    }

    // Update the KPI cards with order counts
    function updateOrderCountCards(counts) {
        // Find the KPI card elements - look for both ID and text content
        const cards = document.querySelectorAll('.card');

        cards.forEach(card => {
            const titleElement = card.querySelector('.card-title');
            if (!titleElement) return;

            const title = titleElement.textContent.trim().toLowerCase();
            const valueElement = card.querySelector('h2');
            if (!valueElement) return;

            // Update based on card title
            if (title.includes('open')) {
                valueElement.textContent = counts.open || 0;
            } else if (title.includes('pending')) {
                valueElement.textContent = counts.pending || 0;
            } else if (title.includes('transit')) {
                valueElement.textContent = counts.in_transit || 0;
            } else if (title.includes('completed')) {
                valueElement.textContent = counts.completed || 0;
            }
        });
    }

    // Function to load tab content
    function loadTabContent(tabType) {
        console.log(`Loading ${tabType} orders`);

        // Map tab types to status values expected by the API
        const statusMap = {
            'all': '',
            'pending': 'pending',
            'in-transit': 'in-transit',
            'completed': 'delivered'
        };

        const status = statusMap[tabType] || '';
        console.log(`Mapped status for API: ${status}`);

        // Fetch orders from API
        fetch(`/api/orders?status=${status}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`API responded with status ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log(`Received ${data.data ? data.data.length : 0} orders from API`);
                displayOrders(data.data || [], tabType);
            })
            .catch(error => {
                console.error('Error fetching orders:', error);
                // Use mock data on error
                const mockOrders = generateMockOrders(tabType);
                console.log(`Using ${mockOrders.length} mock orders instead`);
                displayOrders(mockOrders, tabType);
            });
    }

    // Display orders in the table
    function displayOrders(orders, tabType) {
        // Find the table container - try multiple selectors
        const container = document.querySelector('.tab-content') ||
                         document.querySelector('#order-list-container') ||
                         document.querySelector('.table-responsive') ||
                         document.querySelector('.card-body') ||
                         document.querySelector('.row');

        if (!container) {
            console.error('Order container not found');
            return;
        }

        console.log(`Found container for orders table:`, container);

        // Create table HTML
        let tableHtml = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>ORDER #</th>
                        <th>VENDOR</th>
                        <th>DATE</th>
                        <th>ITEMS</th>
                        <th>TOTAL</th>
                        <th>STATUS</th>
                        <th>ACTIONS</th>
                    </tr>
                </thead>
                <tbody>`;

        // If no orders, show message
        if (orders.length === 0) {
            tableHtml += `
                <tr>
                    <td colspan="7" class="text-center">No ${tabType} orders found</td>
                </tr>`;
        } else {
            // Add order rows
            orders.forEach(order => {
                // Format the status badge
                let statusBadge;
                let statusText;

                switch(order.status) {
                    case 'pending':
                        statusBadge = 'bg-warning';
                        statusText = 'Pending Approval';
                        break;
                    case 'in-transit':
                        statusBadge = 'bg-info';
                        statusText = 'In Transit';
                        break;
                    case 'delivered':
                    case 'completed':
                        statusBadge = 'bg-success';
                        statusText = 'Completed';
                        break;
                    case 'cancelled':
                        statusBadge = 'bg-danger';
                        statusText = 'Cancelled';
                        break;
                    case 'open':
                    default:
                        statusBadge = 'bg-secondary';
                        statusText = 'Open';
                }

                // Format the order number
                const orderNumber = order.orderNumber || `PO-2025-${order.id.toString().padStart(3, '0')}`;

                // Format the date
                let dateDisplay = order.date ||
                                 (order.order_date ? new Date(order.order_date).toISOString().split('T')[0] : '');

                // Format total cost
                let totalDisplay = order.total ||
                                  (order.total_cost ? `$${order.total_cost.toLocaleString()}` : '$0');

                // Get vendor name
                let vendorName = order.vendor || order.supplier_name || 'Unknown Vendor';

                // Get item count
                let itemCount = order.items || order.item_count || '1';

                tableHtml += `
                    <tr>
                        <td>${orderNumber}</td>
                        <td>${vendorName}</td>
                        <td>${dateDisplay}</td>
                        <td>${itemCount}</td>
                        <td>${totalDisplay}</td>
                        <td><span class="badge ${statusBadge}">${statusText}</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary view-btn" data-id="${order.id}">
                                <i class="bi bi-eye"></i>
                            </button>
                            ${order.status === 'pending' ? 
                                `<button class="btn btn-sm btn-outline-success approve-btn" data-id="${order.id}">
                                    <i class="bi bi-check-lg"></i>
                                </button>` : ''}
                        </td>
                    </tr>`;
            });
        }

        tableHtml += `
                </tbody>
            </table>`;

        // Update the container
        container.innerHTML = tableHtml;

        // Add event listeners to buttons
        attachButtonEventListeners();
    }

    // Function to generate fallback mock orders if API fails
    function generateMockOrders(tabType) {
        // Number of orders to match KPI cards
        const orderCounts = {
            'all': 65,  // Total of all orders
            'open': 12,
            'pending': 3,
            'in-transit': 5,
            'completed': 45
        };

        const count = orderCounts[tabType] || 15;
        let status;

        // For 'all' tab, generate a mix of statuses
        if (tabType === 'all') {
            status = '';
        } else if (tabType === 'completed') {
            status = 'delivered'; // Match the database status
        } else {
            status = tabType;
        }

        const orders = [];
        for (let i = 1; i <= count; i++) {
            // For 'all' tab, distribute orders across statuses based on KPI counts
            let orderStatus = status;
            if (tabType === 'all') {
                if (i <= 12) {
                    orderStatus = 'open';
                } else if (i <= 15) {
                    orderStatus = 'pending';
                } else if (i <= 20) {
                    orderStatus = 'in-transit';
                } else {
                    orderStatus = 'delivered';
                }
            }

            orders.push({
                id: i,
                orderNumber: `PO-2025-${i.toString().padStart(3, '0')}`,
                vendor: ['Dell Technologies', 'Apple Inc.', 'Lenovo', 'HP Inc.', 'Microsoft', 'Samsung', 'ASUS'][Math.floor(Math.random() * 7)],
                date: `2025-${(Math.floor(Math.random() * 5) + 1).toString().padStart(2, '0')}-${(Math.floor(Math.random() * 28) + 1).toString().padStart(2, '0')}`,
                items: Math.floor(Math.random() * 15) + 1,
                total: `$${(Math.floor(Math.random() * 15000) + 1000).toLocaleString()}`,
                status: orderStatus
            });
        }

        return orders;
    }

    // Function to attach event listeners to buttons
    function attachButtonEventListeners() {
        // Set up view buttons
        const viewButtons = document.querySelectorAll('.view-btn');
        viewButtons.forEach(button => {
            button.addEventListener('click', function() {
                const orderId = this.getAttribute('data-id');
                const row = this.closest('tr');
                const orderNumber = row.cells[0].textContent;
                alert(`Viewing details for order ${orderNumber}`);
                // In a real implementation, this would show order details
            });
        });

        // Set up approve buttons
       const approveButtons = document.querySelectorAll('.approve-btn');
approveButtons.forEach(button => {
    button.addEventListener('click', function() {
        const orderId = this.getAttribute('data-id');
        const row = this.closest('tr');
        const orderNumber = row.cells[0].textContent;

        if (confirm(`Are you sure you want to approve order ${orderNumber}?`)) {
            // 发送API请求更新服务器上的状态
            fetch(`/api/orders/${orderId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    status: 'in-transit'
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    // 更新UI
                    row.cells[5].innerHTML = '<span class="badge bg-info">In Transit</span>';
                    alert(`Order ${orderNumber} has been approved`);

                    // 更新计数卡
                    updateCountsAfterApproval();
                } else {
                    alert(`Error: ${result.error}`);
                }
            })
            .catch(error => {
                console.error('Error updating order status:', error);
                alert('An error occurred while updating the order status');
            });
        }
    });
});}
    // Update counts after approval action
    function updateCountsAfterApproval() {
        // Find the KPI card elements
        const cards = document.querySelectorAll('.card');
        let pendingCount = 0;
        let transitCount = 0;

        cards.forEach(card => {
            const titleElement = card.querySelector('.card-title');
            if (!titleElement) return;

            const title = titleElement.textContent.trim().toLowerCase();
            const valueElement = card.querySelector('h2');
            if (!valueElement) return;

            if (title.includes('pending')) {
                pendingCount = parseInt(valueElement.textContent) || 0;
                if (pendingCount > 0) {
                    valueElement.textContent = pendingCount - 1;
                }
            } else if (title.includes('transit')) {
                transitCount = parseInt(valueElement.textContent) || 0;
                valueElement.textContent = transitCount + 1;
            }
        });
    }

    // Utility function to check if an element contains text
    Element.prototype.contains = function(text) {
        return this.textContent.includes(text);
    };
});