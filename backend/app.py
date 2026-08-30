from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from agricultural_supply_chain import AgriculturalSupplyChain, product_to_dict
import json
import io
import qrcode
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Initialize supply chain system
supply_chain = AgriculturalSupplyChain()


# Create demo data
def setup_demo_data():
    """Setup some demo products"""
    try:
        # Create demo products if none exist
        if len(supply_chain.get_all_products()) == 0:
            print("Setting up demo data...")

            # Demo product 1 - Organic Tomatoes
            product_id1 = supply_chain.register_product(
                "Organic Tomatoes",
                "Sunny Valley Farm, California",
                "2024-01-15",
                "Grade AA - Premium Quality",
                "farmer_001"
            )
            supply_chain.transfer_ownership(product_id1, "farmer_001", "distributor_002", 120,
                                            "Temperature controlled transport at 15°C")
            supply_chain.add_quality_check(product_id1, "distributor_002", "Received in perfect condition", 15.0)
            supply_chain.transfer_ownership(product_id1, "distributor_002", "retailer_003", 240,
                                            "Quality inspection passed")
            supply_chain.transfer_ownership(product_id1, "retailer_003", "consumer_004", 320,
                                            "Final quality check passed")

            # Demo product 2 - Free-range Eggs
            product_id2 = supply_chain.register_product(
                "Free-range Eggs",
                "Happy Hen Farm, Oregon",
                "2024-01-10",
                "Grade A - Fresh",
                "farmer_001"
            )
            supply_chain.transfer_ownership(product_id2, "farmer_001", "distributor_002", 80,
                                            "Refrigerated transport at 4°C")
            supply_chain.add_quality_check(product_id2, "distributor_002", "Eggs intact and properly stored", 5.0)
            supply_chain.transfer_ownership(product_id2, "distributor_002", "retailer_003", 150,
                                            "Sorted and ready for retail")

            # Demo product 3 - Organic Apples
            product_id3 = supply_chain.register_product(
                "Organic Apples",
                "Green Mountain Orchard, Washington",
                "2024-01-12",
                "Grade A - Crisp and Fresh",
                "farmer_001"
            )
            supply_chain.transfer_ownership(product_id3, "farmer_001", "distributor_002", 90,
                                            "Cold chain maintained")

            print("Demo data setup complete")
    except Exception as e:
        print(f"Demo setup error: {e}")


# Setup demo data when app starts
setup_demo_data()


@app.route('/')
def serve_frontend():
    return send_file('../frontend/index.html')


@app.route('/<path:path>')
def serve_static_files(path):
    try:
        return send_file(f'../frontend/{path}')
    except:
        return jsonify({'error': 'File not found'}), 404


