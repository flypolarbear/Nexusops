"""
NexusOps Agents - Cost Agent Handler

nexusops.cost: 云资源成本分析、预算管理、优化建议
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.agents.base import BaseAgentHandler
from app.gateway.executor.base import ExecutorRequest, ExecutorResult


class CostAgentHandler(BaseAgentHandler):
    """Cost agent handler for cloud resource cost analysis and optimization"""

    @property
    def agent_id(self) -> str:
        return "nexusops.cost"

    @property
    def capabilities(self) -> List[str]:
        return [
            "cost_query",
            "cost_by_service",
            "cost_by_region",
            "cost_trend_analysis",
            "budget_comparison",
            "budget_alert",
            "cost_optimization",
            "resource_utilization",
        ]

    async def handle(self, request: ExecutorRequest) -> ExecutorResult:
        """Handle cost-related requests"""
        await asyncio.sleep(0.2)

        query = request.query.lower()
        context = request.request_context

        # Route to appropriate handler based on query keywords
        if "trend" in query or "趋势" in query:
            return self._handle_trend_analysis(context)
        elif "budget" in query or "预算" in query:
            return self._handle_budget_comparison(context)
        elif "optimization" in query or "优化" in query or "optimize" in query:
            return self._handle_optimization(context)
        elif "utilization" in query or "利用率" in query:
            return self._handle_utilization(context)
        elif "service" in query or "服务" in query:
            return self._handle_cost_by_service(context)
        elif "region" in query or "区域" in query:
            return self._handle_cost_by_region(context)
        else:
            return self._handle_general_cost_query(context)

    def _handle_general_cost_query(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle general cost query"""
        # Mock data for current month
        total_cost = 12500.00
        budget = 15000.00
        usage_percentage = (total_cost / budget) * 100

        return self._success(
            text=f"""## Cost Overview - Current Month

**Total Cost:** ${total_cost:,.2f}
**Budget:** ${budget:,.2f}
**Usage:** {usage_percentage:.1f}%

### Cost by Service
| Service | Cost | % of Total |
|---------|------|------------|
| EC2 | $5,000.00 | 40.0% |
| RDS | $3,000.00 | 24.0% |
| S3 | $1,875.00 | 15.0% |
| Lambda | $1,250.00 | 10.0% |
| CloudWatch | $750.00 | 6.0% |
| Other | $625.00 | 5.0% |

### Cost by Region
| Region | Cost | % of Total |
|--------|------|------------|
| us-east-1 | $6,000.00 | 48.0% |
| us-west-2 | $3,500.00 | 28.0% |
| eu-west-1 | $2,000.00 | 16.0% |
| ap-southeast-1 | $1,000.00 | 8.0% |

### Budget Status
{"Over budget!" if usage_percentage > 100 else f"${budget - total_cost:,.2f} remaining ({100 - usage_percentage:.1f}% of budget)"}
""",
            structured_output={
                "type": "cost_overview",
                "data": {
                    "total_cost": total_cost,
                    "budget": budget,
                    "usage_percentage": usage_percentage,
                    "by_service": {
                        "EC2": 5000.00,
                        "RDS": 3000.00,
                        "S3": 1875.00,
                        "Lambda": 1250.00,
                        "CloudWatch": 750.00,
                        "Other": 625.00,
                    },
                    "by_region": {
                        "us-east-1": 6000.00,
                        "us-west-2": 3500.00,
                        "eu-west-1": 2000.00,
                        "ap-southeast-1": 1000.00,
                    },
                    "period": "current_month",
                },
            },
            suggested_actions=[
                self._action("view-trend", "invoke", "View Cost Trend",
                           {"agent_id": "nexusops.cost", "query": "cost trend analysis"}),
                self._action("view-optimization", "invoke", "Get Optimization Tips",
                           {"agent_id": "nexusops.cost", "query": "cost optimization suggestions"}),
                self._action("view-utilization", "invoke", "Check Resource Utilization",
                           {"agent_id": "nexusops.cost", "query": "resource utilization analysis"}),
            ],
            metadata={"operation": "cost_overview"},
        )

    def _handle_cost_by_service(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle cost breakdown by service"""
        by_service = {
            "EC2": {"cost": 5000.00, "change": 5.2},
            "RDS": {"cost": 3000.00, "change": -2.1},
            "S3": {"cost": 1875.00, "change": 12.5},
            "Lambda": {"cost": 1250.00, "change": 8.3},
            "CloudWatch": {"cost": 750.00, "change": 3.0},
            "DynamoDB": {"cost": 400.00, "change": -5.0},
            "API Gateway": {"cost": 225.00, "change": 15.2},
        }

        service_rows = "\n".join([
            f"| {svc} | ${data['cost']:,.2f} | {'+' if data['change'] >= 0 else ''}{data['change']:.1f}% |"
            for svc, data in by_service.items()
        ])

        return self._success(
            text=f"""## Cost by Service

| Service | Cost (USD) | Change vs Last Month |
|---------|------------|---------------------|
{service_rows}

### Top Cost Drivers
1. **EC2** - 40% of total cost, up 5.2% from last month
2. **RDS** - 24% of total cost, down 2.1% from last month
3. **S3** - 15% of total cost, up 12.5% from last month
""",
            structured_output={
                "type": "cost_by_service",
                "data": {
                    "by_service": by_service,
                    "total": sum(d["cost"] for d in by_service.values()),
                },
            },
            metadata={"operation": "cost_by_service"},
        )

    def _handle_cost_by_region(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle cost breakdown by region"""
        by_region = {
            "us-east-1": {"cost": 6000.00, "resources": 45},
            "us-west-2": {"cost": 3500.00, "resources": 28},
            "eu-west-1": {"cost": 2000.00, "resources": 15},
            "ap-southeast-1": {"cost": 1000.00, "resources": 8},
        }

        region_rows = "\n".join([
            f"| {region} | ${data['cost']:,.2f} | {data['resources']} |"
            for region, data in by_region.items()
        ])

        return self._success(
            text=f"""## Cost by Region

| Region | Cost (USD) | Active Resources |
|--------|------------|------------------|
{region_rows}

### Regional Insights
- **us-east-1** has the highest concentration of resources (45)
- Consider consolidating resources in **ap-southeast-1** to reduce cross-region data transfer costs
""",
            structured_output={
                "type": "cost_by_region",
                "data": {
                    "by_region": by_region,
                    "total": sum(d["cost"] for d in by_region.values()),
                },
            },
            metadata={"operation": "cost_by_region"},
        )

    def _handle_trend_analysis(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle cost trend analysis"""
        # Generate mock trend data for the last 30 days
        today = datetime.now()
        trend_data = []
        base_cost = 350.0

        for i in range(30):
            date = today - timedelta(days=29 - i)
            # Add some variance to make it look realistic
            import random
            random.seed(i)  # Reproducible for demo
            daily_cost = base_cost + random.uniform(-50, 80)
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "cost": round(daily_cost, 2),
            })

        weekly_avg = sum(d["cost"] for d in trend_data[-7:]) / 7
        monthly_avg = sum(d["cost"] for d in trend_data) / 30

        return self._success(
            text=f"""## Cost Trend Analysis (Last 30 Days)

### Daily Cost Trend
```
Cost ($)
450 |                                   *
400 |                    *        *     |
350 |     *  *  *   *      *            |  Weekly Avg: ${weekly_avg:,.2f}
300 |  *              *        *   *    |  Monthly Avg: ${monthly_avg:,.2f}
250 |------------------------------------
     1   5   10  15  20  25  30
```

### Summary Statistics
- **7-Day Average:** ${weekly_avg:,.2f}/day
- **30-Day Average:** ${monthly_avg:,.2f}/day
- **Projected Monthly:** ${monthly_avg * 30:,.2f}

### Trend Observation
Costs have been relatively stable with slight upward trend in the past week.
""",
            structured_output={
                "type": "cost_trend",
                "data": {
                    "trend": trend_data,
                    "weekly_average": round(weekly_avg, 2),
                    "monthly_average": round(monthly_avg, 2),
                    "projected_monthly": round(monthly_avg * 30, 2),
                    "period": "30_days",
                },
            },
            suggested_actions=[
                self._action("view-breakdown", "invoke", "View Service Breakdown",
                           {"agent_id": "nexusops.cost", "query": "cost by service"}),
            ],
            metadata={"operation": "trend_analysis"},
        )

    def _handle_budget_comparison(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle budget comparison and alerts"""
        budget = 15000.00
        current_spend = 12500.00
        remaining = budget - current_spend
        days_remaining = 5
        daily_burn_rate = current_spend / 25  # Assume 25 days into the month
        projected_spend = current_spend + (daily_burn_rate * days_remaining)

        alert_level = "normal"
        if projected_spend > budget * 1.1:
            alert_level = "critical"
        elif projected_spend > budget:
            alert_level = "warning"

        return self._success(
            text=f"""## Budget Comparison & Alerts

### Budget Status
| Metric | Value |
|--------|-------|
| Monthly Budget | ${budget:,.2f} |
| Current Spend | ${current_spend:,.2f} |
| Remaining | ${remaining:,.2f} |
| Days Remaining | {days_remaining} |
| Daily Burn Rate | ${daily_burn_rate:,.2f} |
| Projected Month-End | ${projected_spend:,.2f} |

### Alert Status: {alert_level.upper()}

{"**WARNING:** Projected to exceed budget by ${projected_spend - budget:,.2f}" if projected_spend > budget else "**OK:** On track to stay within budget"}

### Recommendations
{"- Consider reducing EC2 instances by 10% to stay within budget" if alert_level != "normal" else "- Continue monitoring daily spend"}
{"- Review unused resources for potential savings" if alert_level == "critical" else "- Current spending patterns are sustainable"}
""",
            structured_output={
                "type": "budget_comparison",
                "data": {
                    "budget": budget,
                    "current_spend": current_spend,
                    "remaining": remaining,
                    "days_remaining": days_remaining,
                    "daily_burn_rate": round(daily_burn_rate, 2),
                    "projected_spend": round(projected_spend, 2),
                    "alert_level": alert_level,
                    "over_budget": projected_spend > budget,
                },
            },
            suggested_actions=[
                self._action("set-alert", "invoke", "Configure Budget Alert",
                           {"agent_id": "nexusops.cost", "query": "set budget alert at 80%"}),
                self._action("view-optimization", "invoke", "Get Cost Optimization Tips",
                           {"agent_id": "nexusops.cost", "query": "cost optimization"}),
            ] if alert_level != "normal" else [],
            metadata={"operation": "budget_comparison"},
        )

    def _handle_optimization(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle cost optimization suggestions"""
        optimization_tips = [
            {
                "title": "Right-size EC2 Instances",
                "description": "3 instances have CPU utilization below 10%",
                "potential_savings": 450.00,
                "priority": "high",
                "resources": ["i-12345", "i-67890", "i-11111"],
            },
            {
                "title": "Delete Unattached EBS Volumes",
                "description": "Found 5 unattached volumes totaling 500GB",
                "potential_savings": 50.00,
                "priority": "medium",
                "resources": ["vol-abc", "vol-def", "vol-ghi", "vol-jkl", "vol-mno"],
            },
            {
                "title": "Review RDS Instance Types",
                "description": "2 RDS instances could use Reserved Instances",
                "potential_savings": 600.00,
                "priority": "high",
                "resources": ["db-prod-1", "db-staging-1"],
            },
            {
                "title": "Enable S3 Intelligent-Tiering",
                "description": "Move infrequently accessed data to cheaper tiers",
                "potential_savings": 200.00,
                "priority": "low",
                "resources": ["data-bucket", "logs-bucket"],
            },
            {
                "title": "Review NAT Gateway Usage",
                "description": "2 NAT Gateways with low throughput detected",
                "potential_savings": 90.00,
                "priority": "medium",
                "resources": ["nat-1", "nat-2"],
            },
        ]

        total_potential_savings = sum(t["potential_savings"] for t in optimization_tips)

        tips_text = "\n".join([
            f"### {i+1}. {tip['title']} ({tip['priority'].upper()} Priority)\n"
            f"- **Potential Savings:** ${tip['potential_savings']:,.2f}/month\n"
            f"- **Description:** {tip['description']}\n"
            f"- **Affected Resources:** {len(tip['resources'])}\n"
            for i, tip in enumerate(optimization_tips)
        ])

        return self._success(
            text=f"""## Cost Optimization Suggestions

**Total Potential Monthly Savings: ${total_potential_savings:,.2f}**

{tips_text}

### Quick Actions
Implementing the high-priority recommendations could save up to **$1,050/month**.
""",
            structured_output={
                "type": "cost_optimization",
                "data": {
                    "optimization_tips": optimization_tips,
                    "total_potential_savings": total_potential_savings,
                    "high_priority_savings": sum(t["potential_savings"] for t in optimization_tips if t["priority"] == "high"),
                },
            },
            suggested_actions=[
                self._action("apply-rightsizing", "invoke", "Apply EC2 Rightsizing",
                           {"agent_id": "nexusops.cost", "query": "apply EC2 rightsizing recommendations"},
                           confirm_required=True),
                self._action("delete-volumes", "invoke", "Delete Unattached Volumes",
                           {"agent_id": "nexusops.cost", "query": "delete unattached EBS volumes"},
                           confirm_required=True, danger=True),
                self._action("reserve-rds", "invoke", "Review RDS Reserved Instances",
                           {"agent_id": "nexusops.cost", "query": "review RDS reserved instance options"}),
            ],
            metadata={"operation": "cost_optimization"},
        )

    def _handle_utilization(self, context: Dict[str, Any]) -> ExecutorResult:
        """Handle resource utilization analysis"""
        utilization_data = {
            "EC2": {
                "total_instances": 15,
                "avg_cpu": 35.5,
                "avg_memory": 48.2,
                "underutilized": 3,
                "overutilized": 1,
            },
            "RDS": {
                "total_instances": 4,
                "avg_cpu": 42.3,
                "avg_memory": 65.8,
                "underutilized": 1,
                "overutilized": 0,
            },
            "Lambda": {
                "total_functions": 25,
                "avg_invocations_per_day": 15000,
                "avg_duration_ms": 245,
                "cold_start_rate": 3.2,
            },
            "S3": {
                "total_buckets": 12,
                "total_storage_gb": 2500,
                "avg_request_rate": 50000,
            },
        }

        return self._success(
            text=f"""## Resource Utilization Analysis

### EC2 Instances
- **Total Instances:** {utilization_data['EC2']['total_instances']}
- **Average CPU:** {utilization_data['EC2']['avg_cpu']}%
- **Average Memory:** {utilization_data['EC2']['avg_memory']}%
- **Underutilized (< 10% CPU):** {utilization_data['EC2']['underutilized']}
- **Overutilized (> 80% CPU):** {utilization_data['EC2']['overutilized']}

### RDS Databases
- **Total Instances:** {utilization_data['RDS']['total_instances']}
- **Average CPU:** {utilization_data['RDS']['avg_cpu']}%
- **Average Memory:** {utilization_data['RDS']['avg_memory']}%
- **Underutilized:** {utilization_data['RDS']['underutilized']}

### Lambda Functions
- **Total Functions:** {utilization_data['Lambda']['total_functions']}
- **Daily Invocations:** {utilization_data['Lambda']['avg_invocations_per_day']:,}
- **Avg Duration:** {utilization_data['Lambda']['avg_duration_ms']}ms
- **Cold Start Rate:** {utilization_data['Lambda']['cold_start_rate']}%

### S3 Storage
- **Total Buckets:** {utilization_data['S3']['total_buckets']}
- **Total Storage:** {utilization_data['S3']['total_storage_gb']:,} GB
- **Request Rate:** {utilization_data['S3']['avg_request_rate']:,}/day

### Recommendations
- {utilization_data['EC2']['underutilized']} EC2 instances are candidates for downsizing
- Consider Reserved Instances for stable RDS workloads
""",
            structured_output={
                "type": "resource_utilization",
                "data": utilization_data,
            },
            suggested_actions=[
                self._action("view-underutilized", "invoke", "View Underutilized Resources",
                           {"agent_id": "nexusops.cost", "query": "show underutilized EC2 instances"}),
                self._action("optimize-lambda", "invoke", "Optimize Lambda Functions",
                           {"agent_id": "nexusops.cost", "query": "Lambda optimization suggestions"}),
            ],
            metadata={"operation": "resource_utilization"},
        )

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get tool definitions for this agent"""
        return [
            {
                "name": "get_cost_overview",
                "description": "Get overall cost summary for the current period",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period": {
                            "type": "string",
                            "enum": ["daily", "weekly", "monthly"],
                            "default": "monthly",
                        },
                    },
                },
            },
            {
                "name": "get_cost_by_service",
                "description": "Get cost breakdown by cloud service",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "services": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of services to filter",
                        },
                    },
                },
            },
            {
                "name": "get_cost_by_region",
                "description": "Get cost breakdown by region",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "regions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of regions to filter",
                        },
                    },
                },
            },
            {
                "name": "get_cost_trend",
                "description": "Get cost trend analysis over time",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "period_days": {
                            "type": "integer",
                            "default": 30,
                            "description": "Number of days to analyze",
                        },
                    },
                },
            },
            {
                "name": "get_budget_status",
                "description": "Get budget comparison and alerts",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "budget_id": {
                            "type": "string",
                            "description": "Budget identifier",
                        },
                    },
                },
            },
            {
                "name": "get_optimization_suggestions",
                "description": "Get cost optimization recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "priority": {
                            "type": "string",
                            "enum": ["high", "medium", "low", "all"],
                            "default": "all",
                        },
                    },
                },
            },
            {
                "name": "get_resource_utilization",
                "description": "Get resource utilization analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "resource_type": {
                            "type": "string",
                            "enum": ["EC2", "RDS", "Lambda", "S3", "all"],
                            "default": "all",
                        },
                    },
                },
            },
        ]
