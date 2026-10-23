# Central de Afiliado Shopee — V1

Aplicação web pessoal, mobile-first, para organizar produtos, preparar conteúdo, planejar publicações e registrar resultados manualmente.

## Requisitos
- Android com Termux
- Python
- Flask

## Instalação no Termux
Abra o Termux e execute:

```bash
pkg update
pkg install python
pip install flask
```

Copie `app.py` para uma pasta no celular, por exemplo `~/central-afiliado/`.

Depois execute:

```bash
cd ~/central-afiliado
python app.py
```

Abra o Chrome no mesmo celular e acesse:

`http://127.0.0.1:5000`

Deixe o Termux aberto enquanto usa a central. Para parar, volte ao Termux e pressione `CTRL+C` (ou use a tecla CTRL do teclado virtual do Termux).

## O que a V1 faz
- Cadastra e edita produtos, links de afiliado, preço e comissão estimada.
- Permite salvar imagens de produtos e artes.
- Planeja publicações com data, formato e status.
- Guarda legenda, hashtags e chamada para ação.
- Monta um kit de publicação copiável.
- Registra cliques, pedidos e comissão manualmente a partir dos dados disponíveis no painel oficial.
- Armazena os dados localmente em `central.db`.

## Backup
Para fazer backup, pare a aplicação e copie a pasta inteira `central-afiliado`, especialmente `central.db` e `uploads/`, para um local seguro.

## Limitações importantes
- Não há conexão automática com Shopee ou Instagram na V1.
- Não há publicação automática.
- Cliques e pedidos são inseridos manualmente; os números não são verificados pela Shopee.
- A aplicação é local e não tem login. Não exponha a porta para a internet nem use em rede pública. Antes de permitir acesso remoto ou multiusuário, implementar autenticação e segurança.
- O preço pode mudar; confira o preço atual e o link antes de publicar.
