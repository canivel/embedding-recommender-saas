# Team Beta: ML Recommendation Engine

## Mission
Build the machine learning system that generates embeddings, trains recommendation models, and serves personalized recommendations with low latency.

## Technology Stack
- **Language**: Python 3.11+
- **ML Framework**: PyTorch 2.1+
- **Serving**: FastAPI
- **ANN Search**: FAISS (CPU initially, GPU optional)
- **Embedding Cache**: Redis
- **Model Storage**: S3
- **Experiment Tracking**: MLflow or Weights & Biases
- **Training Orchestration**: Integration with Airflow (Team Epsilon)

## Architecture

### Directory Structure
```
ml-engine/
├── src/
│   ├── api/
│   │   ├── recommendations.py
│   │   ├── embeddings.py
│   │   └── training.py
│   ├── models/
│   │   ├── matrix_factorization.py
│   │   ├── two_tower.py
│   │   └── graph_sage.py (Phase 3)
│   ├── serving/
│   │   ├── embedding_store.py
│   │   ├── ann_index.py
│   │   └── cache_manager.py
│   ├── training/
│   │   ├── trainer.py
│   │   ├── data_loader.py
│   │   └── evaluator.py
│   ├── features/
│   │   ├── encoders.py
│   │   └── preprocessors.py
│   └── main.py
├── notebooks/
│   └── experiments/
├── tests/
├── Dockerfile
└── requirements.txt
```

## Model Evolution (Progressive Complexity)

### Phase 1: Matrix Factorization (Weeks 1-2)
**Goal**: Fast baseline to validate pipeline

**Model**: Alternating Least Squares (ALS) or Bayesian Personalized Ranking (BPR)

```python
# src/models/matrix_factorization.py
import torch
import torch.nn as nn

class MatrixFactorization(nn.Module):
    def __init__(self, num_users: int, num_items: int, embedding_dim: int = 64):
        super().__init__()
        self.user_embeddings = nn.Embedding(num_users, embedding_dim)
        self.item_embeddings = nn.Embedding(num_items, embedding_dim)

        # Initialize with small random values
        nn.init.normal_(self.user_embeddings.weight, std=0.01)
        nn.init.normal_(self.item_embeddings.weight, std=0.01)

    def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor):
        user_embeds = self.user_embeddings(user_ids)
        item_embeds = self.item_embeddings(item_ids)
        return (user_embeds * item_embeds).sum(dim=1)

    def predict_user(self, user_id: int, all_items: torch.Tensor):
        user_embed = self.user_embeddings(torch.tensor([user_id]))
        item_embeds = self.item_embeddings(all_items)
        scores = torch.matmul(user_embed, item_embeds.T)
        return scores.squeeze()
```

**Training**:
```python
# src/training/trainer.py
def train_matrix_factorization(
    model: MatrixFactorization,
    train_loader: DataLoader,
    num_epochs: int = 10,
    lr: float = 0.001
):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss()

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        for batch in train_loader:
            user_ids, item_ids, ratings = batch
            optimizer.zero_grad()

            predictions = model(user_ids, item_ids)
            loss = criterion(predictions, ratings)

            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        print(f"Epoch {epoch+1}, Loss: {total_loss/len(train_loader):.4f}")

    return model
```

**Pros**: Simple, fast to train, good baseline
**Cons**: No feature incorporation, cold-start issues

---

### Phase 2: Two-Tower Neural Network (Weeks 3-4)
**Goal**: Incorporate item features, better generalization

**Model**: Separate encoders for users and items

