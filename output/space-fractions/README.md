# Space Fractions - Project Documentation

## Executive Summary
The Space Fractions system is a web-based, interactive learning tool designed to improve fraction-solving skills for sixth-grade students. The system consists of an introductory movie, a main menu, a series of fraction questions, and an ending scene with feedback. The architecture follows a microservices approach, with separate components for the game logic, question management, and user interface. The system is deployed on a cloud-based infrastructure, ensuring scalability and availability.

### Top 3 Design Risks & Mitigations
| Risk | Mitigation |
| --- | --- |
| 1. Scalability issues | Implement load balancing and autoscaling |
| 2. Security vulnerabilities | Implement encryption and secure authentication |
| 3. Data loss | Implement regular backups and data replication |

### QA Coverage Mapping
| ASR/NFR ID | Test Type |
| --- | --- |
| ASR-1 (data durability) | Unit testing, Integration testing |
| NFR-1 (performance) | Load testing, Stress testing |
| ASR-2 (security) | Penetration testing, Vulnerability scanning |

---

## Traceability & Rationale
| Requirement ID | Short Text | Diagram(s) | Component(s) | Artifact filename(s) | Rationale |
| --- | --- | --- | --- | --- | --- |
| FR-1 | Play game | UseCaseDiagram | GameComponent | openapi.yaml | Allows users to play the game |
| NFR-1 | Performance | SequenceDiagram1 | GameComponent | internal.proto | Ensures the game responds quickly to user input |
| ASR-1 | Data durability | DeploymentDiagram | QuestionComponent | sql/question_ddl.sql | Ensures that question data is persisted and recoverable |

---

## Architecture Overview
The Space Fractions system consists of the following components:
* **GameComponent**: responsible for game logic and user interaction
* **QuestionComponent**: responsible for question management and data persistence
* **UserComponent**: responsible for user authentication and authorization

### Technology Options & Stack
* **Language/runtime**: Node.js 18-20 (Justification: meets ASR-1 data durability)
* **Web framework**: Express.js 4-5 (Justification: meets NFR-1 performance)
* **RPC/HTTP**: RESTful API / gRPC (Justification: meets ASR-2 security)
* **Persistence**: PostgreSQL 14-15 (Justification: meets ASR-1 data durability)
* **Cache**: Redis 6-7 (Justification: meets NFR-1 performance)
* **Messaging**: RabbitMQ 3-4 (Justification: meets ASR-2 security)
* **Search**: Elasticsearch 7-8 (Justification: meets NFR-1 performance)
* **Authn/authz**: OAuth2 (Justification: meets ASR-2 security)
* **Observability**: Prometheus 2-3 (Justification: meets NFR-1 performance)
* **CI/CD**: Jenkins 2-3 (Justification: meets ASR-1 data durability)
* **Container runtime**: Docker 20-21 (Justification: meets ASR-1 data durability)
* **Infra provisioning**: Terraform 1-2 (Justification: meets ASR-1 data durability)

---

## API Specifications

### External API (OpenAPI 3.0)
```yml
openapi: 3.0.0
info:
  title: Space Fractions API
  description: API for the Space Fractions game
  version: 1.0.0
paths:
  /play:
    get:
      summary: Play the game
      responses:
        200:
          description: Game started
          content:
            application/json:
              schema:
                type: object
                properties:
                  gameId:
                    type: integer
                    description: Game ID
```

### Internal API (Protobuf)
```proto
syntax = "proto3";
package spacefractions;

service GameService {
  rpc Play(PlayRequest) returns (PlayResponse) {}
}

message PlayRequest {
  int32 gameId = 1;
}

message PlayResponse {
  int32 gameId = 1;
}
```

---

## Database Schemas (SQL DDL)

```sql
CREATE TABLE games (
  id SERIAL PRIMARY KEY,
  game_state JSONB NOT NULL
);
```

---

## Operations & Deployment

### Kubernetes Deployment Configuration
```yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spacefractions
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spacefractions
  template:
    metadata:
      labels:
        app: spacefractions
    spec:
      containers:
      - name: spacefractions
        image: spacefractions:latest
        ports:
        - containerPort: 80
```

---

## Testing Strategy

### Test Matrix
| Test Type | GameComponent | QuestionComponent |
| --- | --- | --- |
| Unit testing | Planned | Planned |
| Integration testing | Planned | Planned |
| Contract testing | Planned | Planned |
| E2E testing | Planned | Planned |
| Chaos testing | Planned | Planned |

### Compatibility & Migration
* Implement backwards compatibility for public APIs for 1 year.
* Use a migration window of 1 month for breaking changes.

---

## Deliverables Manifest
* `architecture.md`
* `openapi.yaml`
* `internal.proto`
* `k8s/spacefractions-deployment.yaml`
* `sql/game_ddl.sql`
* `sql/question_ddl.sql`
* `traceability_matrix.csv`
