# WIP: AI Paperclips

This is a toy project exploring the possibilities and capabilities of [OpenAI's Agents API](https://platform.openai.com/docs/guides/agents) and the [Model Context Protocol](https://www.anthropic.com/news/model-context-protocol).
The goal is to have an LLM-based AI Agent that plays the game of [Universal Paperclip](https://www.decisionproblem.com/paperclips/index2.html) with minimal human guidance.


## Basic Setup

1. Install docker (docker desktop on windows)
2. Copy `docker/secrets_template` to `docker/secrets` and add passwords to the `.txt` files inside
   - browser_automation_api_key.txt: generate a random password yourself
   - openai_config.json: 
     - create API key on https://platform.openai.com
     - look up project id and organization id in your openai account on https://platform.openai.com/settings/organization/general
   - vnc_password.txt: generate a random password yourself
3. Build image and run container
    ```
    docker compose build
    docker compose up
    ```
4. (needed on windows): install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) and start it ("One large window" setting recommended)
5. (when developing in pycharm): Specify paperclip_ai service from `docker/docker-compose.yaml` as python interpreter