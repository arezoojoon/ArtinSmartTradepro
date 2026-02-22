# 🤝 Contributing to Artin Smart Trade

> **Guidelines for contributing to the Artin Smart Trade platform**

## 📋 Table of Contents

- [🌟 Overview](#-overview)
- [🚀 Getting Started](#-getting-started)
- [📋 Development Workflow](#-development-workflow)
- [🔧 Code Standards](#-code-standards)
- [🧪 Testing](#-testing)
- [📝 Documentation](#-documentation)
- [🔄 Pull Request Process](#-pull-request-process)
- [🚨 Issue Reporting](#-issue-reporting)
- [🏷️ Release Process](#-release-process)
- [📞 Getting Help](#-getting-help)

## 🌟 Overview

Thank you for your interest in contributing to Artin Smart Trade! This guide will help you get started with contributing to our B2B trade intelligence platform.

### 🎯 Contribution Areas

We welcome contributions in the following areas:

- **🐛 Bug Fixes**: Fix reported issues
- **✨ New Features**: Implement new functionality
- **📚 Documentation**: Improve documentation
- **🧪 Testing**: Add or improve tests
- **🎨 UI/UX**: Improve user interface and experience
- **⚡ Performance**: Optimize performance
- **🔒 Security**: Improve security measures

## 🚀 Getting Started

### 📋 Prerequisites

- **Python**: 3.9+
- **Node.js**: 18+
- **Docker**: 20.10+
- **Git**: 2.30+
- **PostgreSQL**: 14+
- **Redis**: 6+

### 🛠️ Setup Development Environment

1. **Fork the repository**
```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/artin-smart-trade.git
cd artin-smart-trade
```

2. **Add upstream remote**
```bash
git remote add upstream https://github.com/original-org/artin-smart-trade.git
```

3. **Create virtual environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

4. **Install frontend dependencies**
```bash
cd ../frontend
npm install
```

5. **Set up environment**
```bash
# Backend
cd ../backend
cp .env.example .env
# Edit .env with your configuration

# Frontend
cd ../frontend
cp .env.local.example .env.local
# Edit .env.local with your configuration
```

6. **Start services**
```bash
# Using Docker Compose (recommended)
docker-compose -f docker-compose.dev.yml up -d

# Or manually start services
# Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev
```

7. **Run database migrations**
```bash
cd backend
alembic upgrade head
```

8. **Verify setup**
```bash
# Backend health check
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

## 📋 Development Workflow

### 🌿 Branch Strategy

We use a GitFlow-inspired branching strategy:

- **`main`**: Production-ready code
- **`develop`**: Integration branch for features
- **`feature/*`**: Feature branches
- **`bugfix/*`**: Bug fix branches
- **`hotfix/*`**: Critical fixes for production

### 🔄 Workflow Steps

1. **Create feature branch**
```bash
git checkout develop
git pull upstream develop
git checkout -b feature/amazing-feature
```

2. **Make changes**
- Follow code standards
- Write tests
- Update documentation

3. **Commit changes**
```bash
git add .
git commit -m "feat: add amazing feature"
```

4. **Push branch**
```bash
git push origin feature/amazing-feature
```

5. **Create Pull Request**
- Target `develop` branch
- Fill out PR template
- Request reviews

6. **Address feedback**
- Make requested changes
- Push updates to branch

7. **Merge PR**
- After approval, merge to `develop`
- Delete feature branch

### 🏷️ Commit Message Format

We follow [Conventional Commits](https://conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `security`: Security improvements

#### Examples
```bash
feat(auth): add two-factor authentication
fix(deals): resolve null pointer exception in deal creation
docs(api): update authentication documentation
test(crm): add unit tests for contact service
refactor(database): optimize query performance
```

## 🔧 Code Standards

### 🐍 Python (Backend)

#### Style Guide
- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://isort.readthedocs.io/) for imports
- Use [mypy](https://mypy.readthedocs.io/) for type checking

#### Code Quality
```python
# Good example
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.deal import Deal
from app.schemas.deal import DealCreate, DealResponse


async def create_deal(
    deal_data: DealCreate,
    db: Session,
    current_user_id: UUID
) -> DealResponse:
    """
    Create a new deal in the database.
    
    Args:
        deal_data: Deal creation data
        db: Database session
        current_user_id: Current user ID
        
    Returns:
        Created deal response
        
    Raises:
        HTTPException: If deal creation fails
    """
    try:
        deal = Deal(
            title=deal_data.title,
            total_value=deal_data.total_value,
            created_by=current_user_id
        )
        db.add(deal)
        db.commit()
        db.refresh(deal)
        
        return DealResponse.from_orm(deal)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create deal: {str(e)}"
        )
```

#### Type Hints
- Use type hints for all functions
- Use proper return types
- Use Optional for nullable values

#### Documentation
- Add docstrings to all public functions
- Use Google-style docstrings
- Include type hints in docstrings

### 🟨 TypeScript (Frontend)

#### Style Guide
- Use [ESLint](https://eslint.org/) configuration
- Use [Prettier](https://prettier.io/) for formatting
- Use strict TypeScript mode
- Follow [React](https://react.dev/) best practices

#### Code Quality
```typescript
// Good example
import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Deal } from '@/types/deal';
import { dealService } from '@/services/deal-service';

interface DealCardProps {
  dealId: string;
  onUpdate?: (deal: Deal) => void;
}

export const DealCard: React.FC<DealCardProps> = ({ dealId, onUpdate }) => {
  const [deal, setDeal] = useState<Deal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDeal = async () => {
      try {
        setLoading(true);
        const dealData = await dealService.getDeal(dealId);
        setDeal(dealData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch deal');
      } finally {
        setLoading(false);
      }
    };

    fetchDeal();
  }, [dealId]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error || !deal) {
    return <div>Error: {error}</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{deal.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>Value: ${deal.totalValue.toLocaleString()}</p>
        <p>Status: {deal.status}</p>
      </CardContent>
    </Card>
  );
};
```

#### Component Guidelines
- Use functional components with hooks
- Use proper TypeScript types
- Follow naming conventions
- Add JSDoc comments for complex logic

## 🧪 Testing

### 📋 Testing Strategy

We use a multi-layered testing approach:

- **Unit Tests**: Test individual functions/components
- **Integration Tests**: Test API endpoints and database operations
- **E2E Tests**: Test complete user workflows
- **Performance Tests**: Test system performance

### 🐍 Backend Testing

#### Unit Tests
```python
# tests/test_deal_service.py
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from app.services.deal_service import DealService
from app.schemas.deal import DealCreate
from app.models.deal import Deal


class TestDealService:
    def setup_method(self):
        """Setup test environment"""
        self.deal_service = DealService()
        self.mock_db = Mock()
        self.user_id = uuid4()

    @pytest.fixture
    def sample_deal_data(self):
        """Sample deal data for testing"""
        return DealCreate(
            title="Test Deal",
            total_value=100000,
            currency="USD"
        )

    def test_create_deal_success(self, sample_deal_data):
        """Test successful deal creation"""
        # Arrange
        mock_deal = Deal(
            id=uuid4(),
            title=sample_deal_data.title,
            total_value=sample_deal_data.total_value
        )
        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        self.mock_db.refresh.return_value = None

        # Act
        result = self.deal_service.create_deal(
            sample_deal_data,
            self.mock_db,
            self.user_id
        )

        # Assert
        assert result.title == sample_deal_data.title
        assert result.total_value == sample_deal_data.total_value
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_create_deal_failure(self, sample_deal_data):
        """Test deal creation failure"""
        # Arrange
        self.mock_db.add.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception):
            self.deal_service.create_deal(
                sample_deal_data,
                self.mock_db,
                self.user_id
            )
```

#### Integration Tests
```python
# tests/test_deal_api.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from tests.conftest import TestingSessionLocal


class TestDealAPI:
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    async def auth_headers(self, client):
        """Authentication headers fixture"""
        # Create test user and get token
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_create_deal_api(self, client, auth_headers):
        """Test deal creation API endpoint"""
        # Arrange
        deal_data = {
            "title": "API Test Deal",
            "total_value": 50000,
            "currency": "USD"
        }

        # Act
        response = client.post(
            "/deals",
            json=deal_data,
            headers=auth_headers
        )

        # Assert
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == deal_data["title"]
        assert result["total_value"] == deal_data["total_value"]

    def test_get_deals_api(self, client, auth_headers):
        """Test get deals API endpoint"""
        # Act
        response = client.get("/deals", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        assert isinstance(response.json(), list)
```

### 🟨 Frontend Testing

#### Unit Tests
```typescript
// src/components/__tests__/DealCard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { DealCard } from '../DealCard';
import { dealService } from '@/services/deal-service';

// Mock the deal service
jest.mock('@/services/deal-service');
const mockDealService = dealService as jest.Mocked<typeof dealService>;

describe('DealCard', () => {
  const mockDeal = {
    id: '1',
    title: 'Test Deal',
    totalValue: 100000,
    status: 'active'
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders deal information correctly', async () => {
    // Arrange
    mockDealService.getDeal.mockResolvedValue(mockDeal);

    // Act
    render(<DealCard dealId="1" />);

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Test Deal')).toBeInTheDocument();
      expect(screen.getByText('$100,000')).toBeInTheDocument();
      expect(screen.getByText('active')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    // Arrange
    mockDealService.getDeal.mockImplementation(() => new Promise(() => {}));

    // Act
    render(<DealCard dealId="1" />);

    // Assert
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('shows error state when API fails', async () => {
    // Arrange
    mockDealService.getDeal.mockRejectedValue(new Error('API Error'));

    // Act
    render(<DealCard dealId="1" />);

    // Assert
    await waitFor(() => {
      expect(screen.getByText('Error: API Error')).toBeInTheDocument();
    });
  });
});
```

#### E2E Tests
```typescript
// e2e/deals.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Deals Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[data-testid=email]', 'test@example.com');
    await page.fill('[data-testid=password]', 'testpassword');
    await page.click('[data-testid=login-button]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should create a new deal', async ({ page }) => {
    // Navigate to deals page
    await page.click('[data-testid=deals-nav]');
    await expect(page).toHaveURL('/deals');

    // Click create deal button
    await page.click('[data-testid=create-deal-button]');

    // Fill deal form
    await page.fill('[data-testid=deal-title]', 'E2E Test Deal');
    await page.fill('[data-testid=deal-value]', '75000');
    await page.selectOption('[data-testid=deal-currency]', 'USD');

    // Submit form
    await page.click('[data-testid=submit-button]');

    // Verify deal was created
    await expect(page.locator('[data-testid=deal-title]')).toHaveText('E2E Test Deal');
    await expect(page.locator('[data-testid=deal-value]')).toHaveText('$75,000');
  });

  test('should filter deals by status', async ({ page }) => {
    // Navigate to deals page
    await page.goto('/deals');

    // Filter by status
    await page.selectOption('[data-testid=status-filter]', 'active');

    // Verify filter applied
    const deals = page.locator('[data-testid=deal-card]');
    await expect(deals.first()).toBeVisible();
    
    // Check that all deals have active status
    const dealCards = await deals.all();
    for (const card of dealCards) {
      const status = await card.locator('[data-testid=deal-status]').textContent();
      expect(status).toBe('active');
    }
  });
});
```

### 🧪 Running Tests

#### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_deal_service.py

# Run with verbose output
pytest -v tests/

# Run tests in parallel
pytest -n auto tests/
```

#### Frontend Tests
```bash
# Run unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run specific test file
npm test -- DealCard.test.tsx
```

## 📝 Documentation

### 📚 Documentation Types

- **API Documentation**: OpenAPI/Swagger specs
- **Code Documentation**: Inline comments and docstrings
- **User Documentation**: README files and guides
- **Architecture Documentation**: System design docs

### 📖 Writing Documentation

#### API Documentation
```python
@router.post("/deals", response_model=DealResponse, summary="Create a new deal")
async def create_deal(
    deal_data: DealCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DealResponse:
    """
    Create a new deal in the system.
    
    Args:
        deal_data: Deal creation data including title, value, and currency
        current_user: Authenticated user creating the deal
        db: Database session for persistence
        
    Returns:
        Created deal with assigned ID and timestamps
        
    Raises:
        HTTPException: If user lacks permissions or data is invalid
        
    Example:
        >>> deal_data = DealCreate(title="Export Deal", total_value=100000, currency="USD")
        >>> result = await create_deal(deal_data, current_user, db)
        >>> print(result.title)
        "Export Deal"
    """
```

#### Code Comments
```python
def calculate_margin(selling_price: float, cost: float) -> float:
    """
    Calculate profit margin percentage.
    
    Formula: ((selling_price - cost) / selling_price) * 100
    
    Args:
        selling_price: Final selling price of the deal
        cost: Total cost including procurement and logistics
        
    Returns:
        Profit margin as a percentage (0-100)
        
    Note:
        Returns 0 if selling_price is 0 to avoid division by zero.
    """
    if selling_price == 0:
        return 0.0
    
    return ((selling_price - cost) / selling_price) * 100
```

#### README Sections
```markdown
## 🚀 Quick Start

1. Clone the repository
2. Install dependencies
3. Configure environment
4. Run migrations
5. Start services

## 📖 Usage

### Creating a Deal

```python
from artin_smart_trade import DealService

service = DealService()
deal = service.create_deal({
    "title": "Export Deal",
    "total_value": 100000,
    "currency": "USD"
})
```

## 🧪 Testing

Run tests with:
```bash
pytest
npm test
```
```

## 🔄 Pull Request Process

### 📋 PR Requirements

- **Clear Description**: Explain what changes were made and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update relevant documentation
- **No Merge Conflicts**: Resolve conflicts before submitting
- **Passing Tests**: All tests must pass
- **Code Quality**: Follow code standards

### 📝 PR Template

```markdown
## 📝 Description
Brief description of changes made.

## 🎯 Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## 🧪 Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] All tests passing

## 📚 Documentation
- [ ] API docs updated
- [ ] README updated
- [ ] Code comments added

## ✅ Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] Ready for review

## 🔗 Related Issues
Closes #123
Fixes #456
```

### 🔄 Review Process

1. **Automated Checks**
   - Code formatting
   - Linting
   - Type checking
   - Test coverage

2. **Code Review**
   - At least one reviewer approval
   - Address all feedback
   - Update PR as needed

3. **Integration Testing**
   - Verify no breaking changes
   - Test in staging environment
   - Performance impact assessment

4. **Merge**
   - Squash commits if needed
   - Merge to target branch
   - Delete feature branch

## 🚨 Issue Reporting

### 🐛 Bug Reports

Use the bug report template:

```markdown
## 🐛 Bug Description
Clear description of the bug

## 🔄 Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## 🎯 Expected Behavior
What you expected to happen

## 📸 Screenshots
Add screenshots if applicable

## 🌍 Environment
- OS: [e.g. Windows 10, macOS 12.0]
- Browser: [e.g. Chrome 98, Firefox 97]
- Version: [e.g. v1.2.3]

## 📝 Additional Context
Add any other context about the problem here
```

### ✨ Feature Requests

Use the feature request template:

```markdown
## 🌟 Feature Description
Clear description of the feature

## 🎯 Problem Statement
What problem does this solve?

## 💡 Proposed Solution
How you envision the solution

## 🎨 Alternatives Considered
Other approaches you considered

## 📊 Additional Context
Any additional context or mockups
```

## 🏷️ Release Process

### 📦 Version Management

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### 🔄 Release Steps

1. **Prepare Release**
   - Update version numbers
   - Update CHANGELOG
   - Tag release

2. **Build and Test**
   - Run full test suite
   - Build packages
   - Test deployment

3. **Deploy**
   - Deploy to staging
   - Run smoke tests
   - Deploy to production

4. **Post-Release**
   - Monitor for issues
   - Update documentation
   - Announce release

### 📝 CHANGELOG Format

```markdown
## [1.2.0] - 2024-02-22

### ✨ Added
- New deal management features
- Enhanced API documentation
- Performance improvements

### 🐛 Fixed
- Fixed login issue with special characters
- Resolved memory leak in background tasks
- Fixed currency conversion bug

### 🔒 Changed
- Updated authentication middleware
- Improved error handling
- Refactored deal service

### 🗑️ Removed
- Deprecated legacy API endpoints
- Removed unused dependencies
```

## 📞 Getting Help

### 💬 Community Support

- **GitHub Discussions**: [github.com/your-org/artin-smart-trade/discussions](https://github.com/your-org/artin-smart-trade/discussions)
- **Discord Community**: [discord.gg/artin-smart-trade](https://discord.gg/artin-smart-trade)
- **Stack Overflow**: Use tag `artin-smart-trade`

### 📧 Direct Support

- **Email**: contributors@artin-smart-trade.com
- **Issues**: [GitHub Issues](https://github.com/your-org/artin-smart-trade/issues)
- **Security**: security@artin-smart-trade.com

### 📚 Resources

- **Documentation**: [docs.artin-smart-trade.com](https://docs.artin-smart-trade.com)
- **API Reference**: [api.artin-smart-trade.com/docs](https://api.artin-smart-trade.com/docs)
- **Architecture**: [docs.artin-smart-trade.com/architecture](https://docs.artin-smart-trade.com/architecture)

## 🎉 Recognition

### 🏆 Contributors

We recognize all contributors through:
- **GitHub Contributors**: Listed in README
- **Release Notes**: Mentioned in changelog
- **Community Highlights**: Featured in newsletters
- **Contributor Hall of Fame**: Annual recognition

### 🌟 Recognition Levels

- **🥇 Platinum**: 100+ contributions
- **🥈 Gold**: 50-99 contributions
- **🥉 Bronze**: 10-49 contributions
- **🏅 Contributor**: 1-9 contributions

---

## 🎯 Ready to Contribute?

Thank you for considering contributing to Artin Smart Trade! Your contributions help make our platform better for everyone.

**🚀 [Get Started](https://github.com/your-org/artin-smart-trade/fork) | [Find Issues](https://github.com/your-org/artin-smart-trade/issues) | [Join Community](https://discord.gg/artin-smart-trade)**

---

*Built with ❤️ by the Artin Smart Trade Community*
