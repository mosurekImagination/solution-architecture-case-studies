# Case Study 01: Simple Web Application Architecture

This case study demonstrates a basic web application architecture using AWS services.

## Getting Started

1. **Fill out the Architecture Questionnaire** - Start by completing [`architecture-questionnaire.md`](architecture-questionnaire.md) to gather all requirements and context for your solution.

2. **Review the Architecture Document** - Use [`solution-architecture-template.md`](solution-architecture-template.md) as a template to document your architecture based on the questionnaire answers.

3. **Generate Diagrams** - Create Python scripts to visualize your architecture and run `./generate-diagrams.sh 01` from the project root.

## Architecture Overview

The architecture includes:
- **Users** accessing the application
- **CloudFront CDN** for content delivery
- **Application Load Balancer** distributing traffic
- **Multiple EC2 instances** running web servers
- **RDS PostgreSQL** database for data storage
- **S3** for file storage

## Diagram

The diagram is generated automatically when you run the main generation script from the project root.
