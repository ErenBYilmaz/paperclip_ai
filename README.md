# WIP: AI Paperclips

This is a toy project exploring the possibilities and capabilities of [OpenAI's Agents API](https://platform.openai.com/docs/guides/agents) and the [Model Context Protocol](https://www.anthropic.com/news/model-context-protocol).
The goal is to have an LLM-based AI Agent that plays the game of [Universal Paperclip](https://www.decisionproblem.com/paperclips/index2.html) with minimal human guidance.


## Basic Setup

1. Install docker (docker desktop on windows)
2. Copy `docker/secrets_template` to `docker/secrets` and add passwords to the `.txt` files inside
   - vnc_password.txt: generate a random password yourself and put it into the file
3. Copy `docker/openai.env.template` to `docker/openai.env` and put in your API key, project name and organization name
4. Build image
    ```bash
    cd docker
    docker compose build
    ```
5. (needed on windows): install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) and start it ("One large window" setting recommended)
6. (when developing in pycharm): Specify paperclip_ai service from `docker/docker-compose.yaml` as python interpreter

## Running the agent

```bash
cd docker
docker-compose up
```