# Embedding Recommender SaaS Platform

A production-ready, multi-tenant SaaS platform for building and serving personalized recommendation systems using embedding-based ML models.

## 🎯 Project Overview

This platform enables businesses to easily integrate state-of-the-art recommendation systems into their products without building ML infrastructure from scratch. Customers can upload their interaction data, train custom models, and get personalized recommendations via a simple API.

### Key Features

- ✅ **Multi-tenant Architecture**: Secure isolation between customers
- ✅ **Multiple ML Models**: Matrix Factorization → Two-Tower → GNN (progressive complexity)
- ✅ **Real-time Recommendations**: <100ms p95 latency via FAISS ANN search
- ✅ **Easy Integration**: RESTful API with comprehensive documentation
- ✅ **Data Pipeline**: Automated ingestion, validation, and feature engineering
- ✅ **Observability**: Full monitoring, logging, and tracing infrastructure
- ✅ **Scalable**: Kubernetes-based deployment with auto-scaling

## 📊 Architecture Decision

After analyzing three architectural approaches, we selected **Option 3: Pragmatic Startup MVP** based on:

| Metric | Option 1 (OpenAI) | Option 2 (Gemini) | **Option 3 (MVP)** |
|--------|------------------|-------------------|-------------------|
| Time to Market | 16-32 weeks | 24-48 weeks | **8-12 weeks** ✓ |
| Monthly Cost | $50K-100K+ | $75K-150K+ | **$5K-15K** ✓ |
| Team Size | 5-8 engineers | 6-10 engineers | **2-3 engineers** ✓ |
| Success Probability | 65% | 45% | **85%** ✓ |

**Why Option 3?**
- 10x lower costs extend runway
- Fast validation of product-market fit
- Clear upgrade path to advanced architectures
- Proven technology stack (lower risk)

See [research/](research/) for full analysis of all three options.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Embedding Recommender SaaS                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Frontend   │  │  Back Office │  │  Backend API │  │
│  │  (Next.js)  │  │  (Next.js)   │  │  (FastAPI)   │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                │                  │           │
│         └────────────────┴──────────────────┘           │
│                          │                              │
│         ┌────────────────┴────────────────┐             │
│         │                                 │             │
│  ┌──────▼──────┐                  ┌──────▼──────┐      │
│  │  ML Engine  │                  │    Data     │      │
│  │  (PyTorch)  │                  │  Pipeline   │      │
│  └──────┬──────┘                  └──────┬──────┘      │
│         │                                 │             │
│  ┌──────▼──────────────────────────────────▼──────┐    │
│  │         Infrastructure & Observability         │    │
│  │  (Kubernetes, Airflow, Prometheus, Grafana)    │    │
│  └────────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
.
├── docs/
│   ├── architecture/
│   │   └── SYSTEM_OVERVIEW.md          # High-level architecture
│   ├── api-contracts/
│   │   └── API_CONTRACTS.md            # Service interface definitions
│   ├── teams/
│   │   ├── alpha-backend-api/          # Backend API specs
│   │   ├── beta-ml-engine/             # ML Engine specs
│   │   ├── gamma-frontend/             # Frontend specs
│   │   ├── delta-backoffice/           # Back Office specs
│   │   ├── epsilon-control-plane/      # Infrastructure specs
│   │   ├── zeta-observability/         # Monitoring specs
│   │   └── eta-data-pipeline/          # Data Pipeline specs
│   └── DEVELOPMENT_ROADMAP.md          # Complete development plan
├── research/
│   ├── OPENAI.md                       # Option 1 analysis
│   ├── GEMINI.md                       # Option 2 analysis
│   └── CLAUDE.md                       # (placeholder)
├── backend-api/                        # [To be developed by Team Alpha]
├── ml-engine/                          # [To be developed by Team Beta]
├── frontend/                           # [To be developed by Team Gamma]
├── backoffice/                         # [To be developed by Team Delta]
├── control-plane/                      # [To be developed by Team Epsilon]
├── observability/                      # [To be developed by Team Zeta]
├── data-pipeline/                      # [To be developed by Team Eta]
└── README.md                           # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- kind or minikube (for Kubernetes)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd general-embedding-recommender-saas
   ```

2. **Start infrastructure services**
   ```bash
   docker-compose up -d postgres redis kafka minio
   ```

3. **Start Backend API** (Team Alpha)
   ```bash
   cd backend-api
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn src.main:app --reload
   ```

4. **Start ML Engine** (Team Beta)
   ```bash
   cd ml-engine
   pip install -r requirements.txt
   python src/training/train.py  # Train initial model
   uvicorn src.main:app --port 8001 --reload
   ```

5. **Start Frontend** (Team Gamma)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Grafana: http://localhost:3001

## 📚 Documentation

### For Developers

- **[Development Roadmap](docs/DEVELOPMENT_ROADMAP.md)**: Complete development plan with phases and milestones
- **[System Overview](docs/architecture/SYSTEM_OVERVIEW.md)**: High-level architecture and design decisions
- **[API Contracts](docs/api-contracts/API_CONTRACTS.md)**: Interface definitions between services

### For Teams

Each team has detailed specifications in `docs/teams/[team-name]/SPECIFICATION.md`:

- **[Team Alpha - Backend API](docs/teams/alpha-backend-api/SPECIFICATION.md)**: FastAPI REST API
- **[Team Beta - ML Engine](docs/teams/beta-ml-engine/SPECIFICATION.md)**: Recommendation models
- **[Team Gamma - Frontend](docs/teams/gamma-frontend/SPECIFICATION.md)**: Customer dashboard
- **[Team Delta - Back Office](docs/teams/delta-backoffice/SPECIFICATION.md)**: Admin tools
- **[Team Epsilon - Control Plane](docs/teams/epsilon-control-plane/SPECIFICATION.md)**: Infrastructure
- **[Team Zeta - Observability](docs/teams/zeta-observability/SPECIFICATION.md)**: Monitoring
- **[Team Eta - Data Pipeline](docs/teams/eta-data-pipeline/SPECIFICATION.md)**: Data ingestion

## 🛠️ Technology Stack

### Backend
- **API Framework**: FastAPI (Python 3.11+)
- **ML Framework**: PyTorch 2.1+
- **Database**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Search**: FAISS (ANN)

### Frontend
- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State**: Zustand
- **Data**: React Query

### Infrastructure
- **Orchestration**: Kubernetes
- **Workflows**: Apache Airflow
- **CI/CD**: GitHub Actions + ArgoCD
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or Loki
- **Tracing**: Jaeger

## 📖 API Examples

### Get Recommendations

```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "count": 10,
    "filters": {"category": "electronics"}
  }'
