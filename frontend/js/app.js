// Main Application JavaScript
class FarmTrackApp {
    constructor() {
        this.apiBase = 'http://localhost:5000/api';
        this.currentProduct = null;
        this.stakeholders = {};
        this.qrScanner = null;
        this.currentQRBlob = null;
        this.init();
    }

    init() {
        this.setupNavigation();
        this.loadDashboard();
        this.setupEventListeners();
        this.loadStakeholders();
        this.initQRScanner();
    }

    setupNavigation() {
        // Nav toggle for mobile
        const navToggle = document.querySelector('.nav-toggle');
        const navMenu = document.querySelector('.nav-menu');

        if (navToggle) {
            navToggle.addEventListener('click', () => {
                navMenu.classList.toggle('active');
            });
        }

        // Nav link clicks
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = e.target.getAttribute('href')?.substring(1);
                if (target) {
                    this.showSection(target);

                    // Update active nav link
                    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                    e.target.classList.add('active');

                    // Close mobile menu
                    if (navMenu) {
                        navMenu.classList.remove('active');
                    }
                }
            });
        });
    }

    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.remove('active');
        });

        // Show target section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');

            // Load section-specific data
            switch(sectionId) {
                case 'dashboard':
                    this.loadDashboard();
                    break;
                case 'products':
                    this.loadProducts();
                    break;
                case 'analytics':
                    this.loadAnalytics();
                    break;
                case 'track':
                    this.setupTrackSection();
                    break;
                case 'register':
                    this.setupRegisterSection();
                    break;
            }
        }
    }

    async loadStakeholders() {
        try {
            const response = await fetch(`${this.apiBase}/stakeholders`);
            this.stakeholders = await response.json();
        } catch (error) {
            console.error('Error loading stakeholders:', error);
            this.stakeholders = {
                "farmer_001": "Organic Farms Co.",
                "distributor_002": "Fresh Distributors Ltd.",
                "retailer_003": "Green Grocers Market",
                "consumer_004": "End Consumer",
                "processor_005": "Quality Processors Inc."
            };
        }
    }

    async loadDashboard() {
        try {
            const response = await fetch(`${this.apiBase}/stats`);
            const stats = await response.json();

            // Update stats
            document.getElementById('total-products').textContent = stats.total_products;
            document.getElementById('total-transactions').textContent = stats.total_transactions;
            document.getElementById('authentic-products').textContent = '100%';

            // Load recent activity
            this.loadRecentActivity(stats.recent_activity);
        } catch (error) {
            console.error('Error loading dashboard:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    loadRecentActivity(activities) {
        const activityList = document.getElementById('activity-list');
        if (!activityList) return;

        activityList.innerHTML = '';

        if (!activities || activities.length === 0) {
            activityList.innerHTML = '<div class="no-data">No recent activity</div>';
            return;
        }

        activities.slice(-5).reverse().forEach(activity => {
            const activityItem = this.createActivityItem(activity);
            activityList.appendChild(activityItem);
        });
    }

    createActivityItem(activity) {
        const div = document.createElement('div');
        div.className = 'activity-item';

        let icon, color, message;

        switch(activity.type) {
            case 'REGISTER':
                icon = 'fa-seedling';
                color = '#4caf50';
                message = `New product ${activity.productName} (${activity.productId}) registered by ${activity.by_name}`;
                break;
            case 'TRANSFER':
                icon = 'fa-exchange-alt';
                color = '#2196f3';
                message = `${activity.productName} transferred from ${activity.from_name} to ${activity.to_name} for $${activity.price}`;
                break;
            case 'QUALITY_CHECK':
                icon = 'fa-clipboard-check';
                color = '#ff9800';
                message = `Quality check for ${activity.productName} by ${activity.by_name}: ${activity.quality_note}`;
                break;
            default:
                icon = 'fa-info-circle';
                color = '#666';
                message = 'Activity recorded';
        }

        div.innerHTML = `
            <div class="activity-icon" style="background: ${color}">
                <i class="fas ${icon}"></i>
            </div>
            <div class="activity-content">
                <p>${message}</p>
                <div class="activity-time">${new Date(activity.timestamp).toLocaleString()}</div>
            </div>
        `;

        return div;
    }

    async loadProducts() {
        try {
            const response = await fetch(`${this.apiBase}/products`);
            const products = await response.json();
            this.displayProducts(products);
        } catch (error) {
            console.error('Error loading products:', error);
            this.showError('Failed to load products');
        }
    }

    displayProducts(products) {
        const grid = document.getElementById('products-grid');
        if (!grid) return;

        grid.innerHTML = '';

        if (!products || products.length === 0) {
            grid.innerHTML = '<div class="no-data">No products found</div>';
            return;
        }

        products.forEach(product => {
            const card = this.createProductCard(product);
            grid.appendChild(card);
        });
    }

    createProductCard(product) {
        const card = document.createElement('div');
        card.className = 'product-card';

        card.innerHTML = `
            <div class="product-header">
                <h3>${this.escapeHtml(product.name)}</h3>
                <div class="product-id">${product.id}</div>
            </div>
            <div class="product-body">
                <div class="product-info">
                    <p><span>Origin:</span> <span>${this.escapeHtml(product.origin)}</span></p>
                    <p><span>Harvest Date:</span> <span>${product.harvest_date}</span></p>
                    <p><span>Current Owner:</span> <span>${this.escapeHtml(product.current_owner)}</span></p>
                    <p><span>Transactions:</span> <span>${product.transaction_count}</span></p>
                </div>
                <div class="product-actions">
                    <button class="btn-primary" onclick="event.stopPropagation(); app.trackProduct('${product.id}')">
                        <i class="fas fa-search"></i> Track
                    </button>
                    <button class="btn-qr" onclick="event.stopPropagation(); app.generateAndDisplayQR('${product.id}')">
                        <i class="fas fa-qrcode"></i> QR Code
                    </button>
                    <button class="btn-verify" onclick="event.stopPropagation(); app.verifyProduct('${product.id}')">
                        <i class="fas fa-shield-alt"></i> Verify
                    </button>
                    <button class="btn-secondary" onclick="event.stopPropagation(); app.transferProduct('${product.id}')">
                        <i class="fas fa-exchange-alt"></i> Transfer
                    </button>
                    <button class="btn-warning" onclick="event.stopPropagation(); app.addQualityCheck('${product.id}')">
                        <i class="fas fa-clipboard-check"></i> Quality
                    </button>
                </div>
            </div>
        `;

        return card;
    }

    setupTrackSection() {
        // Clear previous results
        const resultsDiv = document.getElementById('track-results');
        if (resultsDiv) {
            resultsDiv.innerHTML = '<div class="track-placeholder">Enter a product ID above to track its journey</div>';
        }

        // Hide QR display
        const qrDisplay = document.getElementById('qr-display');
        if (qrDisplay) {
            qrDisplay.style.display = 'none';
        }
    }

    setupRegisterSection() {
        // Set today's date as default harvest date
        const today = new Date().toISOString().split('T')[0];
        const harvestDateInput = document.getElementById('harvest-date');
        if (harvestDateInput) {
            harvestDateInput.value = today;
        }
    }

    // ============ QR CODE FUNCTIONALITY ============

    initQRScanner() {
        // Check if html5-qrcode is loaded
        if (typeof Html5Qrcode !== 'undefined') {
            this.qrScanner = new Html5Qrcode("qr-reader");
        } else {
            console.log('QR Scanner library not loaded');
        }
    }

    async generateAndDisplayQR(productId) {
        try {
            // Show loading state
            this.showNotification('Generating QR code...', 'info');

            const response = await fetch(`${this.apiBase}/products/${productId}/qrcode`);

            if (!response.ok) {
                throw new Error('QR code generation failed');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            // Store for download
            this.currentQRBlob = blob;
            this.currentProductId = productId;

            // Display in modal
            this.showQRModal(productId, url);

            this.showSuccess('QR code generated successfully!');

        } catch (error) {
            console.error('Error generating QR code:', error);
            this.showError('Failed to generate QR code: ' + error.message);
        }
    }

    showQRModal(productId, qrUrl) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'qr-modal';
        modal.style.display = 'block';

        modal.innerHTML = `
            <div class="modal-content qr-modal-content">
                <span class="close" onclick="app.closeQRModal()">&times;</span>
                <h3><i class="fas fa-qrcode"></i> QR Code for Product</h3>
                <div class="qr-display-container">
                    <div class="qr-result">
                        <div class="qr-image-wrapper">
                            <img src="${qrUrl}" alt="QR Code for ${productId}" class="qr-code-image">
                        </div>
                        <div class="qr-info">
                            <p><strong>Product ID:</strong> ${productId}</p>
                            <p><strong>Verification URL:</strong> <br>
                            <small>http://localhost:5000/verify/${productId}</small></p>
                        </div>
                        <div class="qr-actions">
                            <button onclick="app.downloadQR()" class="btn-primary">
                                <i class="fas fa-download"></i> Download QR
                            </button>
                            <button onclick="app.printQR()" class="btn-secondary">
                                <i class="fas fa-print"></i> Print
                            </button>
                            <button onclick="app.closeQRModal()" class="btn-secondary">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeQRModal();
            }
        });
    }

    closeQRModal() {
        const modal = document.getElementById('qr-modal');
        if (modal) {
            modal.remove();
        }
        // Clear the QR display in track section
        const qrDisplay = document.getElementById('qr-display');
        if (qrDisplay) {
            qrDisplay.style.display = 'none';
        }
    }

    downloadQR() {
        if (this.currentQRBlob) {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(this.currentQRBlob);
            link.download = `product_${this.currentProductId}_qr.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            this.showSuccess('QR code downloaded successfully!');
        } else {
            this.showError('No QR code to download');
        }
    }

    printQR() {
        const qrImage = document.querySelector('.qr-code-image');
        if (qrImage) {
            const printWindow = window.open('', '_blank');
            if (printWindow) {
                printWindow.document.write(`
                    <html>
                        <head>
                            <title>QR Code - Product ${this.currentProductId}</title>
                            <style>
                                body { display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                                .print-container { text-align: center; }
                                img { max-width: 400px; }
                            </style>
                        </head>
                        <body>
                            <div class="print-container">
                                <img src="${qrImage.src}" alt="QR Code">
                                <h3>Product: ${this.currentProductId}</h3>
                                <p>Scan to verify authenticity</p>
                            </div>
                        </body>
                    </html>
                `);
                printWindow.document.close();
                printWindow.print();
            }
        }
    }

    // QR Scanner functionality
    startQRScanner() {
        const readerContainer = document.getElementById('qr-reader');
        if (!readerContainer) {
            this.showError('QR reader container not found');
            return;
        }

        if (!this.qrScanner) {
            this.showError('QR scanner not initialized. Please refresh the page.');
            return;
        }

        // Show the reader
        readerContainer.style.display = 'block';
        this.showNotification('Scanning QR code...', 'info');

        // Check if camera is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showError('Camera access is not supported in this browser');
            return;
        }

        this.qrScanner.start(
            { facingMode: "environment" },
            {
                fps: 10,
                qrbox: { width: 250, height: 250 }
            },
            (decodedText, decodedResult) => {
                // Success callback
                this.handleQRScan(decodedText);
            },
            (errorMessage) => {
                // Error callback - ignore
                console.log('QR Scan error:', errorMessage);
            }
        ).then(() => {
            this.showNotification('Camera started. Scan a QR code.', 'info');
        }).catch((err) => {
            console.error('Error starting QR scanner:', err);
            this.showError('Could not access camera. Please allow camera access.');
            readerContainer.style.display = 'none';
        });
    }

    handleQRScan(decodedText) {
        try {
            // Try to parse as JSON
            const data = JSON.parse(decodedText);
            if (data.product_id) {
                this.trackProduct(data.product_id);
                this.stopQRScanner();
                this.showSuccess('QR scanned successfully!');
                return;
            }
        } catch (e) {
            // Not JSON, try to extract product ID from URL or text
            console.log('QR data not JSON, trying to extract ID');
        }

        // Try to find product ID in text
        const productIdMatch = decodedText.match(/PROD_\d+/);
        if (productIdMatch) {
            this.trackProduct(productIdMatch[0]);
            this.stopQRScanner();
            this.showSuccess('QR scanned successfully!');
        } else {
            this.showError('Invalid QR code. Could not find product ID.');
            this.stopQRScanner();
        }
    }

    stopQRScanner() {
        if (this.qrScanner) {
            this.qrScanner.stop().then(() => {
                const readerContainer = document.getElementById('qr-reader');
                if (readerContainer) {
                    readerContainer.style.display = 'none';
                }
                console.log('QR scanner stopped');
            }).catch((err) => {
                console.error('Error stopping QR scanner:', err);
            });
        }
    }

    // ============ TRACK PRODUCT ============

    async trackProduct(productId = null) {
        const inputId = productId || document.getElementById('track-product-id')?.value.trim();

        if (!inputId) {
            this.showError('Please enter a product ID');
            return;
        }

        try {
            this.showNotification('Loading product data...', 'info');

            const response = await fetch(`${this.apiBase}/products/${inputId}`);
            if (!response.ok) {
                throw new Error('Product not found');
            }

            const product = await response.json();
            this.currentProduct = product;
            this.displayTrackResults(product);
            this.showSection('track');

            // Auto-generate QR for the tracked product
            await this.generateAndDisplayQRInTrack(product.id);

        } catch (error) {
            this.showError('Product not found. Please check the ID and try again.');
            console.error('Error tracking product:', error);
        }
    }

    async generateAndDisplayQRInTrack(productId) {
        try {
            const response = await fetch(`${this.apiBase}/products/${productId}/qrcode`);
            if (!response.ok) {
                throw new Error('QR generation failed');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            this.currentQRBlob = blob;
            this.currentProductId = productId;

            // Display QR in track section
            const qrDisplay = document.getElementById('qr-display');
            if (qrDisplay) {
                qrDisplay.style.display = 'block';
                qrDisplay.innerHTML = `
                    <div class="qr-display-container">
                        <h4><i class="fas fa-qrcode"></i> Product QR Code</h4>
                        <div class="qr-result">
                            <img src="${url}" alt="QR Code" class="qr-code-image">
                            <div class="qr-actions">
                                <button onclick="app.downloadQR()" class="btn-primary">
                                    <i class="fas fa-download"></i> Download
                                </button>
                                <button onclick="app.printQR()" class="btn-secondary">
                                    <i class="fas fa-print"></i> Print
                                </button>
                                <button onclick="app.viewQRFull()" class="btn-info">
                                    <i class="fas fa-expand"></i> View Full
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error generating QR in track:', error);
        }
    }

    viewQRFull() {
        if (this.currentProductId) {
            this.generateAndDisplayQR(this.currentProductId);
        }
    }

    displayTrackResults(product) {
        const resultsDiv = document.getElementById('track-results');
        if (!resultsDiv) return;

        resultsDiv.innerHTML = `
            <div class="track-results-header">
                <h3><i class="fas fa-search"></i> Product Journey: ${this.escapeHtml(product.name)}</h3>
                <div class="product-status">
                    <span class="status-badge verified">
                        <i class="fas fa-check-circle"></i> Verified
                    </span>
                </div>
            </div>
            ${this.createJourneyTimeline(product).outerHTML}
            ${this.createProductAnalytics(product).outerHTML}
        `;
    }

    createJourneyTimeline(product) {
        const timeline = document.createElement('div');
        timeline.className = 'journey-timeline';

        let html = `
            <div class="product-summary">
                <h4>Product Information</h4>
                <div class="summary-grid">
                    <div class="summary-item">
                        <label>Product ID:</label>
                        <span>${product.id}</span>
                    </div>
                    <div class="summary-item">
                        <label>Name:</label>
                        <span>${this.escapeHtml(product.name)}</span>
                    </div>
                    <div class="summary-item">
                        <label>Origin:</label>
                        <span>${this.escapeHtml(product.origin)}</span>
                    </div>
                    <div class="summary-item">
                        <label>Harvest Date:</label>
                        <span>${product.harvest_date}</span>
                    </div>
                    <div class="summary-item">
                        <label>Current Owner:</label>
                        <span>${this.escapeHtml(product.current_owner_name || product.current_owner)}</span>
                    </div>
                </div>
            </div>
            <div class="timeline-container">
                <h4><i class="fas fa-route"></i> Supply Chain Journey</h4>
                <div class="timeline">
        `;

        if (product.transaction_history && product.transaction_history.length > 0) {
            product.transaction_history.forEach((transaction, index) => {
                html += this.createTimelineItem(transaction, index);
            });
        } else {
            html += '<div class="no-data">No transaction history available</div>';
        }

        html += '</div></div>';
        timeline.innerHTML = html;
        return timeline;
    }

    createTimelineItem(transaction, index) {
        const action = transaction.action || 'TRANSFER';
        const from = transaction.from_name || transaction.from_address || 'Origin';
        const to = transaction.to_name || transaction.to_address || 'Current';
        const price = transaction.price ? `$${transaction.price}` : 'N/A';
        const quality = transaction.quality_update || 'No quality update';

        return `
            <div class="timeline-item">
                <div class="timeline-marker">
                    <div class="marker-icon">
                        <i class="fas ${this.getActionIcon(action)}"></i>
                    </div>
                </div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <h5>${action.replace('_', ' ')}</h5>
                        <span class="timeline-time">${new Date(transaction.timestamp).toLocaleString()}</span>
                    </div>
                    <div class="timeline-details">
                        <p><strong>From:</strong> ${this.escapeHtml(from)}</p>
                        <p><strong>To:</strong> ${this.escapeHtml(to)}</p>
                        ${price !== 'N/A' ? `<p><strong>Price:</strong> ${price}</p>` : ''}
                        <p><strong>Quality Note:</strong> ${this.escapeHtml(quality)}</p>
                    </div>
                </div>
            </div>
        `;
    }

    createProductAnalytics(product) {
        const analytics = document.createElement('div');
        analytics.className = 'product-analytics';

        const totalTransactions = product.transaction_history?.length || 0;
        const priceHistory = product.price_history || [];
        const initialPrice = priceHistory[0]?.price || 0;
        const finalPrice = priceHistory[priceHistory.length - 1]?.price || 0;
        const priceIncrease = finalPrice - initialPrice;
        const priceIncreasePercent = initialPrice > 0 ? ((priceIncrease / initialPrice) * 100).toFixed(1) : 0;

        analytics.innerHTML = `
            <h4><i class="fas fa-chart-bar"></i> Product Analytics</h4>
            <div class="analytics-grid">
                <div class="analytics-card">
                    <div class="analytics-icon">
                        <i class="fas fa-exchange-alt"></i>
                    </div>
                    <div class="analytics-info">
                        <h3>${totalTransactions}</h3>
                        <p>Total Transactions</p>
                    </div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="analytics-info">
                        <h3>$${finalPrice}</h3>
                        <p>Current Value</p>
                    </div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-icon">
                        <i class="fas fa-percentage"></i>
                    </div>
                    <div class="analytics-info">
                        <h3>${priceIncreasePercent}%</h3>
                        <p>Price Increase</p>
                    </div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-icon">
                        <i class="fas fa-users"></i>
                    </div>
                    <div class="analytics-info">
                        <h3>${new Set(product.transaction_history?.map(t => t.from_address).concat(product.transaction_history?.map(t => t.to_address))).size || 1}</h3>
                        <p>Stakeholders</p>
                    </div>
                </div>
            </div>
        `;

        return analytics;
    }

    getActionIcon(action) {
        switch(action) {
            case 'REGISTERED': return 'fa-seedling';
            case 'TRANSFER': return 'fa-exchange-alt';
            case 'QUALITY_CHECK': return 'fa-clipboard-check';
            default: return 'fa-circle';
        }
    }

    async verifyProduct(productId) {
        try {
            const response = await fetch(`${this.apiBase}/products/${productId}/verify`);
            const result = await response.json();

            if (result.authentic) {
                this.showSuccess(`✅ Product ${productId} is authentic and verified on blockchain!`);
            } else {
                this.showError(`❌ Product ${productId} is not authentic or not found.`);
            }
        } catch (error) {
            this.showError('Error verifying product');
            console.error('Error verifying product:', error);
        }
    }

    async transferProduct(productId) {
        const product = await this.getProductData(productId);
        if (!product) return;

        const modal = this.createTransferModal(product);
        document.body.appendChild(modal);
        this.showModal(modal);
    }

    async addQualityCheck(productId) {
        const product = await this.getProductData(productId);
        if (!product) return;

        const modal = this.createQualityCheckModal(product);
        document.body.appendChild(modal);
        this.showModal(modal);
    }

    async getProductData(productId) {
        try {
            const response = await fetch(`${this.apiBase}/products/${productId}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('Error fetching product data:', error);
        }
        return null;
    }

    createTransferModal(product) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close">&times;</span>
                <h3><i class="fas fa-exchange-alt"></i> Transfer Product: ${this.escapeHtml(product.name)}</h3>
                <form id="transfer-form" class="modal-form">
                    <input type="hidden" name="product_id" value="${product.id}">

                    <div class="form-group">
                        <label>From:</label>
                        <select name="from_address" required>
                            <option value="${product.current_owner}">${product.current_owner_name || product.current_owner}</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>To:</label>
                        <select name="to_address" required>
                            <option value="">Select Stakeholder</option>
                            ${Object.entries(this.stakeholders).map(([id, name]) =>
                                `<option value="${id}">${name}</option>`
                            ).join('')}
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Transfer Price ($):</label>
                        <input type="number" name="price" min="0" step="0.01" required>
                    </div>

                    <div class="form-group">
                        <label>Quality Update:</label>
                        <textarea name="quality_update" placeholder="Describe the product condition during transfer..." rows="3"></textarea>
                    </div>

                    <div class="form-actions">
                        <button type="submit" class="btn-primary">
                            <i class="fas fa-exchange-alt"></i> Transfer Ownership
                        </button>
                        <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        `;

        modal.querySelector('#transfer-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleTransfer(e.target);
        });

        return modal;
    }

    createQualityCheckModal(product) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close">&times;</span>
                <h3><i class="fas fa-clipboard-check"></i> Quality Check: ${this.escapeHtml(product.name)}</h3>
                <form id="quality-check-form" class="modal-form">
                    <input type="hidden" name="product_id" value="${product.id}">

                    <div class="form-group">
                        <label>Checked By:</label>
                        <select name="checked_by" required>
                            <option value="">Select Stakeholder</option>
                            ${Object.entries(this.stakeholders).map(([id, name]) =>
                                `<option value="${id}">${name}</option>`
                            ).join('')}
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Temperature (°C):</label>
                        <input type="number" name="temperature" step="0.1" placeholder="Optional">
                    </div>

                    <div class="form-group">
                        <label>Quality Notes:</label>
                        <textarea name="quality_note" placeholder="Describe the product quality condition..." rows="4" required></textarea>
                    </div>

                    <div class="form-actions">
                        <button type="submit" class="btn-primary">
                            <i class="fas fa-clipboard-check"></i> Add Quality Check
                        </button>
                        <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        `;

        modal.querySelector('#quality-check-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleQualityCheck(e.target);
        });

        return modal;
    }

    async handleTransfer(form) {
        const formData = new FormData(form);
        const data = {
            from_address: formData.get('from_address'),
            to_address: formData.get('to_address'),
            price: parseFloat(formData.get('price')),
            quality_update: formData.get('quality_update')
        };

        const productId = formData.get('product_id');

        try {
            const response = await fetch(`${this.apiBase}/products/${productId}/transfer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('Ownership transferred successfully!');
                form.closest('.modal').remove();
                this.loadProducts();
                this.loadDashboard();
            } else {
                this.showError('Transfer failed: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            this.showError('Error transferring ownership');
            console.error('Error:', error);
        }
    }

    async handleQualityCheck(form) {
        const formData = new FormData(form);
        const data = {
            checked_by: formData.get('checked_by'),
            quality_note: formData.get('quality_note'),
            temperature: formData.get('temperature') ? parseFloat(formData.get('temperature')) : null
        };

        const productId = formData.get('product_id');

        try {
            const response = await fetch(`${this.apiBase}/products/${productId}/quality-check`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess('Quality check added successfully!');
                form.closest('.modal').remove();
                this.loadProducts();
                this.loadDashboard();
            } else {
                this.showError('Quality check failed: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            this.showError('Error adding quality check');
            console.error('Error:', error);
        }
    }

    showModal(modal) {
        modal.style.display = 'block';

        // Close modal when clicking X
        modal.querySelector('.close').addEventListener('click', () => {
            modal.remove();
        });

        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    setupEventListeners() {
        // Register form
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.registerProduct();
            });
        }

        // Product search
        const searchInput = document.getElementById('product-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchProducts(e.target.value);
            });
        }

        // Enter key for track input
        const trackInput = document.getElementById('track-product-id');
        if (trackInput) {
            trackInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.trackProduct();
                }
            });
        }

        // QR Scanner button
        const qrScanBtn = document.querySelector('.qr-section .btn-secondary');
        if (qrScanBtn) {
            qrScanBtn.addEventListener('click', () => {
                this.startQRScanner();
            });
        }
    }

    async registerProduct() {
        const formData = {
            name: document.getElementById('product-name').value,
            origin: document.getElementById('farm-location').value,
            harvest_date: document.getElementById('harvest-date').value,
            quality: document.getElementById('initial-quality').value,
            farmer_id: 'farmer_001'
        };

        // Validate form
        for (const [key, value] of Object.entries(formData)) {
            if (!value) {
                this.showError(`Please fill in the ${key.replace('_', ' ')} field`);
                return;
            }
        }

        try {
            const response = await fetch(`${this.apiBase}/products/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (response.ok) {
                this.showSuccess(`Product registered successfully! ID: ${result.product_id}`);
                document.getElementById('register-form').reset();
                this.setupRegisterSection();
                this.loadDashboard();
                this.loadProducts();
            } else {
                this.showError('Error registering product: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error registering product:', error);
            this.showError('Error registering product. Please try again.');
        }
    }

    searchProducts(query) {
        const productCards = document.querySelectorAll('.product-card');
        const searchTerm = query.toLowerCase();

        productCards.forEach(card => {
            const productName = card.querySelector('h3').textContent.toLowerCase();
            const productId = card.querySelector('.product-id').textContent.toLowerCase();
            const productOrigin = card.querySelector('.product-info p:nth-child(1) span:last-child')?.textContent.toLowerCase() || '';

            const matches = productName.includes(searchTerm) ||
                           productId.includes(searchTerm) ||
                           productOrigin.includes(searchTerm);

            card.style.display = matches ? 'block' : 'none';
        });
    }

    async loadAnalytics() {
        try {
            const response = await fetch(`${this.apiBase}/stats`);
            const stats = await response.json();
            this.displayAnalytics(stats);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    displayAnalytics(stats) {
        const analyticsSection = document.getElementById('analytics');
        if (!analyticsSection) return;

        analyticsSection.innerHTML = `
            <div class="analytics-container">
                <h2>Supply Chain Analytics</h2>
                <div class="analytics-grid">
                    <div class="analytics-card large">
                        <h3>System Overview</h3>
                        <div class="stats-list">
                            <div class="stat-item">
                                <span class="stat-label">Total Products:</span>
                                <span class="stat-value">${stats.total_products}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Total Transactions:</span>
                                <span class="stat-value">${stats.total_transactions}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Quality Checks:</span>
                                <span class="stat-value">${stats.total_quality_checks}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Average Price Increase:</span>
                                <span class="stat-value">${stats.avg_price_increase}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="analytics-card">
                        <h3>Recent Activity</h3>
                        <div class="activity-feed">
                            ${stats.recent_activity.slice(-5).map(activity => `
                                <div class="activity-item">
                                    <div class="activity-icon small">
                                        <i class="fas fa-${this.getActivityIcon(activity.type)}"></i>
                                    </div>
                                    <div class="activity-content">
                                        <p>${this.formatActivityMessage(activity)}</p>
                                        <span class="activity-time">${new Date(activity.timestamp).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getActivityIcon(type) {
        switch(type) {
            case 'REGISTER': return 'seedling';
            case 'TRANSFER': return 'exchange-alt';
            case 'QUALITY_CHECK': return 'clipboard-check';
            default: return 'info-circle';
        }
    }

    formatActivityMessage(activity) {
        switch(activity.type) {
            case 'REGISTER':
                return `New ${activity.productName} registered`;
            case 'TRANSFER':
                return `${activity.productName} transferred`;
            case 'QUALITY_CHECK':
                return `Quality check: ${activity.productName}`;
            default:
                return 'Activity recorded';
        }
    }

    showProductDetails(productId) {
        this.trackProduct(productId);
    }

    // Utility methods
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.app = new FarmTrackApp();
});

// Global functions for HTML onclick attributes
function trackProduct() {
    if (window.app) {
        window.app.trackProduct();
    }
}

function startQRScanner() {
    if (window.app) {
        window.app.startQRScanner();
    } else {
        alert('QR Scanner would open here. This feature requires camera access.');
    }
}

function verifyProduct(productId) {
    if (window.app) {
        window.app.verifyProduct(productId);
    }
}

function transferProduct(productId) {
    if (window.app) {
        window.app.transferProduct(productId);
    }
}

function addQualityCheck(productId) {
    if (window.app) {
        window.app.addQualityCheck(productId);
    }
}

// QR Code related global functions
function generateAndDisplayQR(productId) {
    if (window.app) {
        window.app.generateAndDisplayQR(productId);
    }
}

function downloadQR() {
    if (window.app) {
        window.app.downloadQR();
    }
}

function printQR() {
    if (window.app) {
        window.app.printQR();
    }
}

function closeQRModal() {
    if (window.app) {
        window.app.closeQRModal();
    }
}