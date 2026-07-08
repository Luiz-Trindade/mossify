"""
🌿 Exemplo de sistema e-commerce com Mossify.

Demonstra:
- Relacionamento entre modelos (Category 1:N Product)
- CRUD automático para ambos os modelos
- Paginação automática nas listagens
- Cache inteligente com invalidação automática
- Fila assíncrona para criação em lote (Products)
"""

from mossify import Mossify
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

# ============================================
# 1. Modelos
# ============================================


class Category(SQLModel, table=True):
    """Categoria de produtos."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None

    # Relacionamento 1:N com Product
    products: List["Product"] = Relationship(back_populates="category")


class Product(SQLModel, table=True):
    """Produto com categoria associada."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float = Field(gt=0, description="Preço deve ser maior que zero")
    stock: int = Field(default=0, ge=0, description="Estoque não pode ser negativo")
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")

    category: Optional[Category] = Relationship(back_populates="products")


# ============================================
# 2. Aplicação
# ============================================

app = Mossify(
    database_url="sqlite:///ecommerce.db",
    database_models=[Category, Product],
    title="E-Commerce API",
    description="API de e-commerce com CRUD automático e cache",
    cache_ttl=300,  # 5 minutos de cache padrão
)


# ============================================
# 3. CRUD automático
# ============================================

# Categorias – CRUD completo, síncrono
# Endpoints gerados:
#   GET    /categories          → listar (com paginação)
#   POST   /categories          → criar
#   GET    /categories/{id}     → obter
#   PATCH  /categories/{id}     → atualizar parcial
#   PUT    /categories/{id}     → substituir
#   DELETE /categories/{id}     → deletar
#   GET    /categories/count    → contar
app.register_model(Category, tags=["Categories"])

# Produtos – CRUD com fila assíncrona (suporta alta carga)
# Endpoints gerados:
#   GET    /products            → listar (com paginação)
#   POST   /products            → criar (retorna 202 Accepted com fila)
#   GET    /products/{id}       → obter
#   PATCH  /products/{id}       → atualizar parcial
#   PUT    /products/{id}       → substituir
#   DELETE /products/{id}       → deletar
#   GET    /products/count      → contar
app.register_model(
    Product,
    async_mode=True,  # ativa fila para POST
    batch_size=5_000,  # insere em lotes de 5000
    flush_interval=5.0,  # ou a cada 5 segundos
    tags=["Products"],
)


# ============================================
# 4. Execução
# ============================================

if __name__ == "__main__":
    # workers=1 recomendado para fila em memória
    app.run(host="0.0.0.0", port=8000)
