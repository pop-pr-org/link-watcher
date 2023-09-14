# Link Watcher

Script para monitorar os limites de tráfego de links utilizando bases de dados temporais usando docker.

```bash
python3 watcher.py -h

usage: watcher.py [-h] [-f FILE] [-o OUTPUT] [--time-begin TIME_BEGIN] [--time-end TIME_END] [--alert] [-n NUMBER_OF_DAYS]

A script to check if the traffic of a given list of links
is exceeding the configured thresholds.

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  json file with the configuration
  -o OUTPUT, --output OUTPUT
                        path where the json output will be stored

Time range:
  Used to specify the time range to be used in the query.
  If not given, the default time range will be used(from today 8h to today 18h).
  BOTH FLAGS MUST BE BETWEEN QUOTES

  --time-begin TIME_BEGIN
                        starting time to be used in the query. In the format: "YYYY-MM-DD"
  --time-end TIME_END   Ending time to be used in the query. In the format: "YYYY-MM-DD"

alert:
  Options to send alerts.
  If none is given, the script will only check the links and generate the report.

  --alert               If given, ONLY sends the alert
  -n NUMBER_OF_DAYS, --number_of_days NUMBER_OF_DAYS
                        Number of days to be checked and alerted
```

***

## Sumário

- [Setup](#setup)
  - [Arquivo de configuração](#arquivo-de-configuração)
  - [Arquivo de input](#arquivo-de-input)
  - [Build](#build)
- [Execução](#execução)
  - [Especificando um período de tempo](#especificando-um-período-de-tempo)
  - [Exemplos de execução](#exemplos-de-execução)
- [Output](#output)
- [Logs](#logs)
- [Modularização](#modularização)
- [Como o PoP-PR utiliza o script](#como-o-pop-pr-utiliza-o-script)
  - [Cronjobs](#cronjobs)
  - [Relatórios](#relatórios)
  - [Alertas](#alertas)

## Setup

Esse script foi desenvolvido com o intuito de ser executado em um container docker. Portanto, para executá-lo, é necessário ter apenas o [docker](https://docs.docker.com/engine/install/ubuntu/) instalado.
***

### Arquivo de configuração

O arquivo [.env.sample](https://github.com/pop-pr-org/link-watcher/tree/main/.env.sample) contém **informações necessárias** para a execução do script.

Algumas variáveis já estarão preenchidas e podem ser usadas no seu arquivo `.env`. Outras variáveis **precisam ser preenchidas** com informações específicas do seu ambiente, sendo estas:

- Informações do banco de dados temporal:

      TSDB_HOST=seu_host
      TSDB_PORT=porta_do_tsdb
      TSDB_USER=seu_usuario
      TSDB_PASS=sua_senha
      TSDB_DB=nome_do_bd
      TSDB_TIME_FORMAT=formato_da_data_no_bd("%Y-%m-%d %H:%M:%S", por exemplo)

- Informações da sua IRM(Infraescture Resource Modelling):

      IRM_HOST=url da sua IRM
      IRM_TOKEN=token de acesso a sua IRM

- Informações sobre a análise de cada link

      LINK_MAX_TRAFFIC_PERCENTAGE=porcentagem máxima do tráfego do link
      LINK_HISTERESYS=porcentagem de histerese sobre o limite de tráfego
      TIME_BEGIN=horário de início da análise
      TIME_END=horário de fim da análise
      IGNORE_LIST=links que devem ser ignorados na análise(separados por vírgula e sem espaço)

Note que **não é necessário** inserir aspas(") nas variáveis, **apenas o valor**.

**Todas estas informações são necessárias** para que o script consiga se conectar ao banco de dados e analisar o tráfego com base nos seus limites preferenciais.

As **variáveis já preenchidas não necessitam de alteração**, mas podem ser alteradas caso queira.

***

### Arquivo de input

Para configurar os links que serão monitorados, existem **2 opções**:

- [Editar o arquivo hosts.json](#1-editar-o-arquivo-hostsjson-com-os-links-que-deseja-monitorar)
- [Utilizar o módulo irm](#2-utilizar-o-módulo-irm)

### 1. Editar o arquivo [hosts.json](https://github.com/pop-pr-org/link-watcher/tree/main/hosts.json) com os links que deseja monitorar

Os campos no arquivo são:

- `LINK_NAME`: Nome do link que será monitorado **(deve ser igual ao nome do link no banco de dados)**
- `LINK_SPEED`: Velocidade do link **em bits**
- `LINK_MAX_TRAFFIC_PERCENTAGE`: Porcentagem **máxima do tráfego do link**. Por exemplo, em um link com velocidade de 100Mbps e esta variável preenchida com `0.8`, ao atingir **80%** do uso, ou seja 80Mbps de tráfego, todos os **pontos acima disso** serão considerados como **violações de limite**
- `LINK_HISTERESYS`: Porcentagem de **histerese sobre o limite de tráfego**. Por exemplo, em um link com velocidade de 100Mbps, limite de **80%** e **histerese de 0.05**, ao atingir 80Mbps, o script irá considerar que o limite foi violado. Para considerar que esta **violação acabou** o tráfego deverá **atingir 76Mbps**. Isso **evita** que o script **fique alternando** entre limite **violado e não-violado** quando o tráfego se mantém próximo deste limite.

Prepare seu arquivo `json`, vamos chamar de `hosts.json`, no seguinte formato:

```json
{
      "LINKS": [
      {
            "LINK_NAME": "HOST_A", // NECESSÁRIO
            "LINK_SPEED": 100000000000 // NECESSÁRIO (em bits)
      },
      {
            "LINK_NAME": "HOST_B",
            "LINK_SPEED": 100000000000,
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.8, // OPCIONAL
      },
      {
            "LINK_NAME": "HOST_C",
            "LINK_SPEED": 100000000000,
            "LINK_HISTERESYS": 0.05 // OPCIONAL
      },
      {
            "LINK_NAME": "HOST_D",
            "LINK_SPEED": 10000000000,
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.75, // OPCIONAL
            "LINK_HISTERESYS": 0.05 // OPCIONAL
      }
    ]
}
```

Esse arquivo será indicado através da flag `-f` ou `--file` na execução do script.

Caso as variáveis `LINK_MAX_TRAFFIC_PERCENTAGE` ou `LINK_HISTERESYS` **não sejam indicadas no seu arquivo**, o script irá utilizar os valores padrões indicados no arquivo `.env`

### 2. Utilizar o módulo [irm](https://github.com/pop-pr-org/link-watcher/tree/main/irm)

Para isso, basta **não indicar** o arquivo `hosts.json` na execução do script(flag `-f|--file`). Dessa forma, o script irá utilizar o módulo `irm` para extrair as informações necessárias de uma fonte da verdade, como o netbox por exemplo.

Nesse caso, **será necessário** editar o arquivo `.env` com as informações necessárias para a conexão com a fonte da verdade:

```.env
IRM_HOST=url da sua fonte da verdade
IRM_TOKEN=token super secreto
```

O PoP-PR utiliza o [Netbox](https://docs.netbox.dev/en/stable) como fonte da verdade, e o script já está adaptado para utilizar ele. Existe um exemplo de como utilizar o irm do netbox no arquivo [netbox.py.sample](https://github.com/pop-pr-org/link-watcher/tree/main/irm/IrmExtractor.netbox.sample)

Caso **não utilize o `Netbox`**, será necessário adaptar o módulo `irm` para a sua fonte da verdade com o [IRM](https://www.networkcomputing.com/data-centers/challenge-it-infrastructure-resource-management) que você utiliza.

***

### Build

Para construir a imagem docker do script, basta executar:

```bash
docker build . -t link-watcher
```

***

## Execução

Para usar o script, basta executar:

```bash
docker run --name link-watcher -v ./volumes/watcher:/tmp/watcher link-watcher
```

Um container será criado e irá executar [main.py](https://github.com/pop-pr-org/link-watcher/tree/main/main.py) com os parametros passados em [Dockerfile](https://github.com/pop-pr-org/link-watcher/tree/main/Dockerfile#L15)

### Especificando um período de tempo

Por padrão, o script irá gerar um relatório para o dia atual, entre 8h e 18h. Caso queira gerar relatórios para um período em específico, entre 14 e 18 de agosto/2023 por exemplo, basta indicar através das flags `--time-begin` e `--time-end` na execução do script.

```bash
docker run --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher --time-begin "2023-08-14" --time-end "2023-08-14"
```

O mesmo serve para algum dia específico, como 10 de fevereiro de 2023:

```bash
docker run --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher --time-begin "2023-02-10" --time-end "2023-02-10"
```

Lembre-se de que o formato da data é `YYYY-MM-DD` e a data deve estar entre **aspas**.

Dessa forma, o script irá gerar **um relatório**, dos links indicados no arquivo de input, **para cada dia** no período de tempo indicado(Levando em consideração **apenas** o horário indicado nas variáveis `TIME_BEGIN` e `TIME_END` no seu arquivo `.env`).

### Exemplos de execução

**Por padrão**, vamos utilizar o caminho `./volumes/watcher/` para **armazenar os relatórios e logs** do script, **dentro da máquina host**.

Já, **dentro do container**, o caminho padrão será `/tmp/watcher/`. Este **pode ser alterado** no seu arquivo `.env` através da variável `REPORT_OUTPUT_PATH`. Em **caso de alteração**, lembre-se de **alterar também** o caminho no **comando de execução** do script.

A seguir, alguns exemplos de **execução correta do script**:

- Executando o script **com** o arquivo de input `hosts.json` e gerando o relatório para o **dia atual**:

```bash
docker run --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher -f /opt/watcher/hosts.json
```

- Executando o script **sem** o arquivo de input e gerando o relatório para todo o **mês de agosto de 2023**:

```bash
docker run --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher --time-begin "2023-08-01" --time-end "2023-08-31"
```

- Executando o script **sem** o arquivo de input e gerando o relatório para o **dia 10 de fevereiro de 2023**:

```bash
docker run --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher --time-begin "2023-02-10" --time-end "2023-02-10"
```

Agora, alguns exemplos de **execução incorreta do script**:

- Executando o script sem indicar um volume para armazenar os relatórios e logs:

```bash
      docker run --name link-watcher link-watcher
```

Nesse caso, o script irá gerar um relatório para o dia atual, mas **irá armazená-lo onde não será acessível** da máquina host.

- Executando o script e indicando o caminho incorreto dentro do container para montar o volume

```bash
docker run --name link-watcher -v ./volumes/watcher/:/tmp/errado/ link-watcher
```

Nesse caso, o script irá gerar um relatório para o dia atual, mas **não irá armazená-lo no volume**.

***

## Output

Ao **fim da execução**, o script irá criar um arquivo `json` no local indicado através da variável `REPORT_OUTPUT_PATH` no [.env](https://github.com/pop-pr-org/link-watcher/tree/main/.env.sample) com uma **lista de relatórios para cada link** no seguinte formato:

```json
{
      "Data": "10-02-23", // Data do relatório
      "HOST_A": { // Nome do link
            "rx": { // Direção do link
                  "total_exceeded": 15, // Tempo total excedido em minutos
                  "intervals": {
                        "1": { // Intervalo de tempo
                              "begin": "10/02/23-15:28:02",
                              "end": "10/02/23-15:48:02",
                              "exceeded_time": "15min",
                              "max_value": "80469034.8", // Máximo do tráfego no período em bits
                              "mean_value": "82061956.6", // Média do tráfego no período em bits
                              "min_value": "83654878.4" // Mínimo do tráfego no período em bits
                        }
                  }
            },
            "tx": { // Direção do link
                  "total_exceeded": 0,
                  "intervals": {}
            }
      },
      "HOST_B": {
            "rx": {
                  "total_exceeded": 0,
                  "intervals": {}
            },
            "tx": {
                  "total_exceeded": 0,
                  "intervals": {}
            }
      },

      //
      // outros links
      //

      "HOST_Z": {
            "rx": {
                  "total_exceeded": 40,
                  "intervals": {
                        "1": {
                              "begin": "10/02/23-00:09:13",
                              "end": "10/02/23-00:44:13",
                              "exceeded_time": "30min",
                              "max_value": "80469034.8", 
                              "mean_value": "82061956.6", 
                              "min_value": "83654878.4" 
                        },
                        "2": {
                              "begin": "10/02/23-10:04:13",
                              "end": "10/02/23-10:19:13",
                              "exceeded_time": "10min",
                              "max_value": "80469034.8", 
                              "mean_value": "82061956.6", 
                              "min_value": "83654878.4" 
                        }
                  }
            },
            "tx": {
                  "total_exceeded": 40,
                  "intervals": {
                        "1": {
                              "begin": "10/02/23-00:09:13",
                              "end": "10/02/23-00:54:13",
                              "exceeded_time": "40min",
                              "max_value": "80469034.8", 
                              "mean_value": "82061956.6", 
                              "min_value": "83654878.4" 
                        }
                  }
            }
      }

}
```

## Logs

Os logs do script são armazenados no volume do container, dentro do diretório `<caminho do projeto>/volumes/watcher/watcher.log`

***

## Modularização

O script está sendo adaptado para ser modularizado. Dessa forma, será possível adicionar novos módulos para extrair informações de fontes da verdade diferentes, como o netbox por exemplo.

No PoP-PR, utilizamos o [InfluxDB](https://www.influxdata.com/) como banco de dados temporal, mas o script pode ser adaptado para utilizar outros bancos de dados temporais.

Para **alterar qualquer um dos dois citados anteriormente**, uma **nova classe deverá ser implementada** no respectivo diretório (tsdb ou irm)

## Como o PoP-PR utiliza o script

Nosso script é executado diariamente através de um cronjob em um dos servidores do PoP-PR. Um sample do cronjob pode ser encontrado em [link-watcher.cron.sample](https://github.com/pop-pr-org/link-watcher/tree/main/cron/link-watcher.cron.sample).

### Cronjobs

Temos três cronjobs configurados, que irão executar scripts diferentes:

```cron
# watcher run
55 23 * * * root /docker/link-watcher/cron/daily-watcher.sh
# alerta run weekly
30 8 * * mon root /docker/link-watcher/cron/weekly-alert.sh
# alerta run monthly
30 8 1 * * root /docker/link-watcher/cron/monthly-alert.sh
```

O primeiro gera o relatório diário, o segundo envia alertas relativos à ultima semana e o terceiro envia alertas relativo ao último mês.

***

### Relatórios

Os relatórios gerados diariamente ficam armazenados no volume do container junto com arquivo de logs em `<caminho do projeto>/volumes/watcher/`.

### Alertas

**Esse script será depreciado em breve.** Nas próximas versões, o alerta **será um módulo do script principal**. Facilitando a manutenção, configuração e criação de novos módulos de alerta.

O script `alert.py` serve para nos avisar toda semana sobre links que estão com tráfego acima do limite configurado. Ele também é executado através de um cronjob.

Caso você também utilize o [Alerta](https://docs.alerta.io/quick-start.html), basta configurar as variáveis no seu [.env](https://github.com/pop-pr-org/link-watcher/tree/main/.env.sample).

Caso contrário, você pode criar um script para enviar os alertas da forma que preferir.

***

## Roadmap

- [X] criar módulos para extrair informações de fontes da verdade. Ex.: netbox, CMDB, etc.
- [x] gerar o arquivo de configuração `input.json` sempre após a execução do script
- [ ] cuidar com mais de um circuito em um site
- [ ] modularizar as etapas do script
- [ ] separar em input, processamento e output
- [ ] modularizar estas 3 etapas
- [ ] usar o padrão de projeto strategy para modularizar as fontes da verdade e bases de dados
- [ ] adicionar healthcheck
- [ ] adicionar testes unitários
- [ ] adicionar testes de integração
