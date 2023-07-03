# Link Watcher

Script para monitorar os limites de tráfego de links utilizando bases de dados temporais usando docker.

```bash
python3 watcher.py -h

usage: watcher.py [-h] [-f FILE] [-o OUTPUT]

A script to check if the traffic of a given list of links is exceding the configured thresholds.

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  json file with the configuration
  -o OUTPUT, --output OUTPUT
                        path where the json output will be stored
```

***

## Sumário

- [Setup](#setup)
  - [Arquivo de configuração](#arquivo-de-configuração)
  - [Arquivo de input](#arquivo-de-input)
  - [Build](#build)
- [Execução](#execução)
- [Output](#output)
- [Logs](#logs)
- [Como o PoP-PR utiliza o script](#como-o-pop-pr-utiliza-o-script)
  - [Cronjobs](#cronjobs)
  - [Relatórios](#relatórios)
  - [Alertas](#alertas)

## Setup

Esse script foi desenvolvido com o intuito de ser executado em um container docker. Portanto, para executá-lo, é necessário ter apenas o [docker](https://docs.docker.com/engine/install/ubuntu/) instalado.
***

### Arquivo de configuração

Edite o arquivo [.env](https://github.com/PoP-PR/link-watcher/blob/main/watcher.env.sample) com as informações necessárias para o funcionamento do script.

Todas as variáveis e suas descrições a seguir:

```.env
# versioning
VERSION=1.0.0 -> versão do script (não é necessário alterar) 
# watcher info
DEFAULT_MAX_TRAFFIC_PERCENTAGE = 0.8  # Porcentagem máxima do consumo de banda do link (80%)
DEFAULT_LINK_HISTERESYS = 0.05  # Hysterese da porcentagem máxima (5%)
TIME_RANGE = "now() - 1d" # Período de tempo usado na query do TSDB, mude de acordo com a sua necessidade

# watcher output
OUTPUT_IDENT_LEVEL = 6 # identação do arquivo de output
# irm info
IRM_HOST="<url da sua fonte da verdade>"
IRM_TOKEN="<token super secreto>"
# tsdb info
TSDB_HOST="<IP/domínio da sua base de dados>" 
TSDB_PORT=<porta de acesso à sua base de dados>
TSDB_USER="<Usuário>"
TSDB_PASS="<Senha do usuário>"
TSDB_DB="<Nome da base>"
# API info
API_HOST="<IP/domínio da API>" # em desenvolvimento
API_USER="<Usuário da API>" # em desenvolvimento
API_PASS="<Senha do Usuário>" # em desenvolvimento
# Alert
TIME_THRESHOLD = 60  # período de tempo em minutos mínimo para enviar alerta
ALERTA_IP="<IP do alerta>"
ALERTA_URL = "<URL do Alerta>"
EMAILS_TO_ALERT = "Contatos para alerta separados por vírgula"
# Log file
LOGGING_LEVEL = "INFO"  # [DEBUG, INFO, WARNING, ERROR, CRITICAL]
MAX_LOG_SIZE = 10  # in MB
BACKUP_COUNT = 4  # number of log files to keep
LOG_FILE = "/tmp/watcher/watcher.log"  # path do log dentro do container
LOGGER_NAME = "watcher"
```

todas as informações são necessárias para que o script consiga se conectar ao banco de dados e analisar o tráfego com base nos seus limites preferenciais.

No PoP-PR, utilizamos o [InfluxDB](https://www.influxdata.com/) como banco de dados temporal, mas o script pode ser adaptado para utilizar outros bancos de dados temporais.
Para isso, uma nova classe deverá ser implementada no diretório [tsdb](https://github.com/PoP-PR/link-watcher/blob/main/tsdb) \
 para que o script consiga se conectar e fazer queries. Existe um exemplo usando o [influxDB](https://github.com/PoP-PR/link-watcher/blob/main/tsdb/influx_example.py)

***

### Arquivo de input

Para configurar os links que serão monitorados, existem **2 opções**:

### 1. Editar o arquivo [hosts.json](https://github.com/PoP-PR/link-watcher/blob/main/hosts.json) com os links que deseja monitorar

Os campos no arquivo são:

- `LINK_NAME`: Nome do link que será monitorado **(deve ser igual ao nome do link no banco de dados)**
- `LINK_SPEED`: Velocidade do link **em bits**
- `LINK_MAX_TRAFFIC_PERCENTAGE`: Porcentagem máxima do tráfego do link. Por exemplo, em um link com velocidade de 100Mbps, ao atingir 0.8 do uso, ou seja 80Mbps de tráfego, todos os pontos acima disso serão considerados como violações de limite
- `LINK_HISTERESYS`: Porcentagem de histerese sobre o limite de tráfego. Por exemplo, em um link com velocidade de 100Mbps e limite de 80Mbps, ao atingir 80Mbps, o script irá considerar que o limite foi violado. Ao atingir 76Mbps, o script irá considerar que o limite não foi violado. Isso evita que o script fique alternando entre limite violado e não violado quando o tráfego está próximo do limite.

Prepare seu Json, vamos chamar de "hosts.json", no seguinte formato:

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

Caso as variáveis `LINK_MAX_TRAFFIC_PERCENTAGE` ou `LINK_HISTERESYS` não sejam indicadas, o script irá utilizar os valores padrões indicados no arquivo [config.py](https://github.com/PoP-PR/link-watcher/blob/main/config.py#L16)

### 2. Utilizar o módulo [irm](https://github.com/PoP-PR/link-watcher/blob/main/irm) do script para extrair as informações necessárias de uma fonte da verdade, como o netbox por exemplo

Para isso, basta **não indicar** o arquivo `hosts.json` na execução do script. Dessa forma, o script irá utilizar o módulo `irm` para extrair as informações necessárias de uma fonte da verdade.

Nesse caso, será necessário editar o arquivo `.env` com as informações necessárias para a conexão com a fonte da verdade:

```.env
IRM_HOST="<url da sua fonte da verdade>"
IRM_TOKEN="<token super secreto>"
```

Possivelmente, será necessário, adaptar para a sua fonte da verdade com o [`IRM`](https://www.networkcomputing.com/data-centers/challenge-it-infrastructure-resource-management) que você utiliza.

O PoP-PR utiliza o [Netbox](https://docs.netbox.dev/en/stable) como fonte da verdade, e o script já está adaptado para utilizar ele. Existe um exemplo de como utilizar o irm do netbox no arquivo [netbox.py.sample](https://github.com/PoP-PR/link-watcher/blob/main/irm/netbox.py.sample)

***

### Build

Para construir a imagem docker do script, basta executar:

```bash
docker build -t link-watcher .
```

***

## Execução

Para usar o script, basta executar:

```bash
docker compose -f docker-compose-prod.yml up watcher
```

Um container será criado e irá executar [main.py](https://github.com/PoP-PR/link-watcher/blob/main/main.py) com os parametros passados em [Dockerfile](https://github.com/PoP-PR/link-watcher/blob/main/Dockerfile#L15) e [docker-compose-prod.yml](https://github.com/PoP-PR/link-watcher/blob/main/docker-compose-prod.yml#L18)

***

## Output

Ao fim da execução, o script irá criar um arquivo json no local indicado através da flag `-o` no [Dockerfile](https://github.com/PoP-PR/link-watcher/blob/main/Dockerfile#L15) com uma lista de relatórios para cada link no seguinte formato:

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
                  "total_exceeded": 50,
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

## Como o PoP-PR utiliza o script

Nosso script é executado diariamente através de um cronjob em um dos servidores do PoP-PR. Um sample do cronjob pode ser encontrado em [link-watcher.cron.sample](https://github.com/PoP-PR/link-watcher/blob/main/cron/link-watcher.cron.sample).

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

A única diferença entre eles é qual serviço do docker-compose será executado.

***

### Relatórios

Os relatórios gerados diariamente ficam armazenados no volume do container junto com arquivo de logs em `<caminho do projeto>/volumes/watcher/`.

### Alertas

**Esse script será depreciado em breve.** Nas próximas versões, o alerta será um módulo do script principal. Facilitando a manutenção, configuração e criação de novos módulos de alerta.

O script `alert.py` serve para nos avisar toda semana sobre links que estão com tráfego acima do limite configurado. Ele também é executado através de um cronjob.

Help do script:

```bash
usage: alert.py [-h] -d DIRECTORY [-n NUMBER] [-f FILE]

a cronjob to be executed every monday, checking if given links have exceeded its traffic limits in the
last 7 days

options:
  -h, --help                              show this help message and exit
  -d <dir Path>, --directory <dir Path>   directory where the json files are stored
  -n <number>, --number <number>          number of files/days to be checked
  -f <file>, --file <file>                json file with the configuration
```

Caso você também utilize o [Alerta](https://docs.alerta.io/quick-start.html), basta configurar as variáveis no seu [`.env`](https://github.com/PoP-PR/link-watcher/blob/main/watcher.env.sample).

Caso contrário, você pode criar um script para enviar os alertas da forma que preferir.

***

## Roadmap

- [X] criar módulos para extrair informações de fontes da verdade. Ex.: netbox, CMDB, etc.
- [x] gerar o arquivo de configuração `input.json` sempre após a execução do script
- [ ] cuidar com mais de um circuito em um site
- [ ] separar a main em input, processamento e output
- [ ] modularizar estas 3 etapas
- [ ] usar o padrão de projeto strategy para modularizar as fontes da verdade e bases de dados
- [ ] adicionar healthcheck
- [ ] adicionar testes unitários
- [ ] adicionar testes de integração
