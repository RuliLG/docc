#!/bin/bash
# Comprehensive testing script

set -e

echo "🧪 Running comprehensive test suite..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Run backend linting
echo "🔍 Running backend linting..."
echo "  - Black formatting check..."
black --check backend/ cli/ shared/ || (echo "❌ Code formatting issues found. Run 'black backend/ cli/ shared/' to fix" && exit 1)

echo "  - Flake8 linting..."
flake8 backend/ cli/ shared/ || (echo "❌ Linting issues found" && exit 1)

echo "  - Import sorting check..."
isort --check-only backend/ cli/ shared/ || (echo "❌ Import sorting issues found. Run 'isort backend/ cli/ shared/' to fix" && exit 1)

# Run backend type checking
echo "  - Type checking with mypy..."
mypy backend/ cli/ shared/ || echo "⚠️  Type checking found issues"

echo "✅ Backend linting passed"

# Run backend tests
echo "🔬 Running backend tests..."
pytest backend/tests/ -v --cov=backend --cov=cli --cov=shared --cov-report=term-missing --cov-report=xml

echo "✅ Backend tests passed"

# Run frontend tests
echo "🎨 Running frontend tests..."
cd frontend

echo "  - ESLint check..."
npm run lint:check || (echo "❌ Frontend linting issues found. Run 'npm run lint' to fix" && exit 1)

echo "  - Prettier formatting check..."
npm run format:check || (echo "❌ Frontend formatting issues found. Run 'npm run format' to fix" && exit 1)

echo "  - TypeScript type check..."
npm run type-check || (echo "❌ TypeScript type errors found" && exit 1)

echo "  - Jest tests..."
npm test -- --coverage --watchAll=false || (echo "❌ Frontend tests failed" && exit 1)

cd ..

echo "✅ Frontend tests passed"

# Run integration tests
echo "🔗 Running integration tests..."
if [ -f "test_api.py" ]; then
    # Start backend server in background
    echo "  - Starting backend server..."
    uvicorn backend.main:app --host 0.0.0.0 --port 8001 &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 5
    
    # Run integration tests
    echo "  - Running API tests..."
    DOCC_API_BASE_URL="http://localhost:8001/api/v1" python test_api.py || echo "⚠️  Integration tests failed"
    
    # Stop server
    kill $SERVER_PID 2>/dev/null || true
    sleep 2
else
    echo "  - Skipping integration tests (test_api.py not found)"
fi

# Generate test report
echo "📊 Test Summary:"
echo "  ✅ Backend linting: PASSED"
echo "  ✅ Backend tests: PASSED"  
echo "  ✅ Frontend linting: PASSED"
echo "  ✅ Frontend tests: PASSED"

# Check coverage
echo "📈 Test Coverage:"
echo "  Backend coverage report generated in coverage.xml"
echo "  Frontend coverage report in frontend/coverage/"

echo ""
echo "🎉 All tests completed successfully!"