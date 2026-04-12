# Moacyr

Moacyr is a multipurpose Discord bot in early development stage, written in Python 3 and based on the discord.py
library.

[Invite to Server](https://discord.com/oauth2/authorize?client_id=1117573431202947082&permissions=274878285888&integration_type=0&scope=bot)

## Features

- Execute code in many popular languages
- Create user binds to easily save text snippets
- Integration with Steam Community and Workshop
- Find an anime by uploading one of its frames.
- Other minor commands

More will be added later on. Feel free to suggest new features.

## Hosting

### Prerequisites

First, you will need to create a Discord bot. Fortunately, discord.py already has
an [uncomplicated tutorial](https://discordpy.readthedocs.io/en/stable/discord.html) for this.

### Environment Variables

The project also supports .env files for environment configuration. Set up the following environment variables in your
system in order to proceed, note that some are optional.

| Variable    | Description                              |
|-------------|------------------------------------------|
| BOT_TOKEN   | The Discord bot auth token. _(Required)_ |
| STEAM_KEY   | A Steam Web API key.                     |
| LOG_GUILD   | The log guild ID.                        |
| LOG_CHANNEL | The log channel ID.                      |

### Native Installation

You will need Python 3.14 or later on your machine. Project dependencies and the virtual environment must be managed
using the [uv](https://docs.astral.sh/uv/) package/project manager.

```bash
uv run main.py
```

### Containerized Installation

Alternatively, a preconfigured Dockerfile is available for a quicker setup. It should be compatible with both Docker and
Podman.

``` bash
# Building the image
podman build --tag moacyr:3.14 .

# Running
# Replace "token_here" with the actual token
podman run --name moacyr --env BOT_TOKEN=token_here moacyr:3.14
```

If you're using Docker, simply replace `podman` with `docker` in the above commands.

## Web APIs Credits

- [Steam](https://steamcommunity.com/dev/) - General communication with Steam.
- [Wandbox](https://github.com/melpon/wandbox) - Code running in many languages.
- [Trace.moe](https://soruly.github.io/trace.moe-api/) - Anime frame searching.