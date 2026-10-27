# SPEC · P8 · data-seeding-pipeline

## Goal
Provar que gerenciamento profissional de massa de testes (test data management - TDM) resolve na raiz o maior gerador de testes instáveis em QA: dependência de banco compartilhado, colisões de chaves primárias e vazamento de dados de clientes reais (PII) em homologação.

## System under test
- **Domínio:** API de Pagamentos e Câmbio B2B multi-tenant (SaaS financeiro com Tenants, Usuários, Contas Correntes, Transações FX e Webhooks).
- **Armazenamento:** SQLite relacional com chaves estrangeiras ativadas (`PRAGMA foreign_keys = ON`) + exportação para JSON e APIs REST (simulação HTTP idempotente via headers de idempotência `Idempotency-Key`).
- **Por que este alvo:** É o domínio exato de fintech com maior criticidade de integridade referencial, conformidade com LGPD/GDPR (mascaramento de CPF, CNPJ e nomes) e isolamento entre execuções concorrentes de testes.

## O Problema de Engenharia
1. **Colisão de Massa Compartilhada:** Testes executados em paralelo que usam dados estáticos (`user@test.com`) falham aleatoriamente quando o teste B altera o estado que o teste A esperava.
2. **Vazamento de PII:** Empresas copiam dump de produção para homologação contendo documentos reais de pessoas físicas e jurídicas.
3. **Falta de Idempotência e Limpeza:** Executar a carga de testes duas vezes duplica registros ou trava com violação de unicidade (`UNIQUE constraint failed`), sem garantia de teardown limpo.

## Arquitetura da Solução
1. **Faker Determinístico com Semente Fixada:**
   - Suporte a semente determinística (`--seed 42`) para reproduzir cenários exatos de bug.
2. **Factories Relacionais com Dependências Cascata:**
   - Criação encadeada: `Tenant` -> `User` -> `Account` -> `Transaction` -> `WebhookDelivery`.
3. **Sanitização e Mascaramento PII (LGPD/GDPR):**
   - Mascarador com validação de dígitos verificadores válidos de CPF/CNPJ gerados algoritmicamente, sem corresponder a dados reais.
4. **Modos de Execução:**
   - **Isolado / Transacional:** Cada suíte de teste roda dentro de uma transação ou com tenant UUID dedicado.
   - **Idempotente:** Seeder verifica existência via hash de conteúdo / chave idempotente antes de reinserir.
   - **Teardown / Cleanup:** Estratégia de expurgo pós-execução baseada em tags/prefixos de teste (`test_run_<id>_*`).
5. **CLI `seed-pipeline`:**
   - Comandos CLI: `generate`, `seed`, `verify`, `teardown`, `mask`.

## What gets tested (Suíte de Testes)
- Integridade relacional de 100% dos dados gerados (0 violações de chave estrangeira).
- Prova de idempotência: rodar o seeding 2 vezes consecutivas com mesma chave resulta em exatamente 0 duplicações.
- Sanitização de PII: teste negativo prova que nenhum CPF/CNPJ/Email gerado vaza padrão não-mascarado.
- Teardown limpo: teste prova que 100% dos registros marcados com run-id são deletados sem órfãos.

## Done when criteria
1. CLI funcional com comandos `seed`, `mask`, `verify` e `teardown`.
2. Suíte de testes com cobertura >= 85% rodando em < 10s no pytest.
3. CI no GitHub Actions executando lint, testes, step summary e exportação de massa.
4. README bilíngue detalhando o problema de engenharia, arquitetura e trade-offs.
