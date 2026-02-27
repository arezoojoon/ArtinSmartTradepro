#!/usr/bin/env python3
"""
Demo Data Seeder for Artin Smart Trade
Creates demo user: vahid@demo.com / password123
With realistic demo data for logistics, CRM, deals, etc.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from passlib.context import CryptContext
import json

# Database connection
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/artin_smart_trade"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_demo_data():
    async with async_session() as db:
        try:
            # 1. Create demo tenant
            tenant_id = uuid.uuid4()
            await db.execute(text(f"""
                INSERT INTO tenants (id, name, created_at) 
                VALUES ('{tenant_id}', 'Demo Company', NOW())
                ON CONFLICT (id) DO NOTHING
            """))
            
            # 2. Create demo user
            user_id = uuid.uuid4()
            hashed_pw = await hash_password("password123")
            await db.execute(text(f"""
                INSERT INTO users (id, email, hashed_password, full_name, tenant_id, role, is_active, created_at)
                VALUES ('{user_id}', 'vahid@demo.com', '{hashed_pw}', 'وحید دانشور', '{tenant_id}', 'admin', TRUE, NOW())
                ON CONFLICT (email) DO NOTHING
            """))
            
            # 3. Create wallet
            wallet_id = uuid.uuid4()
            await db.execute(text(f"""
                INSERT INTO wallets (id, tenant_id, balance, currency, updated_at)
                VALUES ('{wallet_id}', '{tenant_id}', 5000.00, 'USD', NOW())
                ON CONFLICT (id) DO NOTHING
            """))
            
            # 4. Create logistics carriers
            carriers = [
                ("DHL Express", "+1-800-225-5345", "tracking@dhl.com", "https://dhl.com"),
                ("FedEx", "+1-800-463-3339", "tracking@fedex.com", "https://fedex.com"),
                ("Maersk Line", "+45-3363-0000", "tracking@maersk.com", "https://maersk.com"),
                ("Iran Air Cargo", "+98-21-44690000", "cargo@iranair.com", "https://iranair.com"),
            ]
            
            carrier_ids = []
            for name, phone, email, website in carriers:
                carrier_id = uuid.uuid4()
                carrier_ids.append(carrier_id)
                await db.execute(text(f"""
                    INSERT INTO logistics_carriers (id, tenant_id, name, phone, email, website, created_at, updated_at)
                    VALUES ('{carrier_id}', '{tenant_id}', '{name}', '{phone}', '{email}', '{website}', NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """))
            
            # 5. Create demo shipments
            shipments = [
                {
                    "number": "AST-2024-001",
                    "origin": {"city": "Tehran", "country": "Iran", "port": "Bandar Abbas"},
                    "destination": {"city": "Hamburg", "country": "Germany", "port": "Port of Hamburg"},
                    "status": "in_transit",
                    "carrier_id": carrier_ids[0],
                    "goods": "Electronics Components",
                    "weight": 1250.5,
                    "packages": 8,
                    "eta": (datetime.now() + timedelta(days=12)).date()
                },
                {
                    "number": "AST-2024-002", 
                    "origin": {"city": "Shanghai", "country": "China", "port": "Shanghai Port"},
                    "destination": {"city": "Dubai", "country": "UAE", "port": "Jebel Ali"},
                    "status": "delivered",
                    "carrier_id": carrier_ids[1],
                    "goods": "Textile Products",
                    "weight": 890.0,
                    "packages": 12,
                    "eta": (datetime.now() - timedelta(days=3)).date()
                },
                {
                    "number": "AST-2024-003",
                    "origin": {"city": "Istanbul", "country": "Turkey", "port": "Ambarli"},
                    "destination": {"city": "Tehran", "country": "Iran", "port": "Bandar Abbas"},
                    "status": "customs",
                    "carrier_id": carrier_ids[2],
                    "goods": "Machinery Parts",
                    "weight": 2100.0,
                    "packages": 15,
                    "eta": (datetime.now() + timedelta(days=5)).date()
                }
            ]
            
            shipment_ids = []
            for shipment in shipments:
                shipment_id = uuid.uuid4()
                shipment_ids.append(shipment_id)
                await db.execute(text(f"""
                    INSERT INTO logistics_shipments 
                    (id, tenant_id, shipment_number, origin, destination, status, carrier_id, 
                     goods_description, total_weight_kg, total_packages, estimated_delivery, created_at, updated_at)
                    VALUES ('{shipment_id}', '{tenant_id}', '{shipment["number"]}', 
                           '{json.dumps(shipment["origin"])}', '{json.dumps(shipment["destination"])}',
                           '{shipment["status"]}', '{shipment["carrier_id"]}', '{shipment["goods"]}',
                           {shipment["weight"]}, {shipment["packages"]}, '{shipment["eta"]}', NOW(), NOW())
                    ON CONFLICT (id) DO NOTHING
                """))
                
                # 6. Create packages for each shipment
                for i in range(shipment["packages"]):
                    package_id = uuid.uuid4()
                    weight = shipment["weight"] / shipment["packages"]
                    await db.execute(text(f"""
                        INSERT INTO logistics_packages 
                        (id, shipment_id, barcode, weight_kg, dimensions, status, created_at)
                        VALUES ('{package_id}', '{shipment_id}', 'PKG-{shipment["number"]}-{i+1:03d}',
                               {weight:.2f}, '120x80x60 cm', 'packed', NOW())
                        ON CONFLICT (id) DO NOTHING
                    """))
                
                # 7. Create shipment events/timeline
                events = []
                if shipment["status"] == "in_transit":
                    events = [
                        ("created", "system", {"location": "Origin"}, "Shipment created"),
                        ("picked_up", "carrier", {"location": shipment["origin"]["city"]}, "Package picked up"),
                        ("in_transit", "carrier", {"location": "Transit Hub"}, "In transit to destination"),
                    ]
                elif shipment["status"] == "delivered":
                    events = [
                        ("created", "system", {"location": "Origin"}, "Shipment created"),
                        ("picked_up", "carrier", {"location": shipment["origin"]["city"]}, "Package picked up"),
                        ("in_transit", "carrier", {"location": "Transit Hub"}, "In transit"),
                        ("customs_cleared", "customs", {"location": shipment["destination"]["city"]}, "Customs cleared"),
                        ("delivered", "carrier", {"location": shipment["destination"]["city"]}, "Delivered successfully"),
                    ]
                elif shipment["status"] == "customs":
                    events = [
                        ("created", "system", {"location": "Origin"}, "Shipment created"),
                        ("picked_up", "carrier", {"location": shipment["origin"]["city"]}, "Package picked up"),
                        ("in_transit", "carrier", {"location": "Transit Hub"}, "In transit"),
                        ("at_customs", "customs", {"location": shipment["destination"]["city"]}, "Awaiting customs clearance"),
                    ]
                
                for event_type, actor, payload, notes in events:
                    event_id = uuid.uuid4()
                    event_time = datetime.now() - timedelta(hours=len(events))
                    await db.execute(text(f"""
                        INSERT INTO logistics_events 
                        (id, shipment_id, event_type, actor, payload, notes, timestamp)
                        VALUES ('{event_id}', '{shipment_id}', '{event_type}', '{actor}',
                               '{json.dumps(payload)}', '{notes}', '{event_time}')
                        ON CONFLICT (id) DO NOTHING
                    """))
            
            # 8. Create CRM companies
            companies = [
                ("Siemens AG", "Germany", "Electronics", "contact@siemens.com"),
                ("Alibaba Group", "China", "E-commerce", "business@alibaba.com"),
                ("Dubai Trading Co", "UAE", "Trading", "info@dubaitrading.ae"),
            ]
            
            company_ids = []
            for name, country, industry, email in companies:
                company_id = uuid.uuid4()
                company_ids.append(company_id)
                await db.execute(text(f"""
                    INSERT INTO companies (id, tenant_id, name, country, industry, email, created_at)
                    VALUES ('{company_id}', '{tenant_id}', '{name}', '{country}', '{industry}', '{email}', NOW())
                    ON CONFLICT (id) DO NOTHING
                """))
            
            # 9. Create CRM contacts
            contacts = [
                ("Hans Mueller", "CEO", company_ids[0], "hans.mueller@siemens.com"),
                ("Li Wei", "Procurement Manager", company_ids[1], "li.wei@alibaba.com"),
                ("Ahmed Hassan", "Sales Director", company_ids[2], "ahmed.hassan@dubaitrading.ae"),
            ]
            
            contact_ids = []
            for name, position, company_id, email in contacts:
                contact_id = uuid.uuid4()
                contact_ids.append(contact_id)
                await db.execute(text(f"""
                    INSERT INTO contacts (id, tenant_id, name, position, company_id, email, created_at)
                    VALUES ('{contact_id}', '{tenant_id}', '{name}', '{position}', '{company_id}', '{email}', NOW())
                    ON CONFLICT (id) DO NOTHING
                """))
            
            # 10. Create deals
            deals = [
                ("Electronics Supply Deal", company_ids[0], 125000, "in_progress", "Supply of industrial electronics"),
                ("Textile Import Deal", company_ids[1], 85000, "negotiation", "Import of textile products"),
                ("Machinery Parts Deal", company_ids[2], 210000, "closed_won", "Machinery parts supply contract"),
            ]
            
            for title, company_id, value, stage, description in deals:
                deal_id = uuid.uuid4()
                await db.execute(text(f"""
                    INSERT INTO deals (id, tenant_id, title, company_id, value, stage, description, created_at)
                    VALUES ('{deal_id}', '{tenant_id}', '{title}', '{company_id}', {value}, '{stage}', '{description}', NOW())
                    ON CONFLICT (id) DO NOTHING
                """))
            
            await db.commit()
            print("✅ Demo data created successfully!")
            print("📧 Login: vahid@demo.com")
            print("🔑 Password: password123")
            print(f"🏢 Tenant: Demo Company (ID: {tenant_id})")
            print(f"📦 Created {len(shipments)} shipments")
            print(f"🏭 Created {len(companies)} companies")
            print(f"👥 Created {len(contacts)} contacts")
            print(f"💼 Created {len(deals)} deals")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error creating demo data: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(create_demo_data())
