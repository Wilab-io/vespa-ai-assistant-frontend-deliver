# Vespa AI Assistant Frontend

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run the application

```bash
python src/main.py
```

To also run a mock API server, use the following command:

```bash
MOCK_API=true python src/main.py
```

## Change log level

```bash
export LOG_LEVEL=DEBUG
```

## Rebuild the CSS

Go to the `src` directory and run the following command:

```bash
shad4fast build
```

If you want to watch the CSS changes, run the following command:

```bash
shad4fast watch
```

If you want to build the docker image and run the application, run the following command:

```bash
 docker compose up
```
