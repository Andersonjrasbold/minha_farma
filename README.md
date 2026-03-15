# Minha Farma

MVP de marketplace farmacêutico com Python + Flask + Bootstrap + PostgreSQL.

## Stack
- Backend: Flask
- Frontend: Bootstrap 5 + JavaScript
- ORM: SQLAlchemy
- Banco recomendado para nuvem: PostgreSQL

## Regras principais do MVP
1. Cada farmácia possui sua própria loja virtual.
2. A home mostra ofertas por cidade e por raio de entrega.
3. O usuário pode navegar, adicionar produtos ao carrinho e fechar um pedido.
4. O banco pode rodar localmente em PostgreSQL ou em nuvem com Neon, Render ou Supabase.

## Como rodar
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Banco de dados local (padrão: SQLite)
1. O projeto já vem configurado para usar SQLite por padrão (`sqlite:///minha_farma.db` em `.env.example`).
2. Gere o banco e a tabela:
```bash
source .venv/bin/activate
flask --app run.py db init
flask --app run.py db migrate -m "initial"
flask --app run.py db upgrade
```
3. Popule dados iniciais:
```bash
flask --app run.py seed
```

### Se preferir PostgreSQL
- Edite `.env` para `DATABASE_URL=postgresql+psycopg2://...@127.0.0.1:5432/minha_farma` e rode novamente `db upgrade`.

Crie as tabelas (migrations):
```bash
flask --app run.py db init          # primeira vez
flask --app run.py db migrate -m "initial"
flask --app run.py db upgrade
```

Popular dados iniciais:
```bash
flask --app run.py seed
```

Rodar:
```bash
python run.py
```

### Recriar banco local do zero (quando der erro de tabela)
```bash
flask --app run.py db upgrade
flask --app run.py seed
python run.py
```

Se a migration não existir ainda:
```bash
flask --app run.py db init      # primeira vez
flask --app run.py db migrate -m "initial"
flask --app run.py db upgrade
```

## Próximos passos recomendados
- painel da farmácia
- gateway de pagamento
- cálculo de frete por CEP
- geolocalização real por Maps API
- app mobile com Flutter ou React Native
- notificações por WhatsApp
# minha_farma
