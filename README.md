# DESP-AAS Project Management


## Table of Contents

- [Introduction](#Introduction)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [Deployment](#deployment)
- [License](#license)
- [Support](#support)

## Introduction

###  What is the DESP-AAS Collaborative?


### What is the Moderation microservice?

The Moderation microservice is a core component of the DESP-AAS Collaborative platform that handles content moderation and validation. It provides automated and manual review capabilities to ensure content quality, compliance, and safety across the platform.

**Key Features:**
- **API Integration**: RESTful API endpoints for seamless integration with other microservices

**Use Cases:**
- Reviewing user-generated content before publication
- Filtering inappropriate or non-compliant materials
- Ensuring data quality and consistency
- Supporting community guidelines enforcement


## Prerequisites

Before you begin, ensure you have the following installed:
- **Git** 
- **Docker** Docker is mainly used for the test suite, but can also be used to deploy the project via docker compose

## Installation

1. Clone the repository:
```bash
git clone https://github.com/acri-st/DESPAAS-moderation.git moderation
cd moderation
```

## Development

## Development Mode

### Standard local development

Setup environment
```bash
make setup
```

Start the development server:
```bash
make start
```

To clean the project and remove node_modules and other generated files, use:
```bash
make clean
```

## Contributing

Check out the **CONTRIBUTING.md** for more details on how to contribute.