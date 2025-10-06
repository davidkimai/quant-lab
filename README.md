# Quant Lab 

## Algorithmic Trading Backtesting Platform

An open-source platform for backtesting algorithmic trading strategies with real-time visualization.

## Features

- **3 Production Strategies**: Value Moat (Buffett-inspired), Trend Following, Multi-Factor
- **Event-Driven Backtesting**: Point-in-time data access prevents look-ahead bias
- **Real-Time Streaming**: Server-Sent Events (SSE) for live backtest progress
- **Modern Stack**: FastAPI + React + PostgreSQL/SQLite
- **Type-Safe**: Python type hints + TypeScript for end-to-end safety
- **Performance Metrics**: Sharpe, Sortino, Max Drawdown, Win Rate

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- OR: Python 3.11+, Node.js 20+, PostgreSQL (optional)

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/davidkimai/quant-lab.git
cd quant-lab

# Start all services
docker-compose up

# Access the application
# Web UI: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# 1. Install Python dependencies (Core + API)
cd packages/core
pip install -e .

cd ../api
pip install fastapi uvicorn sqlalchemy pydantic-settings

# 2. Install JavaScript dependencies (Web)
cd ../web
npm install

# 3. Start API server (Terminal 1)
cd packages/api
export PYTHONPATH=../core:.
python -m quant_lab_api.main
# API runs on http://localhost:8000

# 4. Start web server (Terminal 2)
cd packages/web
npm run dev
# Web runs on http://localhost:3000
```

## Architecture

```
quant-lab/
├── packages/
│   ├── core/           # Python library (portfolio, strategies, backtesting)
│   ├── api/            # FastAPI service (REST + SSE streaming)
│   └── web/            # React UI (Vite + Tailwind + Recharts)
├── data/               # Local data cache
├── docker-compose.yml  # Full-stack orchestration
└── README.md
```

### Technology Stack

**Backend:**
- FastAPI - High-performance async API
- SQLAlchemy - ORM with PostgreSQL/SQLite
- Pandas/NumPy - Quantitative analysis
- Pydantic - Data validation

**Frontend:**
- React 18 - Modern UI library
- TypeScript - Type safety
- Recharts - Data visualization
- Tailwind CSS - Utility-first styling
- Vite - Lightning-fast builds

## Usage

### Running a Backtest

1. **Open Web UI**: Navigate to http://localhost:3000
2. **Select Strategy**: Choose from Value Moat, Trend Following, or Multi-Factor
3. **Configure Parameters**:
   - Tickers: AAPL, MSFT, TSLA (comma-separated)
   - Date Range: 2024-01-01 to 2024-06-30
   - Initial Capital: $100,000
4. **Run**: Click "Run Backtest" and watch real-time progress
5. **Analyze Results**: View equity curve and performance metrics

### API Endpoints

```bash
# List strategies
curl http://localhost:8000/api/strategies

# Run backtest (SSE stream)
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "value_moat",
    "tickers": ["AAPL", "MSFT"],
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "initial_capital": 100000
  }'

# Health check
curl http://localhost:8000/health
```

## Trading Strategies

### 1. Value Moat Strategy
**Philosophy**: Buffett-inspired quality at reasonable prices

**Criteria**:
- ROE > 15% (efficient capital allocation)
- Revenue Growth > 10% (expanding moat)
- P/E < 25 (reasonable valuation)

**Use Case**: Long-term investing in high-quality companies

### 2. Trend Following Strategy
**Philosophy**: Momentum-based systematic trading

**Criteria**:
- Price momentum over 20-day period
- Volume confirmation
- Moving average crossovers

**Use Case**: Capturing sustained price trends

### 3. Multi-Factor Strategy
**Philosophy**: Hybrid quantitative approach

**Criteria**:
- Composite score from value, quality, and momentum factors
- Weighted factor combination (30% value, 40% quality, 30% momentum)
- Minimum score threshold of 0.6

**Use Case**: Balanced exposure across multiple investment factors

## Performance Metrics

- **Total Return**: Percentage gain/loss over backtest period
- **Sharpe Ratio**: Risk-adjusted returns (>1 is good, >2 is excellent)
- **Sortino Ratio**: Downside risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades

## Configuration

### Environment Variables

Create `.env` file in project root:

```env
# Database
DATABASE_TYPE=postgresql  # or sqlite
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=quantlab
POSTGRES_PASSWORD=quantlab
POSTGRES_DB=quantlab

# API
CORS_ORIGINS=["http://localhost:3000"]
DEBUG=true

# Web
VITE_API_URL=http://localhost:8000
```

### Database Options

**SQLite (Default)**: No setup required
```env
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./quant_lab.db
```

**PostgreSQL (Production)**:
```env
DATABASE_TYPE=postgresql
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
```

## Development

### Project Structure

```
packages/core/          # Core library
├── quant_lab/
│   ├── data/          # Data providers (CSV, Yahoo)
│   ├── portfolio/     # Portfolio management
│   ├── strategies/    # Trading strategies
│   ├── backtesting/   # Backtesting engine
│   └── models/        # Domain models
└── tests/

packages/api/           # FastAPI service
├── quant_lab_api/
│   ├── routes/        # API endpoints
│   ├── services/      # Business logic
│   ├── repositories/  # Data access
│   └── database/      # ORM models
└── tests/

packages/web/           # React frontend
├── src/
│   ├── components/    # UI components
│   ├── api/           # API client
│   └── types/         # TypeScript types
└── public/
```

### Running Tests

```bash
# Core library tests
cd packages/core
pytest

# API tests
cd packages/api
pytest

# Web tests
cd packages/web
npm test
```

### Code Quality

```bash
# Python formatting
black packages/core packages/api

# Python type checking
mypy packages/core packages/api

# TypeScript type checking
cd packages/web
npm run lint
```

## Extending the Platform

### Adding a New Strategy

1. Create strategy file in `packages/core/quant_lab/strategies/`:

```python
from quant_lab.strategies.protocols import Strategy

class MyStrategy:
    name = "My Strategy"
    description = "My custom trading strategy"
    
    def generate_signals(self, market_data, portfolio, current_date):
        signals = []
        # Your logic here
        return signals
```

2. Register in `packages/api/quant_lab_api/services/backtest_service.py`:

```python
STRATEGIES = {
    "my_strategy": MyStrategy(),
    # ... existing strategies
}
```

### Adding Data Providers

Implement the `DataProvider` protocol in `packages/core/quant_lab/data/protocols.py`:

```python
class MyDataProvider:
    async def fetch_prices(self, tickers, start, end):
        # Fetch price data
        pass
    
    async def fetch_fundamentals(self, tickers):
        # Fetch fundamental data
        pass
```

## Troubleshooting

### Common Issues

**Port conflicts**: Change ports in `docker-compose.yml` or config files

**Database connection**: Ensure PostgreSQL is running and credentials are correct

**CORS errors**: Add your frontend URL to `CORS_ORIGINS` in API config

**SSE streaming**: Some proxies/browsers may buffer SSE. Test with `curl` first.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Recharts](https://recharts.org/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pandas](https://pandas.pydata.org/)

---

**Version**: 0.1.0  
**Status**: Production Ready  
**Maintenance**: Active
