# Temperature Measurements REST Service

A Python REST API service for receiving and managing temperature measurements from multiple sensors.

## Features

- Rest Service and database for HSM

## Architecture

```mermaid
---
config:
  layout: dagre
---
flowchart TD
    %% Oberste Ebene: Sensoren & Laptop
    subgraph PC        
        Browser[Web Browser]
    end

    AU[Arduino Uno\nhsm-arduino]

    %% Raspberry Pi 5 Layer
    subgraph RaspberryPi[Raspberry Pi 5]
        Webapp[Web Application\nhsm-webapp2]
        Backend[Backend Rest Service\nhsm-backend]
        DB[Database Server\npostgres]
    end

    %% Externe Services Layer
    subgraph ExternalServices[External Services]
        OW[Open Weather Service]
    end

    %% Internet als eigene Wolke
    Internet[🌐 Internet]

    %% Verbindungen
    AU --> |JSON| Backend
    Browser --> |HTTP| Webapp
    Webapp --> Backend
    Backend --> DB
    Backend --> Internet
    Internet --> |JSON| OW

    %% Styling
    style AU fill:#c8facc,stroke:#333,stroke-width:1px
    style Browser fill:#cce5ff,stroke:#333,stroke-width:1px
    style Webapp fill:#fff4b3,stroke:#333,stroke-width:1px
    style Backend fill:#fff4b3,stroke:#333,stroke-width:1px
    style DB fill:#fff4b3,stroke:#333,stroke-width:1px
    style Internet fill:#cce5ff,stroke:#333,stroke-width:2px,rx:20,ry:20
    style OW fill:#e0e0e0,stroke:#333,stroke-width:1px
```

## Useful DB Snippets

```
docker exec -it <sha> /bin/bash
psql -U hsmuser -d hsm

select count(*) from temperature_measurements;
select * from temperature_measurements order by timestamp desc limit 15;
select * from sensors;
```
