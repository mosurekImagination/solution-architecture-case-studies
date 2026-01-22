"""
Tourist Mobile Application - Option 4: Target Scale (Klook/Viator Level)
Timeline: Year 4-5 to reach scale
Budget: $1.22M migration + $130k/mo OPEX
Scale: 50M+ users, 10k+ QPS, full microservices, global multi-region
"""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.storage import S3
from diagrams.aws.network import CloudFront, Route53, APIGateway
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.management import Cloudwatch
from diagrams.aws.security import Cognito, WAF, Shield
from diagrams.onprem.client import Users
from diagrams.onprem.inmemory import Redis
from diagrams.programming.framework import React
from diagrams.saas.chat import Slack

# Custom attributes for better layout
graph_attr = {
    "fontsize": "12",
    "bgcolor": "white",
    "pad": "2.0",
    "splines": "spline",
    "rankdir": "TB",
    "ranksep": "3.0",
    "nodesep": "2.0",
    "concentrate": "false",
    "compound": "true",
    "sep": "1.0"
}

node_attr = {
    "fontsize": "10"
}

edge_attr = {
    "fontsize": "8"
}

with Diagram("Option 4: Klook/Viator Scale - 50M+ Users", 
             filename="01/diagrams/option-4-scale-klook",
             direction="TB",
             graph_attr=graph_attr,
             node_attr=node_attr,
             edge_attr=edge_attr,
             show=False):
    
    # Users global
    mobile_users = Users("Mobile Users\n50M+\nGlobal")
    
    # DNS & DDoS
    dns = Route53("Route 53\nGeographic routing\nMulti-region")
    shield = Shield("AWS Shield\nDDoS protection")
    waf = WAF("WAF\nBot mitigation")
    
    with Cluster("CDN & Edge"):
        cdn_global = CloudFront("CloudFront\n500+ edge locations\nGlobal")
        cdn_china = React("Alibaba CDN\nChina")
        cdn_latam = React("Regional CDN\nLatAm")
        cdn_apac = React("Regional CDN\nAPAC")
    
    with Cluster("AWS US-EAST-1 Primary (East)"):
        nlb = React("Network LB\nUltra-high throughput\n10k+ QPS")
        api_gw = APIGateway("API Gateway\nV2 HTTP\nPayload compression")
        
        with Cluster("Kubernetes (EKS)\n(Full microservices, auto-scale)"):
            with Cluster("Microservices (30+ services)"):
                user_pod = React("User Service\nHorizontal scale")
                partner_pod = React("Partner Service")
                recommendation_pod = React("Recommendation\nML-based")
                payment_pod = React("Payment Service\nPCI-DSS")
                loyalty_pod = React("Loyalty\nPoints")
                ar_pod = React("Photo Recognition\nGPU workers")
                search_pod = React("Search Service\nOpenSearch")
            
            with Cluster("Service Mesh (Istio)\nTraffic management\nCanary deployments"):
                mesh = React("Istio\nLoad balancing")
        
        with Cluster("Data Layer - Sharded"):
            db_shard_us = React("PostgreSQL Aurora\n10+ shards\n(US data)")
            db_replica_us = React("Read replicas\n50+")
            cache_us = React("Redis Cluster\n100GB+\n(Sharded)")
            ar_series = React("DynamoDB\nGlobal tables\nAR logs")
            s3_us = S3("S3 (Multi-tier)\nStandard→IA→Glacier")
        
        with Cluster("Search & Analytics"):
            opensearch = React("OpenSearch\nSharded cluster\nReal-time")
            kinesis = React("Kinesis\nMultiple streams\nPartitioned")
            kafka = React("Kafka\nHigh-throughput\nEvent streaming")
            redshift = React("Redshift\nPeta-scale\nAnalytics")
        
        with Cluster("Messaging & Events"):
            sqs = SQS("SQS\nFIFO + standard\nDead-letter queues")
            sns = SNS("SNS\nFan-out\nMillions/sec")
            eventbridge = React("EventBridge\nCross-region\nEvent routing")
        
        observability = React("DataDog APM\nDistributed tracing\nProfiling")
    
    with Cluster("AWS US-WEST-2 Secondary (West)"):
        nlb_west = React("NLB\nActive-active")
        eks_west = React("EKS Cluster\nFull stack")
        db_west = React("PostgreSQL Aurora\n10+ shards")
        cache_west = React("Redis Cluster\n100GB+")
        s3_west = S3("S3 Regional")
    
    with Cluster("AWS CN-NORTH-1 China"):
        nlb_cn = React("NLB")
        eks_cn = React("EKS\nChina data")
        db_cn = React("Aurora\nChina shards")
    
    with Cluster("AWS EU-WEST-1 Europe"):
        nlb_eu = React("NLB\nGDPR compliant")
        eks_eu = React("EKS\nEU data")
        db_eu = React("Aurora\nEU shards")
    
    with Cluster("AWS APAC (Multi-Region)"):
        nlb_apac = React("NLB")
        eks_apac = React("EKS\nAPAC data")
    
    with Cluster("Global Data Replication"):
        global_repl = React("Aurora Global DB\nRead-only replicas\nCross-region")
        s3_repl = React("S3 Cross-Region\nReplication")
    
    with Cluster("DR & Backup"):
        backup = React("Backup Service\n35-day PITR\nMulti-region copies")
        dr_failover = React("DR Automation\nRPO: 5 min\nRTO: 15 min")
    
    with Cluster("Security"):
        auth = Cognito("Cognito\nMFA mandatory")
        kms = React("KMS\nRegional keys")
        secrets = React("Secrets Manager\nRotation")
    
    with Cluster("AI & ML"):
        sagemaker = React("SageMaker\nModel serving\n(ML Endpoints)")
        nvidia_gpu = React("GPU Workers\nPhoto recognition")
    
    with Cluster("External Services"):
        with Cluster("Payment & Compliance"):
            stripe_api = React("Stripe\nHigh-volume")
            paypal = React("PayPal\nFallback")
        
        with Cluster("AI Services"):
            openai = React("OpenAI\nToken pooling")
            gemini = React("Google Gemini")
        
        with Cluster("Communications"):
            twilio = React("Twilio\nGlobal SMS")
            sendgrid = React("SendGrid\nMarketing")
        
        with Cluster("Content"):
            maps = React("Google Maps\nAdvanced")
            translation = React("Neural translation")
    
    with Cluster("Developer Tools"):
        logging = React("CloudWatch Logs\nDataDog")
        metrics = React("Prometheus\nGrafana")
        tracing = React("X-Ray\nJaeger")
    
    # Main user flow
    mobile_users >> Edge(label="HTTPS\nTLS 1.3") >> dns >> shield >> waf
    dns >> Edge(label="US users") >> cdn_global >> nlb
    dns >> Edge(label="China users") >> cdn_china >> nlb_cn
    dns >> Edge(label="LatAm users") >> cdn_latam >> nlb
    dns >> Edge(label="APAC users") >> cdn_apac >> nlb_apac
    
    # Primary region
    nlb >> api_gw >> mesh
    mesh >> user_pod
    mesh >> partner_pod
    mesh >> recommendation_pod
    mesh >> payment_pod
    
    # AR flow with GPU
    user_pod >> ar_pod
    ar_pod >> nvidia_gpu
    ar_pod >> sagemaker
    
    # Data operations
    payment_pod >> db_shard_us
    user_pod >> cache_us
    recommendation_pod >> opensearch
    
    # Events
    user_pod >> kinesis
    kinesis >> kafka
    kafka >> redshift
    
    # Payment processing
    payment_pod >> stripe_api
    payment_pod >> paypal
    
    # Messaging at scale
    user_pod >> sqs
    sqs >> sns
    
    # Global replication
    db_shard_us >> global_repl
    global_repl >> db_west
    global_repl >> db_cn
    global_repl >> db_eu
    
    # Secondary regions
    nlb_west >> eks_west
    nlb_cn >> eks_cn
    nlb_eu >> eks_eu
    
    # Observability
    user_pod >> Edge(label="Real-time traces") >> observability
    observability >> Edge(label="Alert") >> Slack("Slack\nPagerDuty")
    
    # Backup & DR
    db_shard_us >> backup
    backup >> dr_failover
    
    # Security
    user_pod >> auth
    user_pod >> secrets
