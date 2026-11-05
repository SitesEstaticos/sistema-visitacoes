# SNCT IFPI — Gestão de Visitações

MVP responsivo Django para guias assumirem uma turma, localizar salas em uma planta do campus e atualizar ocupação em tempo real. Inclui operações seguras com transações, painel de emergência, métricas, polling de 5 segundos e suporte a uso móvel.

## Requisitos e execução

- Python 3.10+ (testado com Python 3.12)
- SQLite incluído no Python

```bash
cd snct_ifpi
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```
Acesse `http://127.0.0.1:8000/` como guia e `http://127.0.0.1:8000/admin/` como administrador. Cadastre contas de guia pelo admin. A imagem da planta deve ser copiada como `visitas/static/visitas/mapa-campus.jpg`; a pasta está preparada para esse arquivo. Sem ela, é exibido um fundo ilustrativo. Coordenadas X/Y são percentuais de 0 a 100 e podem ser alteradas no admin.

## Funcionalidades

- Login/logout do Django e seleção de turma com transação e `select_for_update()`; bloqueio de múltiplas turmas por guia e de múltiplos guias por turma. O SQLite serializa gravações e não implementa row-level locking: para concorrência pesada em produção, use PostgreSQL.
- Mapa com Panzoom, marcadores acoplados à imagem, atualização de estado a cada 5 s, banner offline, alerta visual após 15 min e alternância com CSRF. API bloqueia (403) tentativa de alterar sala de outra turma.
- Encerrar visitação conclui a turma e libera automaticamente todas as salas vinculadas.
- Admin actions de recuperação de turma/sala, com feedback de sucesso e limpeza dos timestamps/vínculos. `visit_count` incrementa a cada nova ocupação.

## Testes

```bash
python manage.py test
python manage.py check
```

## Implantação

Este repositório é uma base de MVP, não uma configuração de produção pronta. Antes de expor publicamente: defina `SECRET_KEY` via variável de ambiente, `DEBUG=False`, `ALLOWED_HOSTS` explícitos, HTTPS/cookies seguros, configure logging/backup e use PostgreSQL caso haja uso simultâneo intenso. Tailwind e Panzoom são carregados por CDN; disponibilize assets locais se for necessário operar sem internet. A API de polling continua a exigir autenticação e só endpoints POST alteram estado.