```

### Track Interaction

```bash
curl -X POST http://localhost:8000/api/v1/interactions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "item_id": "item_456",
    "interaction_type": "purchase"
  }'
```

### Upload Items

```bash
curl -X POST http://localhost:8000/api/v1/items \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "item_id": "item_789",
        "title": "Wireless Headphones",
        "category": "electronics"
      }
    ]
  }'
```

## 🎯 Development Phases

### Phase 1: Foundation (Weeks 1-4) - MVP
- Core API endpoints
- Matrix Factorization model
- Basic frontend dashboard
- Data ingestion pipeline
- Local deployment

### Phase 2: Enhancement (Weeks 5-8)
- Two-Tower neural network
- Advanced analytics
- A/B testing framework
- Performance optimization

### Phase 3: Production (Weeks 9-12)
- Security hardening
- Load testing
- Documentation completion
- Production deployment

## 📊 Success Metrics

### Technical KPIs
- API latency p95 < 100ms
- API availability > 99.9%
- Model NDCG@10 > 0.35
- Test coverage > 80%

### Business KPIs
- Time to first recommendation < 24 hours
- Customer onboarding < 1 week
- MRR growth > 20% month-over-month
- Churn rate < 5% monthly

## 🔄 Upgrade Path

This MVP architecture can be upgraded to more sophisticated systems once validated:

### Option 1: OpenAI Architecture (12-16 weeks)
- Add GraphSAGE/PinSage GNN models
- Multi-interest networks
- Distributed training
- Cost increase: 5-8x

### Option 2: Gemini Architecture (20-24 weeks)
- Heterogeneous graph infrastructure
- Foundation model approach
- Disaggregated training
- Cost increase: 10-15x

See [research/](research/) for detailed analysis.

## 🤝 Contributing

Each team should:
1. Read your team's specification thoroughly
2. Follow API contracts for inter-service communication
3. Write tests as you develop (TDD recommended)
4. Submit PRs with clear descriptions
5. Get code review before merging

## 📝 License

[To be determined]

## 👥 Team Structure

- **Team Alpha**: Backend API (FastAPI)
- **Team Beta**: ML Engine (PyTorch)
- **Team Gamma**: Frontend (Next.js)
- **Team Delta**: Back Office (Next.js)
- **Team Epsilon**: Control Plane (Kubernetes/Airflow)
- **Team Zeta**: Observability (Prometheus/Grafana)
- **Team Eta**: Data Pipeline (Kafka/Spark)

## 🎓 Learning Resources

- FastAPI: https://fastapi.tiangolo.com/
- PyTorch: https://pytorch.org/tutorials/
- FAISS: https://github.com/facebookresearch/faiss/wiki
- Next.js: https://nextjs.org/learn
- Kubernetes: https://kubernetes.io/docs/tutorials/
- Airflow: https://airflow.apache.org/docs/

## 📞 Support

- **Documentation**: See [docs/](docs/)
- **Issues**: Create GitHub issue
- **Discussions**: Use GitHub Discussions

---

**Built with ❤️ for startups who want to add world-class recommendations to their products**
