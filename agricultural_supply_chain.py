import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid


@dataclass
class Transaction:
    from_address: str
    to_address: str
    price: float
    timestamp: str
    quality_update: str
    action: str


@dataclass
class Product:
    product_id: str
    product_name: str
    farm_location: str
    harvest_date: str
    current_owner: str
    quality_history: List[Dict[str, str]]
    price_history: List[Dict[str, Any]]
    transaction_history: List[Dict[str, Any]]


class SimulatedBlockchain:
    """A complete simulated blockchain for agricultural supply chain tracking"""

    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.transactions: List[Dict] = []
        self.next_id = 1
        self.stakeholders = {
            "farmer_001": "Organic Farms Co.",
            "distributor_002": "Fresh Distributors Ltd.",
            "retailer_003": "Green Grocers Market",
            "consumer_004": "End Consumer",
            "processor_005": "Quality Processors Inc."
        }

    def generate_product_id(self):
        product_id = f"PROD_{self.next_id:06d}"
        self.next_id += 1
        return product_id

    def register_product(self, product_name: str, farm_location: str,
                         harvest_date: str, initial_quality: str, farmer_id: str) -> str:
        """Farmer registers a new product batch"""
        product_id = self.generate_product_id()

        current_time = datetime.now().isoformat()

        product = Product(
            product_id=product_id,
            product_name=product_name,
            farm_location=farm_location,
            harvest_date=harvest_date,
            current_owner=farmer_id,
            quality_history=[{'quality': initial_quality, 'timestamp': current_time, 'checked_by': farmer_id}],
            price_history=[{'price': 0, 'timestamp': current_time, 'stage': 'Registration'}],
            transaction_history=[{
                'from_address': '0x0',
                'to_address': farmer_id,
                'price': 0,
                'timestamp': current_time,
                'quality_update': initial_quality,
                'action': 'REGISTERED'
            }]
        )

        self.products[product_id] = product

        self.transactions.append({
            'type': 'REGISTER',
            'productId': product_id,
            'productName': product_name,
            'timestamp': current_time,
            'by': farmer_id,
            'by_name': self.stakeholders.get(farmer_id, farmer_id)
        })

        print(f"✅ Product registered: {product_name} ({product_id}) by {self.stakeholders.get(farmer_id, farmer_id)}")
        return product_id

    def transfer_ownership(self, product_id: str, from_address: str,
                           to_address: str, price: float, quality_update: str = None) -> bool:
        """Transfer product ownership to next stakeholder"""
        if product_id not in self.products:
            print(f"❌ Product {product_id} not found")
            return False

        product = self.products[product_id]

        if product.current_owner != from_address:
            print(f"❌ Current owner is {product.current_owner}, not {from_address}")
            return False

        current_time = datetime.now().isoformat()

        # Update ownership
        previous_owner = product.current_owner
        product.current_owner = to_address

        # Add quality update if provided
        quality_update_text = quality_update or "Quality maintained during transfer"
        product.quality_history.append({
            'quality': quality_update_text,
            'timestamp': current_time,
            'checked_by': to_address
        })

        # Add price update
        product.price_history.append({
            'price': price,
            'timestamp': current_time,
            'stage': f"Transfer to {self.stakeholders.get(to_address, to_address)}"
        })

        # Add transaction record
        transaction_record = {
            'from_address': from_address,
            'to_address': to_address,
            'price': price,
            'timestamp': current_time,
            'quality_update': quality_update_text,
            'action': 'TRANSFER'
        }

        product.transaction_history.append(transaction_record)

        self.transactions.append({
            'type': 'TRANSFER',
            'productId': product_id,
            'productName': product.product_name,
            'from': from_address,
            'from_name': self.stakeholders.get(from_address, from_address),
            'to': to_address,
            'to_name': self.stakeholders.get(to_address, to_address),
            'price': price,
            'timestamp': current_time
        })

        from_name = self.stakeholders.get(from_address, from_address)
        to_name = self.stakeholders.get(to_address, to_address)
        print(f"✅ Ownership transferred: {product_id} from {from_name} to {to_name} for ${price}")
        return True

    def add_quality_check(self, product_id: str, checked_by: str, quality_note: str, temperature: float = None):
        """Add a quality check without transferring ownership"""
        if product_id not in self.products:
            return False

        product = self.products[product_id]
        current_time = datetime.now().isoformat()

        quality_data = {
            'quality': quality_note,
            'timestamp': current_time,
            'checked_by': checked_by
        }

        if temperature is not None:
            quality_data['temperature'] = f"{temperature}°C"

        product.quality_history.append(quality_data)

        # Also add a transaction record for the quality check
        transaction_record = {
            'from_address': product.current_owner,
            'to_address': product.current_owner,  # Same owner for quality check
            'price': 0,
            'timestamp': current_time,
            'quality_update': quality_note,
            'action': 'QUALITY_CHECK'
        }

        product.transaction_history.append(transaction_record)

        self.transactions.append({
            'type': 'QUALITY_CHECK',
            'productId': product_id,
            'productName': product.product_name,
            'by': checked_by,
            'by_name': self.stakeholders.get(checked_by, checked_by),
            'quality_note': quality_note,
            'timestamp': current_time
        })

        print(f"✅ Quality check added for {product_id} by {self.stakeholders.get(checked_by, checked_by)}")
        return True

    def get_product_history(self, product_id: str) -> Optional[Product]:
        """Retrieve complete history of a product"""
        if product_id not in self.products:
            print(f"❌ Product {product_id} not found")
            return None

        return self.products[product_id]

    def verify_product(self, product_id: str) -> bool:
        """Verify product origin and authenticity"""
        exists = product_id in self.products
        print(f"🔍 Product verification: {product_id} - {'Authentic' if exists else 'Fake'}")
        return exists

    def get_all_products(self) -> Dict[str, Product]:
        """Get all products in the system"""
        return self.products

    def get_stakeholder_products(self, stakeholder_id: str) -> List[Product]:
        """Get all products owned by a specific stakeholder"""
        return [p for p in self.products.values() if p.current_owner == stakeholder_id]

    def get_recent_activity(self, limit: int = 10) -> List[Dict]:
        """Get recent system activity"""
        return self.transactions[-limit:] if self.transactions else []

    def generate_supply_chain_report(self, product_id: str) -> Optional[Dict]:
        """Generate a comprehensive report of the product's journey"""
        product = self.get_product_history(product_id)
        if not product:
            return None

        # Calculate price changes
        initial_price = product.price_history[0]['price']
        final_price = product.price_history[-1]['price']
        price_increase = final_price - initial_price
        price_increase_percent = (price_increase / initial_price * 100) if initial_price > 0 else 0

        # Count transactions by type
        transaction_types = {}
        for tx in product.transaction_history:
            tx_type = tx['action']
            transaction_types[tx_type] = transaction_types.get(tx_type, 0) + 1

        # Get stakeholders involved
        stakeholders_involved = set()
        for tx in product.transaction_history:
            stakeholders_involved.add(tx['from_address'])
            stakeholders_involved.add(tx['to_address'])

        return {
            'product_id': product_id,
            'product_name': product.product_name,
            'origin': product.farm_location,
            'harvest_date': product.harvest_date,
            'current_owner': self.stakeholders.get(product.current_owner, product.current_owner),
            'current_owner_id': product.current_owner,
            'transaction_count': len(product.transaction_history),
            'price_increase': price_increase,
            'price_increase_percent': price_increase_percent,
            'final_price': final_price,
            'transaction_types': transaction_types,
            'quality_checks': len([q for q in product.quality_history if 'checked_by' in q]),
            'stakeholders_involved': len(stakeholders_involved),
            'transactions': product.transaction_history,
            'quality_history': product.quality_history,
            'price_history': product.price_history
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        products = self.get_all_products()

        total_transactions = len(self.transactions)
        total_quality_checks = sum(len(p.quality_history) for p in products.values())

        # Calculate average price increase
        price_increases = []
        for product in products.values():
            if len(product.price_history) > 1:
                initial = product.price_history[0]['price']
                final = product.price_history[-1]['price']
                if initial > 0:
                    increase = ((final - initial) / initial) * 100
                    price_increases.append(increase)

        avg_price_increase = sum(price_increases) / len(price_increases) if price_increases else 0

        return {
            'total_products': len(products),
            'total_transactions': total_transactions,
            'total_quality_checks': total_quality_checks,
            'active_stakeholders': len(self.stakeholders),
            'avg_price_increase': round(avg_price_increase, 1),
            'recent_activity': self.get_recent_activity(10)
        }

    def display_product_journey(self, product_id: str):
        """Display the complete journey of a product in a readable format"""
        product = self.get_product_history(product_id)
        if not product:
            return

        print(f"\n🌱 Journey of {product.product_name} ({product_id})")
        print(f"📍 Origin: {product.farm_location}")
        print(f"📅 Harvested: {product.harvest_date}")
        print(f"👤 Current Owner: {self.stakeholders.get(product.current_owner, product.current_owner)}")
        print("\n🔄 Supply Chain Journey:")

        for i, tx in enumerate(product.transaction_history, 1):
            from_name = self.stakeholders.get(tx['from_address'], tx['from_address'])
            to_name = self.stakeholders.get(tx['to_address'], tx['to_address'])

            print(f"{i}. {tx['action']}: {from_name} → {to_name}")
            if tx['price'] > 0:
                print(f"   💰 Price: ${tx['price']}")
            if tx['quality_update'] and tx['quality_update'] != "No quality update":
                print(f"   ✅ Quality: {tx['quality_update']}")
            print(f"   ⏰ Time: {tx['timestamp']}")
            print()


class AgriculturalSupplyChain:
    def __init__(self, use_real_blockchain=False, provider_url='HTTP://127.0.0.1:7545'):
        self.use_real_blockchain = use_real_blockchain
        self.provider_url = provider_url
        self.blockchain = SimulatedBlockchain()

        if use_real_blockchain:
            self._setup_real_blockchain()
        else:
            print("✅ Agricultural Supply Chain System Initialized")
            print("   Using simulated blockchain (no external connection needed)")

    def _setup_real_blockchain(self):
        """Setup connection to real Ethereum blockchain"""
        try:
            from web3 import Web3

            self.w3 = Web3(Web3.HTTPProvider(self.provider_url))

            if not self.w3.isConnected():
                raise ConnectionError("Failed to connect to blockchain provider")

            # Load contract ABI and address
            try:
                with open('SupplyChain.json', 'r') as f:
                    contract_data = json.load(f)

                contract_abi = contract_data['abi']
                contract_address = contract_data['networks']['5777']['address']

                self.contract = self.w3.eth.contract(
                    address=contract_address,
                    abi=contract_abi
                )

                print("✅ Connected to real Ethereum blockchain")
                print(f"   Network: {self.provider_url}")
                print(f"   Contract: {contract_address}")

            except FileNotFoundError:
                print("❌ Contract file not found. Using simulated blockchain.")
                self.use_real_blockchain = False

        except ImportError:
            print("❌ Web3.py not installed. Using simulated blockchain.")
            self.use_real_blockchain = False
        except Exception as e:
            print(f"❌ Error connecting to blockchain: {e}")
            print("   Using simulated blockchain instead.")
            self.use_real_blockchain = False

    def register_product(self, product_name, farm_location, harvest_date, initial_quality, farmer_id="farmer_001"):
        """Farmer registers a new product batch"""
        return self.blockchain.register_product(
            product_name, farm_location, harvest_date, initial_quality, farmer_id
        )

    def transfer_ownership(self, product_id, from_address, to_address, price, quality_update=None):
        """Transfer product ownership to next stakeholder"""
        return self.blockchain.transfer_ownership(
            product_id, from_address, to_address, price, quality_update
        )

    def add_quality_check(self, product_id, checked_by, quality_note, temperature=None):
        """Add a quality check without transferring ownership"""
        return self.blockchain.add_quality_check(product_id, checked_by, quality_note, temperature)

    def get_product_history(self, product_id):
        """Retrieve complete history of a product"""
        return self.blockchain.get_product_history(product_id)

    def verify_product(self, product_id):
        """Verify product origin and authenticity"""
        return self.blockchain.verify_product(product_id)

    def get_all_products(self):
        """Get all products in the system"""
        return self.blockchain.get_all_products()

    def generate_supply_chain_report(self, product_id):
        """Generate a comprehensive report of the product's journey"""
        return self.blockchain.generate_supply_chain_report(product_id)

    def get_system_stats(self):
        """Get overall system statistics"""
        return self.blockchain.get_system_stats()

    def get_recent_activity(self, limit=10):
        """Get recent system activity"""
        return self.blockchain.get_recent_activity(limit)

    def display_product_journey(self, product_id):
        """Display the complete journey of a product"""
        self.blockchain.display_product_journey(product_id)

    def demo_supply_chain(self):
        """Run a complete demonstration of the supply chain"""
        print("\n" + "=" * 60)
        print("          AGRICULTURAL SUPPLY CHAIN DEMO")
        print("=" * 60)

        # Define stakeholders
        FARMER = "farmer_001"
        DISTRIBUTOR = "distributor_002"
        PROCESSOR = "processor_005"
        RETAILER = "retailer_003"
        CONSUMER = "consumer_004"

        # 1. Farmer registers organic tomatoes
        print("\n1. 🧑‍🌾 FARMER REGISTERS ORGANIC TOMATOES")
        print("-" * 40)
        tomatoes_id = self.register_product(
            product_name="Organic Heirloom Tomatoes",
            farm_location="Sunny Valley Farm, California",
            harvest_date="2024-01-15",
            initial_quality="Grade AA - Premium Quality, Chemical-free",
            farmer_id=FARMER
        )

        # 2. Farmer registers free-range eggs
        print("\n2. 🧑‍🌾 FARMER REGISTERS FREE-RANGE EGGS")
        print("-" * 40)
        eggs_id = self.register_product(
            product_name="Free-range Organic Eggs",
            farm_location="Happy Hen Farm, Oregon",
            harvest_date="2024-01-10",
            initial_quality="Grade A - Fresh, Free-range",
            farmer_id=FARMER
        )

        # 3. Quality check at farm
        print("\n3. ✅ QUALITY CHECK AT FARM")
        print("-" * 40)
        self.add_quality_check(tomatoes_id, FARMER, "Initial quality inspection passed", 22.5)
        self.add_quality_check(eggs_id, FARMER, "Eggs collected and inspected", 18.0)

        # 4. Transfer to distributor
        print("\n4. 🚚 TRANSFER TO DISTRIBUTOR")
        print("-" * 40)
        self.transfer_ownership(tomatoes_id, FARMER, DISTRIBUTOR, 120,
                                "Temperature controlled transport at 15°C")
        self.transfer_ownership(eggs_id, FARMER, DISTRIBUTOR, 80,
                                "Refrigerated transport at 4°C")

        # 5. Quality check at distributor
        print("\n5. ✅ QUALITY CHECK AT DISTRIBUTOR")
        print("-" * 40)
        self.add_quality_check(tomatoes_id, DISTRIBUTOR, "Received in perfect condition", 15.0)
        self.add_quality_check(eggs_id, DISTRIBUTOR, "Eggs intact and properly stored", 5.0)

        # 6. Transfer to processor (for tomatoes)
        print("\n6. 🏭 TOMATOES SENT FOR PROCESSING")
        print("-" * 40)
        self.transfer_ownership(tomatoes_id, DISTRIBUTOR, PROCESSOR, 180,
                                "Sent for organic certification and packaging")

        # 7. Processing quality check
        print("\n7. ✅ PROCESSING QUALITY CHECK")
        print("-" * 40)
        self.add_quality_check(tomatoes_id, PROCESSOR, "Certified organic, packaged for retail", 12.0)

        # 8. Transfer to retailer
        print("\n8. 🏪 TRANSFER TO RETAILER")
        print("-" * 40)
        self.transfer_ownership(tomatoes_id, PROCESSOR, RETAILER, 280,
                                "Premium packaged tomatoes ready for sale")
        self.transfer_ownership(eggs_id, DISTRIBUTOR, RETAILER, 150,
                                "Eggs sorted and ready for retail")

        # 9. Retail quality check
        print("\n9. ✅ RETAIL QUALITY CHECK")
        print("-" * 40)
        self.add_quality_check(tomatoes_id, RETAILER, "Display quality verified", 10.0)
        self.add_quality_check(eggs_id, RETAILER, "Eggs properly refrigerated", 6.0)

        # 10. Sale to consumers
        print("\n10. 🛒 SALE TO CONSUMERS")
        print("-" * 40)
        self.transfer_ownership(tomatoes_id, RETAILER, CONSUMER, 350,
                                "Final quality check passed. Ready for consumption")
        self.transfer_ownership(eggs_id, RETAILER, CONSUMER, 200,
                                "Fresh eggs sold to consumer")

        # Display results
        print("\n11. 📊 DEMO RESULTS SUMMARY")
        print("-" * 40)
        stats = self.get_system_stats()
        print(f"Total Products: {stats['total_products']}")
        print(f"Total Transactions: {stats['total_transactions']}")
        print(f"Quality Checks: {stats['total_quality_checks']}")
        print(f"Average Price Increase: {stats['avg_price_increase']}%")

        # Show tomato journey
        print(f"\n12. 🌱 TOMATO JOURNEY SUMMARY")
        print("-" * 40)
        tomato_report = self.generate_supply_chain_report(tomatoes_id)
        if tomato_report:
            print(f"Product: {tomato_report['product_name']}")
            print(f"Price Journey: ${tomato_report['price_history'][0]['price']} → ${tomato_report['final_price']}")
            print(f"Price Increase: +{tomato_report['price_increase_percent']:.1f}%")
            print(f"Stakeholders Involved: {tomato_report['stakeholders_involved']}")
            print(f"Quality Checks: {tomato_report['quality_checks']}")

        print("\n" + "=" * 60)
        print("           DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)

        return tomatoes_id, eggs_id


# Utility functions for API
def product_to_dict(product):
    """Convert Product object to dictionary for JSON serialization"""
    if not product:
        return None

    return {
        'id': product.product_id,
        'name': product.product_name,
        'origin': product.farm_location,
        'harvest_date': product.harvest_date,
        'current_owner': product.current_owner,
        'current_owner_name': SimulatedBlockchain().stakeholders.get(product.current_owner, product.current_owner),
        'quality_history': product.quality_history,
        'price_history': product.price_history,
        'transaction_history': product.transaction_history
    }


if __name__ == "__main__":
    # Initialize the supply chain system
    supply_chain = AgriculturalSupplyChain()

    # Run the demonstration
    tomato_id, egg_id = supply_chain.demo_supply_chain()

    # Example of checking a specific product
    print(f"\nExample Product ID for testing: {tomato_id}")
    print("You can use this ID in the frontend to track the product journey.")


    # Utility functions for API
    def product_to_dict(product):
        """Convert Product object to dictionary for JSON serialization"""
        if not product:
            return None

        # Get stakeholder names
        blockchain = SimulatedBlockchain()

        # Convert transaction history with proper names
        transaction_history = []
        for tx in product.transaction_history:
            transaction_history.append({
                'from_address': tx.from_address,
                'from_name': blockchain.stakeholders.get(tx.from_address, tx.from_address),
                'to_address': tx.to_address,
                'to_name': blockchain.stakeholders.get(tx.to_address, tx.to_address),
                'price': tx.price,
                'timestamp': tx.timestamp,
                'quality_update': tx.quality_update,
                'action': tx.action
            })

        return {
            'id': product.product_id,
            'name': product.product_name,
            'origin': product.farm_location,
            'harvest_date': product.harvest_date,
            'current_owner': product.current_owner,
            'current_owner_name': blockchain.stakeholders.get(product.current_owner, product.current_owner),
            'quality_history': product.quality_history,
            'price_history': product.price_history,
            'transaction_history': transaction_history
        }