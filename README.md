# Link Watcher

Script para monitorar os limites de tráfego de links utilizando bases de dados temporais e containers docker.

```bash
usage: watcher.py [-h] {watcher,alert} ...

A script to analyze bandwidth usage of a given list of links
and alert if they exceed the configured thresholds

positional arguments:
  {watcher,alert}
    watcher        Queries the TSDB for the given links and checks if they exceeded the configured thresholds
    alert          Checks the given reports created by watcher mode and 

options:
  -h, --help       show this help message and exit
```

**watcher**:

```bash
python3 watcher.py watcher -h
usage: watcher.py watcher [-h] [-f FILE] [-o OUTPUT] [--date-begin DATE_BEGIN] [--date-end DATE_END]

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  json file with the configuration for each link.
  -o OUTPUT, --output OUTPUT
                        path where the json output will be stored

date range:
  Used to specify the date range to be used in the query/alert.
  If not given, the default date range will be used(from today 8h to today 18h defined in your .env file).
  BOTH FLAGS MUST BE BETWEEN DOUBLE QUOTES

  --date-begin DATE_BEGIN
                        starting date to be used in the query. In the format: "YYYY-MM-DD"
  --date-end DATE_END   Ending date to be used in the query. In the format: "YYYY-MM-DD"
```

**Alert**:

```bash
python3 watcher.py alert -h
usage: watcher.py alert [-h] [-d DIRECTORY] [-f FILE] [--time-threshold TIME_THRESHOLD] [--date-begin DATE_BEGIN] [--date-end DATE_END]

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        Directory where the reports are stored (alert mode will search for the reports in this directory). Default: ./volumes/watcher/
                        Can be changed in your .env file
  -f FILE, --file FILE  file containing the links info. Default: "./links.json
                        "
  --time-threshold TIME_THRESHOLD
                        Time(in minutes) threshold for a given link to be alerted. Default: 5
                        Example: If a certain link summed up to 5 or more minutes above the limit, in the given time range: this link will be added to the alert

date range:
  Used to specify the date range to be used in the alert.
  If not given, the default date range will be used: 2024-01-16 to 2024-01-23(7 days from now)

  --date-begin DATE_BEGIN
                        Starting date to be used in the alert. In the format: "YYYY-MM-DD"
  --date-end DATE_END   Ending date to be used in the alert. In the format: "YYYY-MM-DD"
```

***

## Sumário

