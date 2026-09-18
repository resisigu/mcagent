# MineAgent Athletics
Minecraft 1.21.1 NeoForge mod + Python bridge for a general-purpose parkour/athletics AI.

GitHub Actions builds the mod with Java 21 and Gradle 8.10.2. The built JAR is uploaded as an Actions artifact.

Bridge: GET /health, GET /state, POST /mode, POST /control on 127.0.0.1:18765.
Modes: off, learning, play.
Learning data is JSONL under the Minecraft game directory at mineagent/datasets.