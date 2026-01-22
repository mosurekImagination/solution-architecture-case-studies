"""
Tourist Mobile Application - Option 1 MVP Architecture
Timeline: 4 months
Budget: $224k CAPEX, $835/mo OPEX
Region: US only
Features: Basic photo recognition, simple partner recommendations
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Fargate, Lambda
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.storage import S3
from diagrams.aws.network import CloudFront, ALB, Route53
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import Cognito
from diagrams.onprem.client import Users
from diagrams.programming.framework import React
from diagrams.saas.chat import Slack

# Custom attributes for better layout
graph_attr = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "2.0",
    "splines": "ortho",
    "rankdir": "TB",
    "ranksep": "2.5",
    "nodesep": "1.5",
    "concentrate": "true",
    "compound": "true",
    "sep": "0.5"
}

node_attr = {
    "fontsize": "11"
}

edge_attr = {
    "fontsize": "10"
}

with Diagram("Option 1: MVP Architecture (US Only)", 
             filename="01/diagrams/option-1-mvp",
             direction="TB",
             graph_attr=graph_attr,
             node_attr=node_attr,
             edge_attr=edge_attr,
             show=False):
    
    # Users
    mobile_users = Users("Mobile Users\n(iOS/Android)\nPrimary interface")
    
    # DNS
    dns = Route53("Route 53\nDNS\nGlobal routing")
    
    # CDN
    cdn = CloudFront("CloudFront CDN\nCache static content\nReduce latency")
    
    with Cluster("AWS US-EAST-1 Region"):
        
        # Load Balancer
        alb = ALB("Application LB\nHTTPS termination\nHealth checks")
        
        with Cluster("Compute Layer"):
            with Cluster("Modular Monolith\n(Simpler ops, clear boundaries)"):
                api_tasks = [
                    ECS("API Task 1\nUser Mgmt\nAuth & profiles"),
                    ECS("API Task 2\nPartner Mgmt\nBusiness profiles"),
                    ECS("API Task 3\nRecommendations\nGeo queries")
                ]
            
            with Cluster("AR Microservice\n(Isolate AI workload, independent scaling)"):
                ar_lambda = Lambda("Photo Recognition\nLambda\nOn-demand scaling")
                ar_queue = SQS("Recognition Queue\nDecouple uploads\nRetry safety")
        
        with Cluster("Data Layer"):
            # Primary Database
            db_primary = RDS("PostgreSQL Primary\ndb.t4g.large 100GB\nACID for payments\nPostGIS for geo")
            
            # Cache
            cache = ElastiCache("Redis Cache 5GB\nSessions & hot data\n80%+ hit ratio target")
            
            # Object Storage
            s3_photos = S3("S3 Photos\nUser uploads\nDurable & scalable")
            s3_static = S3("S3 Static Assets\nImages & configs\nCDN origin")
        
        with Cluster("Monitoring & Logging"):
            cloudwatch = Cloudwatch("CloudWatch\nCentralized logs\nMetrics & alerts")
            alerts = Slack("Slack Alerts\nHigh priority\n15-min response")
    
    with Cluster("Authentication"):
        auth_service = Cognito("AWS Cognito\nOAuth 2.0/OIDC\nSocial + email login")
    
    with Cluster("External Services"):
        with Cluster("AI Services\n(Multi-provider resilience)"):
            google_vision = React("Google Vision API\nFast landmark detect\n~$1/1000 images")
            openai = React("OpenAI GPT-4 Vision\nPrimary LLM\nRich descriptions")
            gemini = React("Google Gemini\nSecondary fallback\nRedundancy")
        
        with Cluster("3rd Party Services"):
            email = React("SendGrid\nTransactional emails\nReceipts & notifs")
            maps = React("Google Maps API\nGeolocation\nPOI data")
    
    # User flows
    mobile_users >> Edge(label="HTTPS only\nTLS 1.3") >> dns >> cdn >> alb
    
    # API Gateway to services
    alb >> Edge(label="Route to tasks\nhealth checks") >> api_tasks[0]
    alb >> Edge(label="JWT validation") >> auth_service
    
    # Photo Recognition Flow
    api_tasks[0] >> Edge(label="Upload photo") >> s3_photos
    s3_photos >> Edge(label="S3 event trigger") >> ar_queue
    ar_queue >> Edge(label="Process async") >> ar_lambda
    ar_lambda >> Edge(label="1. Quick landmark\ndetection") >> google_vision
    ar_lambda >> Edge(label="2. Generate rich\ndescription") >> openai
    ar_lambda >> Edge(label="3. Fallback if\nOpenAI fails") >> gemini
    
    # Data Layer connections
    api_tasks[0] >> Edge(label="ACID transactions\npayments") >> db_primary
    api_tasks[0] >> Edge(label="Hot data\noffload reads") >> cache
    api_tasks[0] >> Edge(label="Serve assets") >> s3_static
    
    # Partner recommendations - separate path
    api_tasks[1] >> Edge(label="PostGIS geo\nqueries") >> db_primary
    api_tasks[1] >> Edge(label="Cache popular\nresults") >> cache
    
    # External services - separate path
    api_tasks[2] >> Edge(label="Receipts\nnotifications") >> email
    api_tasks[2] >> Edge(label="POI data\nrouting") >> maps
    
    # Monitoring
    api_tasks[0] >> Edge(label="Structured JSON\ncorrelation IDs") >> cloudwatch
    ar_lambda >> Edge(label="Execution logs\nerrors") >> cloudwatch
    cloudwatch >> Edge(label="Error rate >5%\nlatency p99 >5s") >> alerts
    
    # CDN caching
    cdn >> Edge(label="Cache static\nreduce origin load") >> s3_static