```python
# src/models/two_tower.py
import torch
import torch.nn as nn

class TwoTowerModel(nn.Module):
    def __init__(
        self,
        num_users: int,
        num_items: int,
        item_feature_dim: int,
        embedding_dim: int = 128,
        hidden_dims: list = [256, 128]
    ):
        super().__init__()

        # User tower
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.user_tower = self._build_tower(embedding_dim, hidden_dims)

        # Item tower
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        self.item_feature_proj = nn.Linear(item_feature_dim, embedding_dim)
        self.item_tower = self._build_tower(embedding_dim * 2, hidden_dims)

    def _build_tower(self, input_dim: int, hidden_dims: list):
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(0.2))
            prev_dim = hidden_dim
        return nn.Sequential(*layers)

    def encode_user(self, user_ids: torch.Tensor):
        user_embed = self.user_embedding(user_ids)
        return self.user_tower(user_embed)

    def encode_item(self, item_ids: torch.Tensor, item_features: torch.Tensor):
        item_embed = self.item_embedding(item_ids)
        feature_embed = self.item_feature_proj(item_features)
        combined = torch.cat([item_embed, feature_embed], dim=1)
        return self.item_tower(combined)

    def forward(self, user_ids, item_ids, item_features):
        user_repr = self.encode_user(user_ids)
        item_repr = self.encode_item(item_ids, item_features)
        return torch.sum(user_repr * item_repr, dim=1)
```

**Training**: Similar to Phase 1, with feature encoding

**Pros**: Better cold-start, uses features
**Cons**: Still doesn't capture item-item relationships

---

### Phase 3: Lightweight GNN (Weeks 5-8)
**Goal**: Model item-item and user-item graph structure

**Model**: GraphSAGE (scalable, inductive)

```python
# src/models/graph_sage.py
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv

class GraphSAGERecommender(nn.Module):
    def __init__(
        self,
        num_nodes: int,
        input_dim: int,
        hidden_dim: int = 128,
        output_dim: int = 64,
        num_layers: int = 2
    ):
        super().__init__()
        self.node_embedding = nn.Embedding(num_nodes, input_dim)

        self.convs = nn.ModuleList()
        self.convs.append(SAGEConv(input_dim, hidden_dim))
        for _ in range(num_layers - 2):
            self.convs.append(SAGEConv(hidden_dim, hidden_dim))
        self.convs.append(SAGEConv(hidden_dim, output_dim))

    def forward(self, x, edge_index):
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:
                x = F.relu(x)
                x = F.dropout(x, p=0.2, training=self.training)
        return x

    def get_embeddings(self, node_ids, edge_index):
        x = self.node_embedding.weight
        embeddings = self.forward(x, edge_index)
        return embeddings[node_ids]
```

**Pros**: Captures graph structure, inductive (handles new nodes)
**Cons**: More complex, requires graph construction

---

## Embedding Serving System

### 1. Embedding Store (Redis)

```python
# src/serving/embedding_store.py
import redis
import numpy as np
import pickle

class EmbeddingStore:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.embedding_dim = 128

    def set_embeddings(self, tenant_id: str, embeddings: dict):
        """Store embeddings for a tenant."""
        for entity_id, embedding in embeddings.items():
            key = f"{tenant_id}:embedding:{entity_id}"
            # Serialize numpy array
            value = pickle.dumps(embedding)
            self.redis.set(key, value, ex=3600)  # 1 hour TTL

    def get_embedding(self, tenant_id: str, entity_id: str) -> np.ndarray:
        """Retrieve single embedding."""
        key = f"{tenant_id}:embedding:{entity_id}"
        value = self.redis.get(key)
        if value:
            return pickle.loads(value)
        return None

    def get_embeddings_batch(self, tenant_id: str, entity_ids: list) -> dict:
        """Retrieve multiple embeddings efficiently."""
        keys = [f"{tenant_id}:embedding:{eid}" for eid in entity_ids]
        values = self.redis.mget(keys)
        return {
            entity_id: pickle.loads(val) if val else None
            for entity_id, val in zip(entity_ids, values)
        }
```

### 2. ANN Index (FAISS)

