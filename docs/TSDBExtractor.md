# TSDBExtractor

Esse módulo é responsável por conectar ao banco de dados temporal, extrair os dados e armazená-los em uma lista para trata-los posteriormente.

Vamos tratar da implementação desse módulo e como ele pode ser alterado para se adequar a novas necessidades.

## Sumário

- [Onde é utilizado](#onde-é-utilizado)
- [Como a classe é implementada](#como-a-classe-é-implementada)
- [O que deve ser retornado por cada método](#o-que-deve-ser-retornado-por-cada-método)
  - [connect](#connect)
  - [query_iface_traffic](#query_iface_traffic)
- [Como alterar a classe para a sua necessidade](#como-alterar-a-classe-para-a-sua-necessidade)

## Onde é utilizado

O módulo `TSDBExtractor` do pacote `TSDB` é chamado no arquivo watcher.py, nos seguintes trechos de código:

1. Na função `main`, para se conectar ao banco de dados temporal:

    ```python
    db_client = TsdbExtractor.connect(TsdbExtractor, **TSDB_AUTH)
    ```

2. Na função `check_exceeded_intervals`, para extrair os dados do banco de dados temporal:

    ```python
        # querying for rx
        data = TsdbExtractor.query_iface_traffic(link_configs, "rx", db_client)
        check_link_data(data, reports, link_configs, "rx")

        # querying for tx
        data = TsdbExtractor.query_iface_traffic(link_configs, "tx", db_client)
        check_link_data(data, reports, link_configs, "tx")
    ```

## Como a classe é implementada

A classe `TSDBExtractor`, implementa a interface `TSDB` presente no arquivo `__init__.py` do pacote `TSDB`. Seus únicos métodos são `connect` e `query_iface_traffic`.

O método `connect` é responsável por se conectar ao banco de dados temporal, utilizando as credenciais passadas como parâmetro.

Enquanto o método `query_iface_traffic` é responsável por extrair os dados do banco de dados temporal, utilizando as credenciais passadas como parâmetro, e retornar uma lista com os dados extraídos.

## O que deve ser retornado por cada método

### connect

O método `connect` deve retornar um objeto do tipo `client` que representa a conexão com o banco de dados temporal.

Esse `client` será utilizado posteriormente para se fazer as consultas ao TSDB.

### query_iface_traffic

O método `query_iface_traffic` deve retornar uma `lista de dicionários` com os dados extraídos do banco de dados temporal com, **ao menos**, os seguintes pares de chave-valor:

```text
[
    {
        "time": timestamp,
        "value": value in bits
    },
    .
    .
    .
]
```

Essa lista será utilizada posteriormente para se verificar se os limites de tráfego foram excedidos.

## Como alterar a classe para a sua necessidade

Para alterar a classe `TSDBExtractor` para se adequar a sua necessidade, você deve:

1. Alterar o método `connect` para se conectar ao seu banco de dados temporal.

    Você pode criar ou alterar variáveis do seu arquivo `.env` para armazenar as credenciais do seu banco de dados temporal.

2. Alterar o método `query_iface_traffic` para extrair os dados do seu banco de dados temporal.

    Note que esse método **precisa** utilizar as variáveis de ambiente `QUERY_DATE_BEGIN` e `QUERY_DATE_END` para definir o intervalo de tempo que será consultado no banco de dados temporal.

    Essas variáveis de ambiente são definidas durante a execução do script e são utilizadas posteriormente para gerar o relatório.

Tenha em mente que os métodos devem retornar os tipos de dados especificados na seção [O que deve ser retornado por cada método](#o-que-deve-ser-retornado-por-cada-método).

## Exemplo de implementação

Para exemplificar como a classe `TSDBExtractor` pode ser alterada para se adequar a sua necessidade, vamos utilizar o banco de dados temporal [InfluxDB](https://www.influxdata.com/).

No pacote `TSDB`, existe um arquivo chamado `TsdbExtractor.influx.sample` que contém uma implementação utilizando o influxdb.

Tenha em mente que esse arquivo é apenas um exemplo de implementação e pode não funcionar para o seu caso de uso.
