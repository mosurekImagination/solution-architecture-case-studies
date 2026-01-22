"""
Tourist Mobile Application - Option 3: Start Big - All Features Day 1
Timeline: 10 months to full launch
Budget: $2.17M CAPEX, $4,665/mo OPEX
Regions: US + China + EU ready
Features: Complete platform with all features from day 1
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Fargate, Lambda
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.storage import S3
from diagrams.aws.network import CloudFront, ALB, Route53, APIGateway
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import Cognito, WAF
from diagrams.onprem.client import Users
from diagrams.programming.framework import React
from diagrams.saas.chat import Slack

# Custom attributes for better layout
graph_attr = {
    "fontsize": "13",
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
    "fontsize": "10"
}

edge_attr = {
    "fontsize": "9"
}

with Diagram("Option 3: All Features Day 1 - Complete Platform", 
             filename="01/diagrams/option-3-all-features",
             direction="TB",
             graph_attr=graph_attr,
             node_attr=node_attr,
             edge_attr=edge_attr,
             show=False):
    
    # Users
    mobile_users = Users("Mobile Users\n(iOS/Android)\nGlobal")
    
    # DNS & WAF
    dns = Route53("Route 53\nGlobal routing\nMulti-region")
    waf = WAF("WAF\nDDoS protection")
    
    with Cluster("CDN Layer"):
        cdn_global = CloudFront("CloudFront\nGlobal CDN\nAll regions")
        cdn_china = React("Alibaba CDN\nChina")
    
    with Cluster("AWS US-EAST-1 Primary Region"):
        api_gateway = APIGateway("API Gateway\nRationing & auth")
        alb = ALB("ALB\nHealthchecks")
        
        with Cluster("Microservices\n(Independent scaling)"):
            user_service = ECS("User Service\nAuth & profiles")
            partner_service = ECS("Partner Service\nBusiness mgmt")
            recommendation_svc = ECS("Recommendation\nService\nML engine")
            payment_service = ECS("Payment Service\nStripe integration")
            loyalty_service = ECS("Loyalty Service\nPoints engine")
        
        with Cluster("AI & Recognition"):
            ar_lambda = Lambda("Photo Recognition\nMulti-model")
            ar_queue = SQS("Recognition Queue")
        
        with Cluster("Data Layer"):
            db_primary = RDS("PostgreSQL Primary\ndb.r6g.2xlarge\n1TB+\nRead replicas")
            cache = ElastiCache("Redis Cluster\n20GB+\nHA mode")
            ar_timeseries = React("DynamoDB\nAR logs\n(Time-series)")
            s3 = S3("S3\nPhotos + assets")
            opensearch = React("OpenSearch\nGeo search\nFull-text")
        
        with Cluster("Analytics & Events"):
            kinesis = React("Kinesis\nReal-time streams\nUser behavior")
            analytics_db = React("Redshift\nData warehouse\nBI queries")
            eventbridge = React("EventBridge\nEvent mesh")
        
        cloudwatch = Cloudwatch("CloudWatch\nFull observability")
    
    with Cluster("AWS CN-NORTH-1 China Region"):
        alb_cn = ALB("ALB\nChina")
        
        with Cluster("Microservices"):
            user_svc_cn = ECS("User Service")
            partner_svc_cn = ECS("Partner Service")
            recommendation_svc_cn = ECS("Recommendation")
        
        with Cluster("Data Layer"):
            db_cn = RDS("PostgreSQL\n1TB+\nChina data")
            cache_cn = ElastiCache("Redis Cluster\n20GB+")
            s3_cn = S3("S3\nChina content")
            opensearch_cn = React("OpenSearch")
        
        cloudwatch_cn = Cloudwatch("CloudWatch")
    
    with Cluster("AWS EU Region (Prepared)"):
        alb_eu = ALB("ALB\nEU (GDPR ready)")
        db_eu_prep = React("PostgreSQL\n(Prepared)")
    
    with Cluster("Cross-Region"):
        replication = React("Active-Active\nAsync replication\nEventual consistency")
        dr = React("Disaster Recovery\nRPO: 15 min")
    
    with Cluster("Authentication & Security"):
        auth = Cognito("AWS Cognito\nMulti-factor")
        kms = React("KMS\nEncryption\nAES-256")
    
    with Cluster("External Services"):
        with Cluster("AI Services"):
            google_vision = React("Google Vision")
            openai = React("OpenAI\nGPT-4V")
            gemini = React("Google Gemini")
        
        with Cluster("Payments & Notifications"):
            stripe = React("Stripe\nPCI-DSS L2")
            sns = SNS("SNS\nPush/SMS")
            email = React("SendGrid")
        
        with Cluster("Services"):
            maps = React("Google Maps")
            translation = React("Google Translate")
    
    # Main user flow
    mobile_users >> Edge(label="HTTPS\nTLS 1.3") >> dns >> waf >> cdn_global >> api_gateway >> alb
    
    # Microservices
    alb >> Edge(label="Route requests") >> user_service
    alb >> Edge(label="Route requests") >> partner_service
    alb >> Edge(label="Route requests") >> recommendation_svc
    
    # Payment flow
    user_service >> Edge(label="Initiate checkout") >> payment_service
    payment_service >> Edge(label="Process card") >> stripe
    payment_service >> Edge(label="Update points") >> loyalty_service
    
    # AR flow
    user_service >> Edge(label="Upload photo") >> s3
    s3 >> Edge(label="S3 event") >> ar_queue
    ar_queue >> ar_lambda
    ar_lambda >> Edge(label="Landmark detect") >> google_vision
    ar_lambda >> Edge(label="Describe") >> openai
    ar_lambda >> Edge(label="Fallback") >> gemini
    ar_lambda >> Edge(label="Store logs") >> ar_timeseries
    
    # Data layer
    user_service >> Edge(label="ACID") >> db_primary
    partner_service >> Edge(label="ACID") >> db_primary
    recommendation_svc >> Edge(label="Geo queries") >> opensearch
    user_service >> Edge(label="Session cache") >> cache
    partner_service >> Edge(label="Cache results") >> cache
    
    # Analytics
    user_service >> Edge(label="Stream events") >> kinesis
    kinesis >> Edge(label="Real-time") >> analytics_db
    eventbridge >> Edge(label="Coordinate") >> sns
    
    # Notifications
    payment_service >> Edge(label="Send SMS") >> sns
    user_service >> Edge(label="Send email") >> email
    recommendation_svc >> Edge(label="Recommendations") >> email
    
    # Locations
    user_service >> Edge(label="POI") >> maps
    user_service >> Edge(label="i18n") >> translation
    
    # China region
    dns >> Edge(label="CN users") >> cdn_china >> alb_cn
    alb_cn >> user_svc_cn
    user_svc_cn >> db_cn
    user_svc_cn >> cache_cn
    
    # Cross-region
    db_primary >> Edge(label="Replicate") >> replication >> db_cn
    
    # Security
    alb >> Edge(label="JWT") >> auth
    user_service >> Edge(label="Encrypt secrets") >> kms
    
    # Monitoring
    user_service >> Edge(label="APM") >> cloudwatch
    ar_lambda >> Edge(label="Traces") >> cloudwatch
    cloudwatch >> Edge(label="Alert") >> Slack("Slack\nAlerts")
