# Web Command

Output a command to a web browser console.

## Install

```
pip install web-command
```

## Example

```sh
web-command -s -l info -w 60 -- curl -s https://wttr.in/los-angeles
```

Browse http://localhost:8000/ to see the output.

## Usage

```
usage: web-command [-h] [-a HOST] [-p PORT] [-s] [-l LEVEL] [-w WAIT_TIME]
                   [-V]
                   [COMMAND [COMMAND ...]]

Output a command to a web browser.

positional arguments:
  COMMAND               command to run (default: None)

optional arguments:
  -h, --help            show this help message and exit
  -a HOST, --host HOST  host to bind to (default: localhost)
  -p PORT, --port PORT  port to bind to (default: 8000)
  -s, --suppress-output
                        suppress output (default: False)
  -l LEVEL, --log-level LEVEL
                        log level (default: none)
  -w WAIT_TIME, --wait-time WAIT_TIME
                        seconds to wait before restarting command (default: 5)
  -V, --version         show version and exit (default: False)
```

## Development

```sh
git clone https://github.com/vjagaro/web-command.git
cd web-command-server
poetry install
npm install
npm run build
```

To build and publish:

```sh
poetry build
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi
# In another virtual environment:
pip install --index-url https://test.pypi.org/simple/ web-command
# If this looks good...
poetry publish
```