- [Setup](#setup)
  - [Arquivo de configuração](#arquivo-de-configuração)
  - [Arquivo de input](#arquivo-de-input)
  - [Build](#build)
- [Execução](#execução)
  - [Especificando um período de tempo](#especificando-um-período-de-tempo)
  - [Exemplos de execução do modo watcher](#exemplos-de-execução-do-watcher)
  - [Exemplos de execução do modo alerta](#exemplos-de-execução-do-alerta)
- [Output](#output)
- [Logs](#logs)
- [Modularização](#modularização)
- [Como o PoP-PR utiliza o script](#como-o-pop-pr-utiliza-o-script)
  - [Cronjobs](#cronjobs)
  - [Relatórios](#relatórios)

## Setup

Esse script foi desenvolvido com o intuito de ser executado em um container docker. Portanto, para executá-lo, é necessário ter apenas o [docker](https://docs.docker.com/engine/install/ubuntu/) instalado.
***

### Arquivo de configuração

O arquivo [.env.sample](https://github.com/pop-pr-org/link-watcher/blob/main/.env.sample) contém **informações necessárias** para a execução do script.

Algumas variáveis já estarão preenchidas e podem ser usadas no seu arquivo `.env`. Outras variáveis **precisam ser preenchidas** com informações específicas do seu ambiente, sendo estas:

- Informações do banco de dados temporal:

```text
TSDB_HOST=seu_host
TSDB_PORT=porta_do_tsdb
TSDB_USER=seu_usuario
TSDB_PASS=sua_senha
TSDB_DB=nome_do_bd
TSDB_TIME_FORMAT=formato_da_data_no_bd("%Y-%m-%d %H:%M:%S", por exemplo)
TSDB_TIMEZONE=timezone da sua base de dados (UTC, por exemplo)
```

- Informações da sua IRM(Infraescture Resource Modelling):

```text
IRM_HOST=url da sua IRM
IRM_TOKEN=token de acesso a sua IRM
```

- Informações sobre a análise de cada link

```text
IGNORE_LIST=links que devem ser ignorados na análise(separados por vírgula e sem espaço. Pode estar vazio)
```

- Informações sobre o sistema de alerta por e-mail

```text
ALERTA_IP=IP do seu sistema de alerta
ALERTA_URL=endpoint do seu sistema de alerta
EMAILS_TO_ALERT=Contatos para alertar separados por vírgula
TELEGRAM_CHAT_IDS=IDs dos chats do telegram para alertar separados por vírgula (pode estar vazio)
```

Note que **não é necessário** inserir aspas(") nas variáveis, **apenas o valor**.

**Todas estas informações são necessárias** para que o script consiga se conectar ao banco de dados e analisar o tráfego com base nos seus limites preferenciais.

As **variáveis já preenchidas não necessitam de alteração**, mas podem ser alteradas caso queira.

***

### Arquivo de input

Para configurar os links que serão monitorados, existem **2 opções**:

- [Editar o arquivo links.json](#1-editar-o-arquivo-linksjson-com-os-links-que-deseja-monitorar)
- [Utilizar o módulo irm](#2-utilizar-o-módulo-irm)

### 1. Editar o arquivo [links.json](https://github.com/pop-pr-org/link-watcher/blob/main/links.json.sample) com os links que deseja monitorar

Os campos no arquivo são:

- `LINK_NAME`: Nome do link que será monitorado **(deve ser igual ao nome do link no banco de dados)**
- `LINK_SPEED`: Velocidade do link **em bits**
- `LINK_MAX_TRAFFIC_PERCENTAGE`: Porcentagem **máxima do tráfego do link**. Por exemplo, em um link com velocidade de 100Mbps e esta variável preenchida com `0.8`, ao atingir **80%** do uso, ou seja 80Mbps de tráfego, todos os **pontos acima disso** serão considerados como **violações de limite**
- `LINK_HISTERESYS`: Porcentagem de **histerese sobre o limite de tráfego**. Por exemplo, em um link com velocidade de 100Mbps, limite de **80%** e **histerese de 0.05**, ao atingir 80Mbps, o script irá considerar que o limite foi violado. Para considerar que esta **violação acabou** o tráfego deverá **atingir 76Mbps**. Isso **evita** que o script **fique alternando** entre limite **violado e não-violado** quando o tráfego se mantém próximo deste limite.

Prepare seu arquivo `json`, vamos chamar de `links.json`, no seguinte formato:

```json
{
      "LINK_A": {
            "LINK_SPEED": 10000000000, // NECESSÁRIO (em bits)
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.85, // OPCIONAL
      },
      "LINK_B": {
            "LINK_SPEED": 500000000, // NECESSÁRIO (em bits)
            "LINK_HISTERESYS": 0.05 // OPCIONAL
      },
      "LINK_C": {
            "LINK_SPEED": 700000000, // NECESSÁRIO (em bits)
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.7, // OPCIONAL
            "LINK_HISTERESYS": 0.05 // OPCIONAL
      },
      "LINK_D": {
            "LINK_SPEED": 700000000, // NECESSÁRIO (em bits)
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.9, // OPCIONAL
            "LINK_HISTERESYS": 0.08 // OPCIONAL
      }
}
```

Esse arquivo será indicado através da flag `-f` ou `--file` na execução do script.

Caso as variáveis `LINK_MAX_TRAFFIC_PERCENTAGE` ou `LINK_HISTERESYS` **não sejam indicadas no seu arquivo**, o script irá utilizar os valores padrões indicados no arquivo `.env`

### 2. Utilizar o módulo [irm](https://github.com/pop-pr-org/link-watcher/tree/main/irm)

Para isso, basta **não indicar** o arquivo `links.json` na execução do script(flag `-f|--file`). Dessa forma, o script irá utilizar o módulo `irm` para extrair as informações necessárias de uma fonte da verdade, como o netbox por exemplo.

Nesse caso, **será necessário** editar o arquivo `.env` com as informações necessárias para a conexão com a fonte da verdade:

```.env
IRM_HOST=url da sua fonte da verdade
IRM_TOKEN=token super secreto
```

O PoP-PR utiliza o [Netbox](https://docs.netbox.dev/en/stable) como fonte da verdade, e o script já está adaptado para utilizar ele. Existe um exemplo de como utilizar o irm do netbox no arquivo [netbox.py.sample](https://github.com/pop-pr-org/link-watcher/tree/main/irm/IrmExtractor.netbox.sample.py)

Caso **não utilize o `Netbox`**, será necessário adaptar o módulo `irm` para a sua fonte da verdade com o [IRM](https://www.networkcomputing.com/data-centers/challenge-it-infrastructure-resource-management) que você utiliza.

***

### Build

Para construir a imagem docker do script, basta executar:

```bash
docker build . -t link-watcher
```

***

## Execução

### Watcher

Para usar o script no modo `watcher`, basta executar:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher watcher
```

Um container será criado e irá executar [watcher.py](https://github.com/pop-pr-org/link-watcher/blob/main/watcher.py) com os parametros passados em [Dockerfile](https://github.com/pop-pr-org/link-watcher/blob/main/Dockerfile#L14)

#### Especificando um período de tempo

Por padrão, o script irá gerar um relatório para o dia atual, entre 8h e 18h. Caso queira gerar relatórios para um período em específico, entre 14 e 18 de agosto/2023 por exemplo, basta indicar através das flags `--date-begin` e `--date-end` na execução do script.

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher watcher --date-begin "2023-08-14" --date-end "2023-08-14"
```

O mesmo serve para algum dia específico, como 10 de fevereiro de 2023:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher watcher --date-begin "2023-02-10" --date-end "2023-02-10"
```

Lembre-se de que o formato da data é `YYYY-MM-DD` e a data deve estar entre **aspas**.

Dessa forma, o script irá gerar **um relatório**, dos links indicados no arquivo de input, **para cada dia** no período de tempo indicado(Levando em consideração **apenas** o horário indicado nas variáveis `TIME_BEGIN` e `TIME_END` no seu arquivo `.env`).

#### Exemplos de execução do Watcher

**Por padrão**, vamos utilizar o caminho `./volumes/watcher/` para **armazenar os relatórios e logs** do script, **dentro da máquina host**.

Já, **dentro do container**, o caminho padrão será `/tmp/watcher/`. Este **pode ser alterado** no seu arquivo `.env` através da variável `REPORT_OUTPUT_PATH`. Em **caso de alteração**, lembre-se de **alterar também** o caminho no **comando de execução** do script.

A seguir, alguns exemplos de **execução correta do script**:

- Executando o script **com** o arquivo de input `links.json` e gerando o relatório para o **dia atual**:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher watcher -f /opt/watcher/links.json
```

- Executando o script **sem** o arquivo de input e gerando o relatório para todo o **mês de agosto de 2023**:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher watcher --date-begin "2023-08-01" --date-end "2023-08-31"
```

- Executando o script **sem** o arquivo de input e gerando o relatório para o **dia 10 de fevereiro de 2023**:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher watcher --date-begin "2023-02-10" --date-end "2023-02-10"
```

Agora, alguns exemplos de **execução incorreta do script**:

- Executando o script sem indicar um volume para armazenar os relatórios e logs:

```bash
docker run --rm --name link-watcher link-watcher
```

Nesse caso, o script irá gerar um relatório para o dia atual, mas **irá armazená-lo em um loccal não acessível** da máquina host.

- Executando o script e indicando o caminho incorreto dentro do container para montar o volume

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/errado/ link-watcher watcher
```

Nesse caso, o script irá gerar um relatório para o dia atual, mas **não irá armazená-lo no volume**.

### Alert

Para usar o script no modo `alert`, basta executar:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher alert -d /tmp/watcher/ -f /tmp/watcher/links.json --date-begin "2023-08-07" --date-end "2023-08-14"
```

Lembre-se de que o formato da data é `YYYY-MM-DD` e a data deve estar entre **aspas**.

Nesse caso, o script irá gerar um alerta para o período de tempo indicado, utilizando o arquivo `links.json` como referência de velocidade para os links que serão analisados.

#### Exemplos de execução do alerta

Por padrão, vamos utilizar o caminho `./volumes/watcher/` para **armazenar os relatórios e logs** do script, **dentro da máquina host**.

Já, **dentro do container**, o caminho padrão será `/tmp/watcher/`. Este **pode ser alterado** no seu arquivo `.env` através da variável `REPORT_OUTPUT_PATH`. Em **caso de alteração**, lembre-se de **alterar também** o caminho no **comando de execução** do script.

A seguir, alguns exemplos de **execução correta do script**:

- Executando o script **sem** indicar o período de tempo e gerando o alerta para os últimos **7 dias**:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher alert -d /tmp/watcher/ -f /tmp/watcher/links.json
```

- Executando o script **indicando** o período de tempo e gerando o alerta para o **mês de agosto de 2023**:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher alert -d /tmp/watcher/ -f /tmp/watcher/links.json --date-begin "2023-08-01" --date-end "2023-08-31"
```

- Executando o script **indicando** o período de tempo e gerando o alerta para o **dia 10 de janeiro de 2024**:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher alert -d /tmp/watcher/ -f /tmp/watcher/links.json --date-begin "2024-01-10" --date-end "2024-01-10"
```

- Executando o script **sem** indicar o caminho do diretório onde os relatórios estão armazenados:

```bash
docker run --rm --name link-watcher link-watcher alert -f /tmp/watcher/links.json
```

Nesse caso, o script irá gerar um alerta para o período de tempo padrão, buscando os relatórios no diretório padrão(pode ser alterado no arquivo `.env`).

Agora, alguns exemplos de **execução incorreta do script**:

- Executando o script **indicando o diretório errado** onde os relatórios estão armazenados:

```bash
docker run --rm --name link-watcher link-watcher alert -d /caminho/errado/ -f /tmp/watcher/links.json
```

Nesse caso, o script **não** irá conseguir encontrar os relatórios para gerar o alerta.

- Executando o script **indicando o arquivo errado** de configuração dos links:

```bash
docker run --rm --name link-watcher -v ./volumes/watcher/:/tmp/watcher/ link-watcher alert -d /tmp/watcher/ -f /tmp/watcher/links.errado
```

Nesse caso, o script **não** irá conseguir encontrar o arquivo de configuração dos links.

***

## Output

Ao **fim da execução**, o script irá criar um arquivo `json` no local indicado através da variável `REPORT_OUTPUT_PATH` no [.env](https://gitlab.pop-pr.rnp.br/pop-pr/link-watcher/-/blob/main/.env.sample) com uma **lista de relatórios para cada link** no seguinte formato:

```json
{
      "Data": "10-02-23", // Data do relatório
      "LINK_A": { // Nome do link
            "rx": { // Direção do link
                  "total_exceeded": 15, // Tempo total excedido em minutos
                  "intervals": {
                        "1": { // Intervalo de tempo
                              "begin": "10/02/23-15:28:02",
                              "end": "10/02/23-15:48:02",
                              "exceeded_time": "15min",
                              "percentile": 71250.98
                        }
                  }
            },
            "tx": { // Direção do link
                  "total_exceeded": 0,
                  "intervals": {}
            }
      },
      "LINK_B": {
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

      "LINK_Z": {
            "rx": {
                  "total_exceeded": 40,
                  "intervals": {
                        "1": {
                              "begin": "10/02/23-00:09:13",
                              "end": "10/02/23-00:44:13",
                              "exceeded_time": "30min",
                              "percentile": 85347320.56

                        },
                        "2": {
                              "begin": "10/02/23-10:04:13",
                              "end": "10/02/23-10:19:13",
                              "exceeded_time": "10min",
                              "percentile": 5506328.61

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
                              "percentile": 4956625.78

                        }
                  }
            }
      }

}
```

Além disso, caso tenha utilizado o módulo IRM do link watcher, o script irá gerar um arquivo `json` com o template de configuração no local indicado através da variável `IRM_OUTPUT_PATH` no [.env](https://github.com/pop-pr-org/link-watcher/tree/main/.env.sample) com uma **lista de links** no seguinte formato:

```json
{
      "LINK_A": {
            "LINK_SPEED": 10000000000,
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.85,
            "LINK_HISTERESYS": 0.05
      },
      "LINK_B": {
            "LINK_SPEED": 500000000,
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.8,
            "LINK_HISTERESYS": 0.05
      },
      "LINK_C": {
            "LINK_SPEED": 700000000,
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.7,
            "LINK_HISTERESYS": 0.05
      },
      "LINK_D": {
            "LINK_SPEED": 700000000,
            "LINK_MAX_TRAFFIC_PERCENTAGE": 0.9,
            "LINK_HISTERESYS": 0.08
      }
}
```

Assim, não será necessário editar o arquivo de input manualmente ou buscar as informações novamente na fonte da verdade.


## Modularização

O script está sendo adaptado para ser modularizado. Dessa forma, será possível adicionar novos módulos para extrair informações de fontes da verdade diferentes, como o netbox por exemplo.

No PoP-PR, utilizamos o [InfluxDB](https://www.influxdata.com/) como banco de dados temporal, mas o script pode ser adaptado para utilizar outros bancos de dados temporais, veja mais informações no diretório [docs](https://github.com/pop-pr-org/link-watcher/tree/main/docs).

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

***

## Logs

Os logs do script são armazenados no volume do container, dentro do diretório `<caminho do projeto>/volumes/watcher/watcher.log`

***
