#!/usr/bin/env python3
"""
Simple demo diagram using the diagrams library.
This script creates a basic web application architecture diagram.
"""

import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3
from diagrams.aws.network import CloudFront, ALB
from diagrams.onprem.client import Users

# Determine output directory (use OUTPUT_DIR env var if set, otherwise current directory)
output_dir = os.getenv("OUTPUT_DIR", ".")
if output_dir != ".":
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, "demo_diagram")
else:
    filename = "demo_diagram"

# Create a diagram with a descriptive name
# show=False means it won't open automatically, just save the file
with Diagram("Simple Web Application Architecture", filename=filename, show=False, direction="LR"):
    
    # Users accessing the application
    users = Users("Users")
    
    # Content Delivery Network
    cdn = CloudFront("CDN")
    
    # Load Balancer
    with Cluster("Application Layer"):
        alb = ALB("Load Balancer")
        
        # Web servers
        web1 = EC2("Web Server 1")
        web2 = EC2("Web Server 2")
        
        alb >> web1
        alb >> web2
    
    # Database
    with Cluster("Data Layer"):
        db = RDS("PostgreSQL Database")
    
    # Storage
    storage = S3("File Storage")
    
    # Connect the components
    users >> cdn >> alb
    web1 >> db
    web2 >> db
    web1 >> storage
    web2 >> storage

output_path = os.path.join(output_dir, "demo_diagram.png") if output_dir != "." else "demo_diagram.png"
print(f"Diagram generated successfully! Check '{output_path}'")
