# Central de Afiliados V2

Versão reconstruída em módulos, preservando a V1. A V2 usa banco separado em `data_v2/central_v2.db` e uploads em `data_v2/uploads/`; não sobrescreve o banco nem as fotos atuais.

## Recursos
- Painel com contadores e fila de publicações.
- Catálogo com busca, filtro por categoria, preço, comissão, link de afiliado e galeria de até 10 fotos por produto.
- Botão para copiar o link de afiliado, com alternativa caso a API de clipboard não esteja disponível.
- Formulários de cadastro/edição que preservam as fotos existentes.
- Planejamento de conteúdo com data, formato, status, legenda, hashtags e CTA.
- Registro manual de cliques, pedidos e comissão; não finge sincronização com a Shopee.
- Login, proteção básica de formulários contra CSRF, limite de upload de 20 MB e cookies de sessão com HttpOnly/SameSite.
- Layout mobile-first separado em templates e CSS para facilitar manutenção.

## Rodar no Termux
Na pasta raiz do repositório:
```bash
pip install flask
python v2/app.py
```
Abra no Chrome do mesmo celular: `http://127.0.0.1:5001`.
Credenciais iniciais de teste: usuário `1`, senha `1`. Antes de qualquer exposição à rede, defina `CENTRAL_USERNAME`, `CENTRAL_PASSWORD` e `CENTRAL_SECRET_KEY` no ambiente. O servidor é local, não de produção.

## Dados
A V2 inicia com um banco separado e vazio, sem importar ou modificar automaticamente os dados da V1. Depois de validar a V2, a migração pode ser feita com backup e conferência, sem apagar a original.

## Limitações
- Não há integração oficial automática com Shopee/Instagram.
- Publicação continua manual.
- Resultados são inseridos manualmente.
- Preços e comissões precisam ser conferidos no painel oficial antes de divulgar.
- A busca de produtos em tendências/mais vendidos ainda precisa de fonte/API confiável e não é inventada pela aplicação.
