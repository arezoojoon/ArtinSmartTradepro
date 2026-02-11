/// <reference types="cypress" />

/**
 * Cypress E2E Tests — Artin Smart Trade Frontend
 * Tests: login, registration, sidebar navigation, dead buttons, wallet.
 */

const BASE_URL = 'http://localhost:3000';
const API_URL = 'http://localhost:8000/api/v1';

describe('Authentication Flow', () => {
    it('shows login page', () => {
        cy.visit(`${BASE_URL}/login`);
        cy.get('input[type="email"], input[name="email"]').should('exist');
        cy.get('input[type="password"]').should('exist');
        cy.contains('button', /sign in|log in|login/i).should('exist');
    });

    it('shows registration page', () => {
        cy.visit(`${BASE_URL}/register`);
        cy.get('input[name="email"]').should('exist');
        cy.get('input[type="password"]').should('exist');
        cy.get('input[name="company_name"], input[name="companyName"]').should('exist');
    });

    it('rejects invalid login', () => {
        cy.visit(`${BASE_URL}/login`);
        cy.get('input[type="email"], input[name="email"]').type('fake@test.com');
        cy.get('input[type="password"]').type('wrong');
        cy.contains('button', /sign in|log in|login/i).click();
        // Should show error
        cy.contains(/invalid|error|failed/i, { timeout: 5000 }).should('exist');
    });
});

describe('Sidebar Navigation', () => {
    beforeEach(() => {
        // Login first
        cy.visit(`${BASE_URL}/login`);
        cy.get('input[type="email"], input[name="email"]').type('admin@artin.com');
        cy.get('input[type="password"]').type('admin123');
        cy.contains('button', /sign in|log in|login/i).click();
        cy.url({ timeout: 10000 }).should('include', '/dashboard');
    });

    const sidebarLinks = [
        { label: 'Dashboard', href: '/dashboard' },
        { label: 'CRM', href: '/crm' },
        { label: 'Companies', href: '/crm/companies' },
        { label: 'Campaigns', href: '/crm/campaigns' },
        { label: 'Follow-Ups', href: '/crm/followups' },
        { label: 'Voice Intelligence', href: '/crm/voice' },
        { label: 'Vision Intelligence', href: '/crm/vision' },
        { label: 'Hunter', href: '/hunter' },
        { label: 'Trade Intelligence', href: '/trade' },
        { label: 'AI Brain', href: '/brain' },
        { label: 'Wallet', href: '/wallet' },
    ];

    sidebarLinks.forEach(({ label, href }) => {
        it(`navigates to ${label} (${href}) without crash`, () => {
            cy.get(`a[href="${href}"]`).click();
            cy.url().should('include', href);
            // Should not show unhandled error page
            cy.contains(/application error|unhandled/i).should('not.exist');
        });
    });
});

describe('Dead Button Detection', () => {
    beforeEach(() => {
        cy.visit(`${BASE_URL}/login`);
        cy.get('input[type="email"], input[name="email"]').type('admin@artin.com');
        cy.get('input[type="password"]').type('admin123');
        cy.contains('button', /sign in|log in|login/i).click();
        cy.url({ timeout: 10000 }).should('include', '/dashboard');
    });

    it('Dashboard "Top Up Wallet" button navigates to /wallet', () => {
        cy.visit(`${BASE_URL}/dashboard`);
        cy.contains('Top Up Wallet').click();
        cy.url().should('include', '/wallet');
    });

    it('Wallet "Add Funds" button shows feedback', () => {
        cy.visit(`${BASE_URL}/wallet`);
        cy.contains('button', /add funds/i).click();
        // Should show alert or redirect — not silently fail
        cy.on('window:alert', (text) => {
            expect(text).to.include('Stripe');
        });
    });

    it('Dashboard empty state "Launch Lead Hunter" navigates', () => {
        cy.visit(`${BASE_URL}/dashboard`);
        // Only visible when totalLeads === 0
        cy.get('body').then(($body) => {
            if ($body.text().includes('Launch Lead Hunter')) {
                cy.contains('Launch Lead Hunter').click();
                cy.url().should('include', '/hunter');
            }
        });
    });
});

describe('Empty Pages Check', () => {
    beforeEach(() => {
        cy.visit(`${BASE_URL}/login`);
        cy.get('input[type="email"], input[name="email"]').type('admin@artin.com');
        cy.get('input[type="password"]').type('admin123');
        cy.contains('button', /sign in|log in|login/i).click();
        cy.url({ timeout: 10000 }).should('include', '/dashboard');
    });

    it('CRM contacts page has content', () => {
        cy.visit(`${BASE_URL}/crm/contacts`);
        // Should not be a blank page
        cy.get('body').invoke('text').then((text) => {
            expect(text.trim().length).to.be.greaterThan(10);
        });
    });

    it('Campaigns page has content', () => {
        cy.visit(`${BASE_URL}/crm/campaigns`);
        cy.get('body').invoke('text').then((text) => {
            expect(text.trim().length).to.be.greaterThan(10);
        });
    });
});

describe('API Integration Checks', () => {
    it('Health endpoint returns OK', () => {
        cy.request(`${API_URL.replace('/api/v1', '')}/health`).then((resp) => {
            expect(resp.status).to.equal(200);
            expect(resp.body.version).to.equal('2.0.0');
        });
    });

    it('/billing/wallet endpoint exists', () => {
        cy.request({
            url: `${API_URL}/billing/wallet`,
            failOnStatusCode: false,
            headers: { Authorization: 'Bearer fake' },
        }).then((resp) => {
            // Should NOT be 404 (Method Not Allowed)
            // Currently WILL be 404 — this is a detected bug
            expect(resp.status).to.not.equal(404);
        });
    });
});
