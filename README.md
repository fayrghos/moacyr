# Moacyr

Moacyr is a multipurpose Discord bot in early development stage, written in Python 3 and based on the discord.py library.

[Invite to Server](https://discord.com/oauth2/authorize?client_id=1117573431202947082&permissions=274878285888&integration_type=0&scope=bot) | [Command List](https://fayrghos.github.io/moacyr-web/commands)

## Features
- Execute code in many popular languages
- Create user binds to easily save text snippets
- Integration with Steam Community and Workshop
- Find an anime by uploading one of its frames.
- Other minor commands

More will be added later on. Feel free to suggest new features.

## Hosting
### Prerequisites
First, you will need to create a Discord bot. Fortunately, discord.py already has an [uncomplicated tutorial](https://discordpy.readthedocs.io/en/stable/discord.html) for this.

### Environment Variables
Set up the following environment variables in your system in order to proceed. Note that some are optional.

|Variable|Description|
|--|--|
|BOT_TOKEN|The Discord bot auth token. _(Required)_|
|STEAM_KEY|A Steam Web API key.|
|LOG_GUILD| The log guild ID.|
|LOG_CHANNEL| The log channel ID.|

> [!TIP]
> The project also supports .env files for environment configuration.

### Native Installation
You can simply install Python 3.12 (or later) along with the project dependencies. I highly recommend creating a [Virtual Environment](https://docs.python.org/3/library/venv.html), especially in Linux environments.

```bash
# Installing dependencies
pip install -r requirements.txt

# Running
python main.py
```

### Containerized Installation
Alternatively, a preconfigured Dockerfile is available for a quicker setup. It should be compatible with both Docker and Podman.

``` bash
# Building the image
docker build --tag moacyr:3.12 .

# Running
# Replace "token_here" with the actual token
docker run --name moacyr --env BOT_TOKEN=token_here moacyr:3.12
```
If you're using Podman, simply replace `docker` with `podman` in the above commands.

## Web APIs Credits
- [Steam](https://steamcommunity.com/dev/) - General communication with Steam.
- [Wandbox](https://github.com/melpon/wandbox) - Code running in many languages.
- [Trace.moe](https://soruly.github.io/trace.moe-api/) - Anime frame searching.