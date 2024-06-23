# servicenow-kb-copilot
A natural language interface for creating and managing ServiceNow Knowledge Base articles using AI. Integrates OpenAI for content generation, CosmosDB for vector search, and ServiceNow API for KB management.

# Phase 1 Project Setup

## Setup Costmos DB Emulator

docker pull mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:mongodb

docker images

docker run \
    --detach \
    --publish 8081:8081 \
    --publish 10250:10250 \
    --env AZURE_COSMOS_EMULATOR_ENABLE_MONGODB_ENDPOINT=4.0 \
    mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:mongodb
sudo firewall-cmd --zone=public --add-port=8081/tcp --permanent
sudo firewall-cmd --zone=public --add-port=10250/tcp --permanent


https://localhost:8081/_explorer/index.html

curl -k https://localhost:8081/_explorer/emulator.pem > ~/emulatorcert.crt

pip install pymongo

import pymongo

client = pymongo.MongoClient(
    host=(
        "mongodb://localhost:C2y6yDjf5%2FR%2Bob0N8A7Cgv30VRDJIWEHLM%2B4QDU5DE2"
        "nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw%2FJw%3D%3D@localhost:10255/a"
        "dmin?ssl=true"
    ),
    tls=True,
)

client = pymongo.MongoClient(
    host=(
        "mongodb://localhost:C2y6yDjf5%2FR%2Bob0N8A7Cgv30VRDJIWEHLM%2B4QDU5DE2"
        "nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw%2FJw%3D%3D@localhost:10255/a"
        "dmin?ssl=true"
    ),
    tls=True,
)
