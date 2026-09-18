# MineAgent Athletics
Minecraft 1.21.1 NeoForge mod + Python bridge for a general-purpose parkour/athletics AI.

## Project information
- Author: **vister000**
- Website: https://vis0.top
- GitHub: https://github.com/resisigu
- Minecraft: **1.21.1**
- Mod Loader: **NeoForge**
- License: **MIT**
- Status: Independent, unofficial Minecraft mod

MineAgent Athletics is an unofficial Minecraft mod and is not affiliated with Mojang or Microsoft.

## Features
- General-purpose Minecraft parkour/athletics AI bridge
- Learning mode for recording human movement and course data
- Play mode for Python-controlled movement
- Localhost bridge between Minecraft and Python

## Bridge API
The local bridge listens on `127.0.0.1:18765`.

- `GET /health`
- `GET /state`
- `POST /mode`
- `POST /control`

Modes: `off`, `learning`, `play`.

Learning data is JSONL under the Minecraft game directory at `mineagent/datasets`.

## Build
GitHub Actions builds the mod with Java 21 and Gradle 8.10.2. The built JAR is uploaded as an Actions artifact.

## Credits
Developed by **vister000**.

MineAgent Athletics uses NeoForge and Minecraft APIs. See their respective projects and licenses for applicable terms.

## License
This project is licensed under the MIT License.
