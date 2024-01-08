<h1>Monitors the availability of many websites</h1>

<h2>System Design</h2>
![system design](https://viewer.diagrams.net/index.html?tags=%7B%7D&highlight=0000ff&edit=_blank&layers=1&nav=1&title=system_design.png#R7ZhLc5swEMc%2FDUdneNrJMbbTpJ10mpnMtMkpI8MaNAHkChHjfPpKIPGS4yZ%2BtBxyAi3Lgv67%2BxPIcGZJcU3RKvpOAogN2wwKw5kbtm2Z9pgfhGVTWcaeVxlCigPp1Bju8SuoO6U1xwFkHUdGSMzwqmv0SZqCzzo2RClZd92WJO4%2BdYVC0Az3Pop16y8csKiynntmY78BHEbqyZYpryRIOUtDFqGArFsm58pwZpQQVp0lxQxiIZ7SpbrvyxtX6xejkLJ33XCTRO78KwJqj749%2FXSns%2BfXkYzyguJcThjhF0if%2FBjLt2YbJQUleRqAiGYZznQdYQb3K%2BSLq2uefG6LWBLLy%2FrbqUcBZVC0TPJtr4EkwOiGuxS1ltUtsnQsV47XTSIspW7USsJY2pDMfViHbuThJ1KhD6hla2oFC00mnueVOPU3MeZ6UefvYi0qZW8XtQH5z2Gp94%2Bc8TAg7VnVH5Z3HIXti67CjqUrPN4i8PmpBHY0gTV5IQ0uRV8LhWOUZdjvatlUqclHUGD2IM7PXGsix4%2FC88ysx%2FOi5TzftAZ3QDGfGFBlS%2FkkH9qDxzK2p4ZNqHK0aY%2F6wd7MX0Zy6sMOlRQHEQ2B7fCT4kHQQZxeDa1se1uyrWwUYsQ4HbqM3VIC8gl3BPOZ1cXmmr1i67dpNW95Vxtk%2FUDeG1WrAlXCaIHKiqynvX%2BRujozg4BHopAQro5t5jTWy5Yn4RYt%2BOrYqVYU4zAVpcyLQFTGVDQv5svPpbyQ4CAQMaYUePOjRRlPlM9KTK%2BcsDc1vPn2gtrVY31K1GuofEhnmdpGj5HJm%2BjC6eTCPqxUlAtZLjM4SfI8LXkrSoLc5%2BL%2F7%2FWuRu1g1rvJnjjOeAeyj1C65mqD0kfpuYur%2ByPUfidCvU%2BEnqILz7XCEmkoyZkZ9jhm4huId%2BQ4FGc%2BBcSgTFf2PGCyqnY5mKwcrJ7rdTKkFv3hkvVCyymfdZYnAyCrO7g%2FCfVCg0Wr%2BnC2Wh%2FNMsSHPplPj%2BiLT0Sfop0tfWugYnQF4Z2MfuJIzWM2YFTX%2FXcEVtvOxB06nC39p0XLjtq4WMZQSMJMj8OgPViyPzf24EG9adcGQm08kAheb5PFNvckwqSHFmvyj4mg%2FztR%2BJ1DVlKBCElhkeFBt71qg6P8%2FDpe9%2Bd3dCAGemEOoYLYjqh3liv3Zn%2FeufoD)

System consist of 3 parts: aiven_cli, producer, consumer

<h3>aiven_cli</h3>
aiven_cli is responsible for adding/removing urls from table `url`.
```bash
usage: aiven-cli [-h] [-p PERIOD] [-r REGEX] {add,remove} url

add/remove url and regex

positional arguments:
  {add,remove}          action
  url                   valid url, for instance http://test.com

options:
  -h, --help            show this help message and exit
  -p PERIOD, --period PERIOD
                        interval between requests
  -r REGEX, --regex REGEX
                        regex, for instance .*
```

Example:
```bash
aiven_cli.py add http://test.com -p 15
```

Run in docker-compose:
```bash
docker-compose run aiven-create-db ./aiven/cli/aiven_cli.py add http://test.com -p 15
```

<h3>Producer</h3>

Producer is responsible for getting url without runs, or url with last run older than checking period.
Based on this urls, producer create task in table `task`


<h3>Consumer</h3>
Producer is responsible for getting tasks with status 0 (not started yet) from table `task`.
Based on this task consumer send request to website and save result into table `task_result`.


<h2>Start system</h2>

<h3>Environment variables</h3>
1. For service `aiven-create-db` and `aiven-cli`:
    - `DB_DSN` - db connection uri. For instance, `postgresql://user:password@random_numbers.a.aivencloud.com:26418/defaultdb?sslmode=require`.
    - `DB_TIMEOUT` - timeout for db connection and db commands. By default `5`.
    - `MIN_PERIOD` - min period between checking website. By default `5`.
    - `MAX_PERIOD` - max period between checking website. By default `300`.

2. For service `aiven-producer`
    - `DB_DSN` - db connection uri. For instance, `postgresql://user:password@random_numbers.a.aivencloud.com:26418/defaultdb?sslmode=require`.
    - `DB_TIMEOUT` - timeout for db connection and db commands. By default `5`.
    - `MIN_PERIOD` - min period between checking website. By default `5`.
    - `MAX_PERIOD` - max period between checking website. By default `300`.
    - `CONCURRENCY` - how many concurrency workers producer creates. By default `3`
    - `SLEEP_WITHOUT_TASK` - how long producer's worker will be sleep without tasks. By default `1` second.
    - `SLEEP_AFTER_EXCEPTION` - how long producer's worker will be sleep after exception during creating task. By default `1` second.

3. For service `aiven-consumer`
    - `DB_DSN` - db connection uri. For instance, `postgresql://user:password@random_numbers.a.aivencloud.com:26418/defaultdb?sslmode=require`.
    - `DB_TIMEOUT` - timeout for db connection and db commands. By default `5`.
    - `MIN_PERIOD` - min period between checking website. By default `5`.
    - `MAX_PERIOD` - max period between checking website. By default `300`.
    - `CONCURRENCY` - how many concurrency workers producer creates. By default `100`
    - `SLEEP_WITHOUT_TASK` - how long producer's worker will be sleep without tasks. By default `1` second.
    - `SLEEP_AFTER_EXCEPTION` - how long producer's worker will be sleep after exception during creating task. By default `1` second.
    - `HTTP_REQUEST_TIMEOUT` - http request timeout (for checking websites)

<h3>Start cluster</h3>
1. create file `.env_create_db` based on `template.env_create_db`
2. create file `.env_consumer` based on `template.env_consumer`
3. create file `.env_producer` based on `template.env_producer`
4. run cluster
```bash
docker-compose up --scale aiven-consumer=5
```
5. add url
```bash
docker-compose run aiven-create-db ./aiven/cli/aiven_cli.py add http://test.com
```

<h2>Useful commands</h2>

1. Run tests
```bash
docker build -f docker/Dockerfile --progress=plain --target test .
```

Current coverage:
```bash
Name                         Stmts   Miss  Cover   Missing
----------------------------------------------------------
aiven/__init__.py                0      0   100%
aiven/cli/__init__.py            0      0   100%
aiven/cli/aiven_cli.py          53      3    94%   70, 80-81
aiven/consumer/__init__.py       0      0   100%
aiven/consumer/worker.py        62      6    90%   70-74, 81, 87-88
aiven/db/__init__.py             0      0   100%
aiven/db/create_db.py           14      0   100%
aiven/db/crud.py                40      0   100%
aiven/db/db.py                  15      0   100%
aiven/producer/__init__.py       0      0   100%
aiven/producer/worker.py        34      3    91%   40, 46-47
conf/__init__.py                 0      0   100%
conf/config.py                   7      0   100%
conf/config_consumer.py          7      0   100%
conf/config_producer.py          6      0   100%
----------------------------------------------------------
TOTAL                          238     12    95%
```

2. Run flake
```bash
docker build -f docker/Dockerfile --progress=plain --target flake .
```

3. Add pre-commit hook
```bash
pre-commit install
```

<h2>TODO</h2>
1. Add different metrics such as: amount of tasks in queue, amount of urls, amount of tasks results with `status` != 2XX etc.
2. Add notification (via slack/email) about exceptions
3. Add Sentry
4. Add ELK
5. Add batching (consumer has to fetch a batch of tasks instead of fetching 1 by 1)