# API Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    try:
        products = supply_chain.get_all_products()
        products_list = []

        for product_id, product in products.items():
            products_list.append({
                'id': product_id,
                'name': product.product_name,
                'origin': product.farm_location,
                'current_owner': supply_chain.blockchain.stakeholders.get(
                    product.current_owner, product.current_owner
                ),
                'current_owner_id': product.current_owner,
                'harvest_date': product.harvest_date,
                'transaction_count': len(product.transaction_history)
            })

        return jsonify(products_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product details"""
    try:
        product = supply_chain.get_product_history(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        product_dict = product_to_dict(product)
        return jsonify(product_dict)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/register', methods=['POST'])
def register_product():
    """Register a new product"""
    try:
        data = request.json

        # Validate required fields
        required_fields = ['name', 'origin', 'harvest_date', 'quality']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        product_id = supply_chain.register_product(
            data['name'],
            data['origin'],
            data['harvest_date'],
            data['quality'],
            data.get('farmer_id', 'farmer_001')
        )

        return jsonify({
            'product_id': product_id,
            'message': 'Product registered successfully',
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<product_id>/transfer', methods=['POST'])
def transfer_product(product_id):
    """Transfer product ownership"""
    try:
        data = request.json

        required_fields = ['from_address', 'to_address', 'price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        success = supply_chain.transfer_ownership(
            product_id,
            data['from_address'],
            data['to_address'],
            float(data['price']),
            data.get('quality_update', '')
        )

        if success:
            return jsonify({
                'message': 'Ownership transferred successfully',
                'success': True
            })
        else:
            return jsonify({'error': 'Transfer failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<product_id>/quality-check', methods=['POST'])
def add_quality_check(product_id):
    """Add a quality check"""
    try:
        data = request.json

        required_fields = ['checked_by', 'quality_note']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        success = supply_chain.add_quality_check(
            product_id,
            data['checked_by'],
            data['quality_note'],
            data.get('temperature')
        )

        if success:
            return jsonify({
                'message': 'Quality check added successfully',
                'success': True
            })
        else:
            return jsonify({'error': 'Quality check failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<product_id>/verify', methods=['GET'])
def verify_product(product_id):
    """Verify product authenticity"""
    try:
        is_authentic = supply_chain.verify_product(product_id)
        return jsonify({
            'product_id': product_id,
            'authentic': is_authentic,
            'message': 'Product is authentic' if is_authentic else 'Product not found'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<product_id>/qrcode', methods=['GET'])
def generate_qrcode(product_id):
    """Generate QR code for product"""
    try:
        product = supply_chain.get_product_history(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        # Create comprehensive QR data with verification URL
        qr_data = {
            'product_id': product_id,
            'name': product.product_name,
            'origin': product.farm_location,
            'harvest_date': product.harvest_date,
            'owner': supply_chain.blockchain.stakeholders.get(product.current_owner, product.current_owner),
            'verify_url': f"http://localhost:5000/verify/{product_id}"
        }

        # Convert to JSON string for QR code
        qr_json = json.dumps(qr_data)

        # Alternative: Use just the URL for simpler scanning
        # qr_data = f"http://localhost:5000/verify/{product_id}"

        qr = qrcode.make(qr_json)
        img_io = io.BytesIO()
        qr.save(img_io, 'PNG', quality=95)
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<product_id>/qrcode/download', methods=['GET'])
def download_qrcode(product_id):
    """Download QR code as PNG file"""
    try:
        product = supply_chain.get_product_history(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        qr_data = {
            'product_id': product_id,
            'name': product.product_name,
            'origin': product.farm_location,
            'harvest_date': product.harvest_date,
            'owner': supply_chain.blockchain.stakeholders.get(product.current_owner, product.current_owner),
            'verify_url': f"http://localhost:5000/verify/{product_id}"
        }

        qr_json = json.dumps(qr_data)
        qr = qrcode.make(qr_json)
        img_io = io.BytesIO()
        qr.save(img_io, 'PNG', quality=95)
        img_io.seek(0)

        return send_file(
            img_io,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'product_{product_id}_qr.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/verify/<product_id>')
def verify_page(product_id):
    """Page that displays product info when QR is scanned"""
    product = supply_chain.get_product_history(product_id)
    if not product:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Product Verification - FarmTrack</title>
            <style>
                body { font-family: 'Inter', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }
                .error { color: #e74c3c; padding: 50px; background: #fdf0ed; border-radius: 10px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h1>❌ Product Not Found</h1>
                <p>This product may not exist or has been removed from the system.</p>
                <p><a href="/">Return to Home</a></p>
            </div>
        </body>
        </html>
        """

    # Get transaction history for display
    history_html = ""
    for i, tx in enumerate(product.transaction_history[-5:], 1):
        from_name = supply_chain.blockchain.stakeholders.get(tx.get('from_address', 'Origin'),
                                                             tx.get('from_address', 'Origin'))
        to_name = supply_chain.blockchain.stakeholders.get(tx.get('to_address', 'Current'),
                                                           tx.get('to_address', 'Current'))
        action = tx.get('action', 'Transfer')
        timestamp = tx.get('timestamp', '')
        price = tx.get('price', 0)

        history_html += f"""
        <div class="history-item">
            <div class="history-step">{i}</div>
            <div class="history-content">
                <strong>{action}:</strong> {from_name} → {to_name}
                {f'<br><span class="price">💰 ${price}</span>' if price > 0 else ''}
                <br><small>{timestamp}</small>
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Product Verification - FarmTrack</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Inter', Arial, sans-serif; 
                max-width: 900px; 
                margin: 0 auto; 
                padding: 20px; 
                background: #f8f9fa;
                color: #2d3436;
            }}
            .header {{
                background: linear-gradient(135deg, #00b894, #00a381);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{ font-size: 2em; margin-bottom: 10px; }}
            .product-card {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }}
            .product-name {{ font-size: 1.8em; color: #2d3436; margin-bottom: 15px; }}
            .product-details {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
            .detail-item {{ padding: 10px; background: #f8f9fa; border-radius: 8px; }}
            .detail-item strong {{ display: block; color: #636e72; font-size: 0.9em; margin-bottom: 5px; }}
            .detail-item span {{ font-size: 1.1em; color: #2d3436; }}
            .verified-badge {{
                display: inline-block;
                background: #00b894;
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                font-weight: 600;
                margin-top: 15px;
            }}
            .verified-badge i {{ margin-right: 8px; }}
            .history-section {{
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .history-section h2 {{ margin-bottom: 20px; color: #2d3436; }}
            .history-item {{
                display: flex;
                gap: 20px;
                padding: 15px;
                border-left: 3px solid #00b894;
                margin-bottom: 15px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            .history-step {{
                background: #00b894;
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                flex-shrink: 0;
            }}
            .history-content {{ flex: 1; }}
            .price {{ color: #e17055; font-weight: 600; }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding: 20px;
                color: #636e72;
            }}
            .btn-home {{
                display: inline-block;
                background: #0984e3;
                color: white;
                padding: 10px 25px;
                border-radius: 25px;
                text-decoration: none;
                margin-top: 20px;
            }}
            .btn-home:hover {{ background: #0770c4; }}
            @media (max-width: 600px) {{
                .product-details {{ grid-template-columns: 1fr; }}
                .header h1 {{ font-size: 1.5em; }}
                .product-name {{ font-size: 1.4em; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 FarmTrack Verification</h1>
            <p>Authentic product verified on blockchain</p>
        </div>

        <div class="product-card">
            <h2 class="product-name">{product.product_name}</h2>
            <div class="product-details">
                <div class="detail-item">
                    <strong>Product ID</strong>
                    <span>{product_id}</span>
                </div>
                <div class="detail-item">
                    <strong>Origin</strong>
                    <span>{product.farm_location}</span>
                </div>
                <div class="detail-item">
                    <strong>Harvest Date</strong>
                    <span>{product.harvest_date}</span>
                </div>
                <div class="detail-item">
                    <strong>Current Owner</strong>
                    <span>{supply_chain.blockchain.stakeholders.get(product.current_owner, product.current_owner)}</span>
                </div>
            </div>
            <div class="verified-badge">
                <i class="fas fa-check-circle"></i> Verified Authentic
            </div>
        </div>

        <div class="history-section">
            <h2><i class="fas fa-route"></i> Supply Chain Journey</h2>
            {history_html}
            <div style="text-align: center; margin-top: 20px;">
                <p><small>Total transactions: {len(product.transaction_history)}</small></p>
                <a href="/" class="btn-home">Return to Home</a>
            </div>
        </div>

        <div class="footer">
            <p><small>Verified on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
            <p><small>🔒 Blockchain verified · Tamper-proof record</small></p>
        </div>
    </body>
    </html>
    """


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        stats = supply_chain.get_system_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/activity', methods=['GET'])
def get_activity():
    """Get recent activity"""
    try:
        limit = request.args.get('limit', 10, type=int)
        activity = supply_chain.get_recent_activity(limit)
        return jsonify(activity)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stakeholders', methods=['GET'])
def get_stakeholders():
    """Get all stakeholders"""
    try:
        stakeholders = supply_chain.blockchain.stakeholders
        return jsonify(stakeholders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<product_id>/report', methods=['GET'])
def get_product_report(product_id):
    """Get detailed product report"""
    try:
        report = supply_chain.generate_supply_chain_report(product_id)
        if not report:
            return jsonify({'error': 'Product not found'}), 404

        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("          AGRICULTURAL SUPPLY CHAIN SERVER")
    print("=" * 60)
    print("Starting server...")
    print("\nDemo products available:")
    products = supply_chain.get_all_products()
    for product_id, product in products.items():
        print(f"  - {product.product_name} ({product_id})")
        print(f"    QR Code: http://localhost:5000/api/products/{product_id}/qrcode")
        print(f"    Verify: http://localhost:5000/verify/{product_id}")
        print()

    print("\n" + "=" * 60)
    print("Access the application at: http://localhost:5000")
    print("QR Code endpoints available at: /api/products/[ID]/qrcode")
    print("Verification pages at: /verify/[ID]")
    print("=" * 60)
    app.run(debug=True, port=5000)