```python
# src/serving/ann_index.py
import faiss
import numpy as np

class FAISSIndex:
    def __init__(self, dimension: int, index_type: str = "IVF"):
        self.dimension = dimension
        if index_type == "IVF":
            # Inverted File Index with Product Quantization
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFPQ(
                quantizer,
                dimension,
                nlist=100,  # Number of clusters
                m=8,  # Number of subquantizers
                nbits=8  # Bits per subquantizer
            )
        else:
            # Simple flat index (for small datasets)
            self.index = faiss.IndexFlatL2(dimension)

        self.id_map = {}  # Map FAISS index to item IDs

    def build(self, embeddings: np.ndarray, item_ids: list):
        """Build index from embeddings."""
        assert len(embeddings) == len(item_ids)

        # Train index (for IVF)
        if hasattr(self.index, 'train'):
            self.index.train(embeddings)

        # Add vectors
        self.index.add(embeddings)

        # Store ID mapping
        self.id_map = {i: item_id for i, item_id in enumerate(item_ids)}

    def search(self, query_embedding: np.ndarray, k: int = 10) -> list:
        """Search for k nearest neighbors."""
        query_embedding = query_embedding.reshape(1, -1)
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:  # Valid index
                results.append({
                    "item_id": self.id_map[idx],
                    "distance": float(dist),
                    "score": 1.0 / (1.0 + dist)  # Convert distance to score
                })
        return results

    def save(self, path: str):
        """Save index to disk."""
        faiss.write_index(self.index, path)
        # Also save id_map separately
        import pickle
        with open(f"{path}.idmap", "wb") as f:
            pickle.dump(self.id_map, f)

    @classmethod
    def load(cls, path: str):
        """Load index from disk."""
        instance = cls(dimension=128)  # Dimension will be overwritten
        instance.index = faiss.read_index(path)
        instance.dimension = instance.index.d

        import pickle
        with open(f"{path}.idmap", "rb") as f:
            instance.id_map = pickle.load(f)

        return instance
```

### 3. Recommendation Service

```python
# src/api/recommendations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class RecommendationRequest(BaseModel):
    tenant_id: str
    user_id: str
    count: int = 10
    filters: dict = {}

@router.post("/internal/ml/recommendations")
async def get_recommendations(request: RecommendationRequest):
    try:
        # 1. Get user embedding from cache
        embedding_store = EmbeddingStore(redis_url=settings.REDIS_URL)
        user_embedding = embedding_store.get_embedding(
            request.tenant_id, request.user_id
        )

        if user_embedding is None:
            # Cold start: use default or popular items
            return get_cold_start_recommendations(request.tenant_id, request.count)

        # 2. Load tenant's FAISS index
        index_path = f"s3://bucket/{request.tenant_id}/faiss_index.bin"
        faiss_index = FAISSIndex.load(index_path)

        # 3. Search ANN
        candidates = faiss_index.search(user_embedding, k=request.count * 2)

        # 4. Apply filters
        filtered = apply_filters(candidates, request.filters)

        # 5. Rerank (optional, Phase 2+)
        reranked = rerank_candidates(filtered, user_embedding)

        return {
            "recommendations": reranked[:request.count],
            "model_version": "v1.0.0",
            "latency_ms": 45,
            "cache_hit": user_embedding is not None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Training Pipeline

### Data Loader

```python
# src/training/data_loader.py
import pyarrow.parquet as pq
from torch.utils.data import Dataset, DataLoader

class InteractionDataset(Dataset):
    def __init__(self, parquet_path: str):
        # Load interactions from S3
        table = pq.read_table(parquet_path)
        self.user_ids = table['user_id'].to_numpy()
        self.item_ids = table['item_id'].to_numpy()
        self.labels = table['label'].to_numpy()

    def __len__(self):
        return len(self.user_ids)

    def __getitem__(self, idx):
        return {
            'user_id': self.user_ids[idx],
            'item_id': self.item_ids[idx],
            'label': self.labels[idx]
        }
