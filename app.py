from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from agricultural_supply_chain import AgriculturalSupplyChain, product_to_dict
import json
import io
import qrcode
from datetime import datetime

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

        qr_data = f"""
Product: {product.product_name}
ID: {product_id}
Origin: {product.farm_location}
Harvest: {product.harvest_date}
Current Owner: {supply_chain.blockchain.stakeholders.get(product.current_owner, product.current_owner)}
Verify: http://localhost:5000/api/products/{product_id}/verify
        """.strip()

        qr = qrcode.make(qr_data)
        img_io = io.BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)

        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
    print("Starting Agricultural Supply Chain Server...")
    print("Demo products available:")
    products = supply_chain.get_all_products()
    for product_id, product in products.items():
        print(f"  - {product.product_name} ({product_id})")

    print("\nAccess the application at: http://localhost:5000")
    app.run(debug=True, port=5000)