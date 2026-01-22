"""
Tourist Mobile Application - Option 2: Progressive Build (RECOMMENDED)
Timeline: MVP in 4 months, full features in 7 months
Budget: $719k CAPEX, $1,810-$2,260/mo OPEX
Regions: US + China from day 1
Features: MVP + payments + loyalty + partner portal
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

with Diagram("Option 2: Progressive Build - US + China (RECOMMENDED)", 
             filename="01/diagrams/option-2-progressive",
             direction="TB",
             graph_attr=graph_attr,
             node_attr=node_attr,
             edge_attr=edge_attr,
             show=False):
    
    # Users
    mobile_users = Users("Mobile Users\n(iOS/Android)\nUS + China")
    
    # DNS
    dns = Route53("Route 53\nGlobal routing\nMulti-region")
    
    with Cluster("CDN Layer"):
        cdn_us = CloudFront("CloudFront\nUS/Global CDN")
        cdn_china = React("Alibaba CDN\nChina CDN\n(Great Firewall)")
    
    with Cluster("AWS US-EAST-1 Region"):
        alb_us = ALB("ALB\nUS Region")
        
        with Cluster("Compute Layer"):
            with Cluster("Modular Monolith\n(Simpler ops, clear boundaries)"):
                api_tasks_us = [
                    ECS("API Task 1\nUser Mgmt"),
                    ECS("API Task 2\nPartner Mgmt"),
                    ECS("API Task 3\nRecommendations")
                ]
            
            with Cluster("AR Microservice\n(Isolate AI workload, independent scaling)"):
                ar_lambda_us = Lambda("Photo Recognition\nLambda")
                ar_queue_us = SQS("Recognition Queue")
            
            with Cluster("Payment & Loyalty\n(Phase 2 addition)"):
                payment_lambda = Lambda("Payment\nProcessor\n(Stripe)")
                loyalty_lambda = Lambda("Loyalty\nPoints Engine")
        
        with Cluster("Data Layer"):
            db_us = RDS("PostgreSQL Primary\ndb.t4g.xlarge\n500GB\nUS data")
            db_us_read = RDS("Read Replica\nUS Region")
            cache_us = ElastiCache("Redis\nSessions & cache\n10GB")
            s3_photos = S3("S3 Photos\nUS users")
            
        with Cluster("Event & Messaging"):
            eventbridge = React("EventBridge\nEvent-driven flows")
            sns = SNS("SNS\nPush notifications")
        
        cloudwatch_us = Cloudwatch("CloudWatch\nLogs & metrics")
    
    with Cluster("AWS CN-NORTH-1 Region (China)"):
        alb_cn = ALB("ALB\nChina Region\n(Data residency)")
        
        with Cluster("Compute Layer"):
            with Cluster("Modular Monolith"):
                api_tasks_cn = [
                    ECS("API Task 1\nUser Mgmt"),
                    ECS("API Task 2\nPartner Mgmt"),
                    ECS("API Task 3\nRecommendations")
                ]
            
            with Cluster("AR Microservice"):
                ar_lambda_cn = Lambda("Photo Recognition\nLambda")
                ar_queue_cn = SQS("Recognition Queue")
        
        with Cluster("Data Layer"):
            db_cn = RDS("PostgreSQL\ndb.t4g.xlarge\n500GB\nChina data")
            cache_cn = ElastiCache("Redis\n10GB")
            s3_photos_cn = S3("S3 Photos\nChina users")
        
        cloudwatch_cn = Cloudwatch("CloudWatch\nChina logs")
    
    with Cluster("Cross-Region Replication"):
        replication = React("Async Replication\nRead-only data\nRPO: 15 min\nEventual consistency")
    
    with Cluster("Authentication"):
        auth = Cognito("AWS Cognito\nOAuth 2.0/OIDC")
    
    with Cluster("External Services"):
        with Cluster("AI Services"):
            google_vision = React("Google Vision\nAPI")
            openai = React("OpenAI\nGPT-4 Vision")
            gemini = React("Google Gemini\nFallback")
        
        with Cluster("3rd Party (Phase 2)"):
            stripe = React("Stripe\nPayment Gateway\nPCI-DSS L2")
            email = React("SendGrid\nTransactional")
            maps = React("Google Maps\nGeolocation")
    
    # User flows
    mobile_users >> Edge(label="HTTPS\nTLS 1.3") >> dns
    dns >> Edge(label="Route to US\nCDN") >> cdn_us >> alb_us
    dns >> Edge(label="Route to China\nCDN") >> cdn_china >> alb_cn
    
    # US Region flows
    alb_us >> Edge(label="Route tasks\nhealth checks") >> api_tasks_us[0]
    alb_us >> Edge(label="JWT validation") >> auth
    
    api_tasks_us[0] >> Edge(label="Upload photo") >> s3_photos
    s3_photos >> Edge(label="S3 trigger") >> ar_queue_us
    ar_queue_us >> ar_lambda_us
    ar_lambda_us >> Edge(label="Landmark detect") >> google_vision
    ar_lambda_us >> Edge(label="Generate description") >> openai
    ar_lambda_us >> Edge(label="Fallback") >> gemini
    
    # Payment flow (Phase 2)
    api_tasks_us[1] >> Edge(label="Process payment") >> payment_lambda
    payment_lambda >> Edge(label="Stripe API") >> stripe
    payment_lambda >> Edge(label="Update points") >> loyalty_lambda
    
    # Data connections
    api_tasks_us[0] >> Edge(label="ACID transactions") >> db_us
    api_tasks_us[0] >> Edge(label="Read replica\noffload") >> db_us_read
    api_tasks_us[0] >> Edge(label="Cache hot data") >> cache_us
    
    # Event-driven
    api_tasks_us[0] >> Edge(label="Events") >> eventbridge
    eventbridge >> Edge(label="Publish") >> sns
    
    # China Region flows
    alb_cn >> Edge(label="Route tasks") >> api_tasks_cn[0]
    alb_cn >> Edge(label="JWT validation") >> auth
    
    api_tasks_cn[0] >> Edge(label="Upload photo") >> s3_photos_cn
    s3_photos_cn >> Edge(label="S3 trigger") >> ar_queue_cn
    ar_queue_cn >> ar_lambda_cn
    ar_lambda_cn >> Edge(label="Landmark detect") >> google_vision
    ar_lambda_cn >> Edge(label="Generate description") >> openai
    
    api_tasks_cn[0] >> Edge(label="ACID transactions") >> db_cn
    api_tasks_cn[0] >> Edge(label="Cache hot data") >> cache_cn
    
    # Cross-region replication
    db_us >> Edge(label="Replicate read-only\ndata (allowed)") >> replication >> db_cn
    
    # Monitoring
    api_tasks_us[0] >> Edge(label="Structured logs") >> cloudwatch_us
    ar_lambda_us >> Edge(label="Execution logs") >> cloudwatch_us
    api_tasks_cn[0] >> Edge(label="Structured logs") >> cloudwatch_cn
    ar_lambda_cn >> Edge(label="Execution logs") >> cloudwatch_cn
    
    cloudwatch_us >> Edge(label="Alert if\nerror rate >5%") >> Slack("Slack\nAlerts")
    
    # External services
    api_tasks_us[0] >> Edge(label="Send emails") >> email
    api_tasks_us[0] >> Edge(label="POI data") >> maps