```

### Model Training Orchestration

```python
# src/training/trainer.py
def train_model(tenant_id: str, model_type: str, config: dict):
    # 1. Load training data from S3
    data_path = f"s3://bucket/{tenant_id}/training_data/"
    train_dataset = InteractionDataset(data_path)
    train_loader = DataLoader(train_dataset, batch_size=1024, shuffle=True)

    # 2. Initialize model
    if model_type == "matrix_factorization":
        model = MatrixFactorization(...)
    elif model_type == "two_tower":
        model = TwoTowerModel(...)
    elif model_type == "gnn":
        model = GraphSAGERecommender(...)

    # 3. Train
    trainer = ModelTrainer(model, config)
    trainer.fit(train_loader)

    # 4. Evaluate
    metrics = evaluate_model(model, val_loader)
    print(f"NDCG@10: {metrics['ndcg_10']:.4f}")

    # 5. Generate embeddings for all items
    item_embeddings = model.encode_all_items()

    # 6. Build FAISS index
    faiss_index = FAISSIndex(dimension=128)
    faiss_index.build(item_embeddings, item_ids)

    # 7. Save to S3
    faiss_index.save(f"s3://bucket/{tenant_id}/faiss_index.bin")
    save_model(model, f"s3://bucket/{tenant_id}/model.pth")

    # 8. Update Redis with new embeddings
    embedding_store.set_embeddings(tenant_id, item_embeddings)

    return {"status": "success", "metrics": metrics}
```

## Cold-Start Handling

### Strategy 1: Popular Items
```python
def get_cold_start_recommendations(tenant_id: str, count: int) -> list:
    # Return most popular items for new users
    popular_items = get_popular_items(tenant_id, limit=count)
    return [{"item_id": item_id, "score": 0.5} for item_id in popular_items]
```

### Strategy 2: Content-Based
```python
def get_content_based_recommendations(
    tenant_id: str,
    user_profile: dict,
    count: int
) -> list:
    # Use item features to match user preferences
    # Example: If user likes "electronics", recommend electronics
    pass
```

## Evaluation Metrics

```python
# src/training/evaluator.py
import numpy as np

def ndcg_at_k(predictions: list, ground_truth: list, k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain."""
    dcg = sum([
        (2**rel - 1) / np.log2(i + 2)
        for i, rel in enumerate(predictions[:k])
    ])
    idcg = sum([
        (2**rel - 1) / np.log2(i + 2)
        for i, rel in enumerate(sorted(ground_truth, reverse=True)[:k])
    ])
    return dcg / idcg if idcg > 0 else 0.0

def precision_at_k(predictions: list, ground_truth: set, k: int = 10) -> float:
    """Precision@K."""
    return len(set(predictions[:k]) & ground_truth) / k

def recall_at_k(predictions: list, ground_truth: set, k: int = 10) -> float:
    """Recall@K."""
    return len(set(predictions[:k]) & ground_truth) / len(ground_truth)
```

## Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install PyTorch (CPU version for cost savings)
RUN pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-engine
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ml-engine
  template:
    spec:
      containers:
      - name: ml-engine
        image: ml-engine:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
```

## Success Criteria

- Recommendation latency p95 < 50ms
- NDCG@10 > 0.35 (baseline: 0.25)
- Cold-start coverage > 95%
- Model training time < 4 hours
- FAISS index build time < 30 minutes

## Development Workflow

### Phase 1 (Weeks 1-2): Matrix Factorization
- [ ] Implement ALS/BPR model
- [ ] Training pipeline
- [ ] FAISS index building
- [ ] Redis embedding cache
- [ ] Basic recommendation API

### Phase 2 (Weeks 3-4): Two-Tower
- [ ] Implement two-tower architecture
- [ ] Feature encoding (text, categorical)
- [ ] Improved cold-start handling
- [ ] A/B testing framework

### Phase 3 (Weeks 5-8): GNN
- [ ] Graph construction from interactions
- [ ] GraphSAGE implementation
- [ ] Graph sampling for scalability
- [ ] Advanced reranking
