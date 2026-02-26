-- Demo Data Seeder for Artin Smart Trade
-- Creates demo user: vahid@demo.com / password123
-- With realistic demo data for logistics, CRM, deals, etc.

-- 1. Create demo tenant
INSERT INTO tenants (id, name, created_at) 
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Demo Company', NOW())
ON CONFLICT (id) DO NOTHING;

-- 2. Create demo user (password: password123)
INSERT INTO users (id, email, hashed_password, full_name, tenant_id, role, is_active, created_at)
VALUES ('550e8400-e29b-41d4-a716-446655440001', 'vahid@demo.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6ukx.LFvO6', 'وحید دانشور', '550e8400-e29b-41d4-a716-446655440000', 'admin', TRUE, NOW())
ON CONFLICT (email) DO NOTHING;

-- 3. Create wallet
INSERT INTO wallets (id, tenant_id, balance, currency, updated_at)
VALUES ('550e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440000', 5000.00, 'USD', NOW())
ON CONFLICT (id) DO NOTHING;

-- 4. Create logistics carriers
INSERT INTO logistics_carriers (id, tenant_id, name, phone, email, website, created_at, updated_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440000', 'DHL Express', '+1-800-225-5345', 'tracking@dhl.com', 'https://dhl.com', NOW(), NOW()),
    ('550e8400-e29b-41d4-a716-446655440011', '550e8400-e29b-41d4-a716-446655440000', 'FedEx', '+1-800-463-3339', 'tracking@fedex.com', 'https://fedex.com', NOW(), NOW()),
    ('550e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440000', 'Maersk Line', '+45-3363-0000', 'tracking@maersk.com', 'https://maersk.com', NOW(), NOW()),
    ('550e8400-e29b-41d4-a716-446655440013', '550e8400-e29b-41d4-a716-446655440000', 'Iran Air Cargo', '+98-21-44690000', 'cargo@iranair.com', 'https://iranair.com', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 5. Create demo shipments
INSERT INTO logistics_shipments 
(id, tenant_id, shipment_number, origin, destination, status, carrier_id, 
 goods_description, total_weight_kg, total_packages, estimated_delivery, created_at, updated_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440020', '550e8400-e29b-41d4-a716-446655440000', 'AST-2024-001', 
     '{"city": "Tehran", "country": "Iran", "port": "Bandar Abbas"}', 
     '{"city": "Hamburg", "country": "Germany", "port": "Port of Hamburg"}',
     'in_transit', '550e8400-e29b-41d4-a716-446655440010', 'Electronics Components',
     1250.5, 8, '2024-12-15', NOW(), NOW()),
     
    ('550e8400-e29b-41d4-a716-446655440021', '550e8400-e29b-41d4-a716-446655440000', 'AST-2024-002', 
     '{"city": "Shanghai", "country": "China", "port": "Shanghai Port"}', 
     '{"city": "Dubai", "country": "UAE", "port": "Jebel Ali"}',
     'delivered', '550e8400-e29b-41d4-a716-446655440011', 'Textile Products',
     890.0, 12, '2024-12-01', NOW(), NOW()),
     
    ('550e8400-e29b-41d4-a716-446655440022', '550e8400-e29b-41d4-a716-446655440000', 'AST-2024-003', 
     '{"city": "Istanbul", "country": "Turkey", "port": "Ambarli"}', 
     '{"city": "Tehran", "country": "Iran", "port": "Bandar Abbas"}',
     'customs', '550e8400-e29b-41d4-a716-446655440012', 'Machinery Parts',
     2100.0, 15, '2024-12-08', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- 6. Create packages for each shipment
-- Packages for AST-2024-001 (8 packages)
INSERT INTO logistics_packages (id, shipment_id, barcode, weight_kg, dimensions, status, created_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440030', '550e8400-e29b-41d4-a716-446655440020', 'PKG-AST-2024-001-001', 156.31, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440031', '550e8400-e29b-41d4-a716-446655440020', 'PKG-AST-2024-001-002', 156.31, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440032', '550e8400-e29b-41d4-a716-446655440020', 'PKG-AST-2024-001-003', 156.31, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440033', '550e8400-e29b-41d4-a716-446655440020', 'PKG-AST-2024-001-004', 156.31, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440034', '550e8400-e29b-41d4-a716-446655440020', 'PKG-AST-2024-001-005', 156.31, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440035', '550e8400-e29b-41d4-a716-446655440020', 'PKG-AST-2024-001-006', 156.31, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440036', '550e8400-e29b-41d4-a716-446655440020', 'PKG-AST-2024-001-007', 156.31, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440037', '550e8400-e29b-41d4-a716-446655440020', 'PKG-AST-2024-001-008', 156.32, '120x80x60 cm', 'packed', NOW())
ON CONFLICT (id) DO NOTHING;

-- Packages for AST-2024-002 (12 packages)
INSERT INTO logistics_packages (id, shipment_id, barcode, weight_kg, dimensions, status, created_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440038', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-001', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440039', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-002', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440040', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-003', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440041', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-004', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440042', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-005', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440043', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-006', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440044', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-007', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440045', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-008', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440046', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-009', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440047', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-010', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440048', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-011', 74.17, '120x80x60 cm', 'delivered', NOW()),
    ('550e8400-e29b-41d4-a716-446655440049', '550e8400-e29b-41d4-a716-446655440021', 'PKG-AST-2024-002-012', 74.16, '120x80x60 cm', 'delivered', NOW())
ON CONFLICT (id) DO NOTHING;

-- Packages for AST-2024-003 (15 packages)
INSERT INTO logistics_packages (id, shipment_id, barcode, weight_kg, dimensions, status, created_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440050', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-001', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440051', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-002', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440052', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-003', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440053', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-004', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440054', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-005', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440055', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-006', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440056', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-007', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440057', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-008', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440058', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-009', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440059', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-010', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440060', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-011', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440061', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-012', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440062', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-013', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440063', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-014', 140.00, '120x80x60 cm', 'packed', NOW()),
    ('550e8400-e29b-41d4-a716-446655440064', '550e8400-e29b-41d4-a716-446655440022', 'PKG-AST-2024-003-015', 140.00, '120x80x60 cm', 'packed', NOW())
ON CONFLICT (id) DO NOTHING;

-- 7. Create shipment events/timeline
-- Events for AST-2024-001 (in_transit)
INSERT INTO logistics_events (id, shipment_id, event_type, actor, payload, notes, timestamp)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440070', '550e8400-e29b-41d4-a716-446655440020', 'created', 'system', '{"location": "Origin"}', 'Shipment created', '2024-12-03 08:00:00'),
    ('550e8400-e29b-41d4-a716-446655440071', '550e8400-e29b-41d4-a716-446655440020', 'picked_up', 'carrier', '{"location": "Tehran"}', 'Package picked up', '2024-12-03 10:30:00'),
    ('550e8400-e29b-41d4-a716-446655440072', '550e8400-e29b-41d4-a716-446655440020', 'in_transit', 'carrier', '{"location": "Transit Hub"}', 'In transit to destination', '2024-12-03 14:00:00')
ON CONFLICT (id) DO NOTHING;

-- Events for AST-2024-002 (delivered)
INSERT INTO logistics_events (id, shipment_id, event_type, actor, payload, notes, timestamp)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440073', '550e8400-e29b-41d4-a716-446655440021', 'created', 'system', '{"location": "Origin"}', 'Shipment created', '2024-11-28 09:00:00'),
    ('550e8400-e29b-41d4-a716-446655440074', '550e8400-e29b-41d4-a716-446655440021', 'picked_up', 'carrier', '{"location": "Shanghai"}', 'Package picked up', '2024-11-28 11:00:00'),
    ('550e8400-e29b-41d4-a716-446655440075', '550e8400-e29b-41d4-a716-446655440021', 'in_transit', 'carrier', '{"location": "Transit Hub"}', 'In transit', '2024-11-28 16:00:00'),
    ('550e8400-e29b-41d4-a716-446655440076', '550e8400-e29b-41d4-a716-446655440021', 'customs_cleared', 'customs', '{"location": "Dubai"}', 'Customs cleared', '2024-11-30 10:00:00'),
    ('550e8400-e29b-41d4-a716-446655440077', '550e8400-e29b-41d4-a716-446655440021', 'delivered', 'carrier', '{"location": "Dubai"}', 'Delivered successfully', '2024-12-01 14:30:00')
ON CONFLICT (id) DO NOTHING;

-- Events for AST-2024-003 (customs)
INSERT INTO logistics_events (id, shipment_id, event_type, actor, payload, notes, timestamp)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440078', '550e8400-e29b-41d4-a716-446655440022', 'created', 'system', '{"location": "Origin"}', 'Shipment created', '2024-12-04 07:00:00'),
    ('550e8400-e29b-41d4-a716-446655440079', '550e8400-e29b-41d4-a716-446655440022', 'picked_up', 'carrier', '{"location": "Istanbul"}', 'Package picked up', '2024-12-04 09:00:00'),
    ('550e8400-e29b-41d4-a716-446655440080', '550e8400-e29b-41d4-a716-446655440022', 'in_transit', 'carrier', '{"location": "Transit Hub"}', 'In transit', '2024-12-04 13:00:00'),
    ('550e8400-e29b-41d4-a716-446655440081', '550e8400-e29b-41d4-a716-446655440022', 'at_customs', 'customs', '{"location": "Tehran"}', 'Awaiting customs clearance', '2024-12-05 08:00:00')
ON CONFLICT (id) DO NOTHING;

-- 8. Create CRM companies
INSERT INTO companies (id, tenant_id, name, country, industry, email, created_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440090', '550e8400-e29b-41d4-a716-446655440000', 'Siemens AG', 'Germany', 'Electronics', 'contact@siemens.com', NOW()),
    ('550e8400-e29b-41d4-a716-446655440091', '550e8400-e29b-41d4-a716-446655440000', 'Alibaba Group', 'China', 'E-commerce', 'business@alibaba.com', NOW()),
    ('550e8400-e29b-41d4-a716-446655440092', '550e8400-e29b-41d4-a716-446655440000', 'Dubai Trading Co', 'UAE', 'Trading', 'info@dubaitrading.ae', NOW())
ON CONFLICT (id) DO NOTHING;

-- 9. Create CRM contacts
INSERT INTO contacts (id, tenant_id, name, position, company_id, email, created_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440100', '550e8400-e29b-41d4-a716-446655440000', 'Hans Mueller', 'CEO', '550e8400-e29b-41d4-a716-446655440090', 'hans.mueller@siemens.com', NOW()),
    ('550e8400-e29b-41d4-a716-446655440101', '550e8400-e29b-41d4-a716-446655440000', 'Li Wei', 'Procurement Manager', '550e8400-e29b-41d4-a716-446655440091', 'li.wei@alibaba.com', NOW()),
    ('550e8400-e29b-41d4-a716-446655440102', '550e8400-e29b-41d4-a716-446655440000', 'Ahmed Hassan', 'Sales Director', '550e8400-e29b-41d4-a716-446655440092', 'ahmed.hassan@dubaitrading.ae', NOW())
ON CONFLICT (id) DO NOTHING;

-- 10. Create deals
INSERT INTO deals (id, tenant_id, title, company_id, value, stage, description, created_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440110', '550e8400-e29b-41d4-a716-446655440000', 'Electronics Supply Deal', '550e8400-e29b-41d4-a716-446655440090', 125000, 'in_progress', 'Supply of industrial electronics', NOW()),
    ('550e8400-e29b-41d4-a716-446655440111', '550e8400-e29b-41d4-a716-446655440000', 'Textile Import Deal', '550e8400-e29b-41d4-a716-446655440091', 85000, 'negotiation', 'Import of textile products', NOW()),
    ('550e8400-e29b-41d4-a716-446655440112', '550e8400-e29b-41d4-a716-446655440000', 'Machinery Parts Deal', '550e8400-e29b-41d4-a716-446655440092', 210000, 'closed_won', 'Machinery parts supply contract', NOW())
ON CONFLICT (id) DO NOTHING;

-- 11. Add some wallet transactions for demo
INSERT INTO wallet_transactions (id, wallet_id, amount, type, description, reference_id, created_at)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440120', '550e8400-e29b-41d4-a716-446655440002', 5000.00, 'credit', 'Initial wallet funding', 'INITIAL_FUND', NOW()),
    ('550e8400-e29b-41d4-a716-446655440121', '550e8400-e29b-41d4-a716-446655440002', -250.00, 'debit', 'AI Trade Analysis', 'AI_ANALYSIS_001', NOW()),
    ('550e8400-e29b-41d4-a716-446655440122', '550e8400-e29b-41d4-a716-446655440002', -150.00, 'debit', 'Hunter Job', 'HUNTER_JOB_001', NOW()),
    ('550e8400-e29b-41d4-a716-446655440123', '550e8400-e29b-41d4-a716-446655440002', -100.00, 'debit', 'Voice Intelligence', 'VOICE_INTEL_001', NOW())
ON CONFLICT (id) DO NOTHING;
