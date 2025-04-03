# AI Paperclips

This is a toy project exploring the possibilities and capabilities of [OpenAI's Agents API](https://platform.openai.com/docs/guides/agents) and the [Model Context Protocol](https://www.anthropic.com/news/model-context-protocol).
The goal is to have an LLM-based AI Agent that plays the game of [Universal Paperclip](https://www.decisionproblem.com/paperclips/index2.html) with minimal human guidance.


## Basic Setup

1. Install docker desktop
2. Build image and run container
```
docker compose build
docker compose up
```
3. (needed on windows): install [VcXsrv](https://sourceforge.net/projects/vcxsrv/) and start it (default settings should work)