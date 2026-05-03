# Moacyr

A multipurpose Discord bot built with Python 3 and the discord.py library.

[Invite Application](https://discord.com/oauth2/authorize?client_id=1117573431202947082&permissions=274878285888&integration_type=0&scope=bot)

## Features

- Run code in many popular languages
- Create user binds to save text snippets
- Integrate with Steam Community and Workshop
- Find anime scenes by uploading a frame
- Use additional utility commands

## Self-Hosting

### Prerequisites

First, you will need to create a Discord bot and invite it to your server. Fortunately, discord.py already has an [uncomplicated tutorial](https://discordpy.readthedocs.io/en/stable/discord.html) for this.

### Environment Variables

The project also supports .env files for environment configuration. Set up the following environment variables in your
system in order to proceed, note that variables marked with "\*" are mandatory.

| Variable    | Description                       | Default |
| ----------- | --------------------------------- | ------- |
| BOT_TOKEN\* | The Discord bot auth token.       |         |
| STEAM_KEY   | A Steam Web API key.              |         |
| DB_PATH\*   | The path for the SQLite database. | ./data/ |

### Native Installation

You will need Python 3.14 or later on your machine. Project dependencies and the virtual environment must be managed
using the [uv](https://docs.astral.sh/uv/) package/project manager.

```bash
uv run main.py
```

### Containerized Installation

Alternatively, a preconfigured Dockerfile is available for a quicker setup. It should be compatible with both Docker and
Podman.

```bash
# Building the image
podman build --tag moacyr:3.14 .

# Running
# Replace "token_here" with the actual token
podman run --name moacyr --env BOT_TOKEN=token_here moacyr:3.14
```

If you're using Docker, simply replace `podman` with `docker` in the above commands.

## Third-Party APIs

Some features rely on third-party web APIs. The services used are listed below.

- [Steam](https://steamcommunity.com/dev/) - Platform and community integration.
- [Wandbox](https://github.com/melpon/wandbox) - Multi-language code execution.
- [trace.moe](https://soruly.github.io/trace.moe-api/) - Anime frame recognition.
