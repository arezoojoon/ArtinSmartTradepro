"""
Pipeline Automation Service
Phase 6 Enhancement - Automated deal pipeline with stage transitions and notifications
"""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from dataclasses import dataclass
from enum import Enum
import json

from app.models.deal import Deal, DealMilestone, DealRiskAssessment
from app.models.crm import CRMCompany, CRMContact
from app.models.user import User
from app.models.tenant import Tenant
from app.config import get_settings


class TriggerType(str, Enum):
    STAGE_CHANGE = "stage_change"
    MILESTONE_DUE = "milestone_due"
    RISK_DETECTED = "risk_detected"
    DEAL_STALLED = "deal_stalled"
    DEADLINE_APPROACHING = "deadline_approaching"
    VALUE_THRESHOLD = "value_threshold"
    TIME_IN_STAGE = "time_in_stage"


class ActionType(str, Enum):
    NOTIFICATION = "notification"
    EMAIL = "email"
    TASK = "task"
    STAGE_CHANGE = "stage_change"
    ASSIGNMENT = "assignment"
    ALERT = "alert"
    WEBHOOK = "webhook"


@dataclass
class AutomationRule:
    """Automation rule definition"""
    id: str
    name: str
    description: str
    trigger_type: TriggerType
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime


@dataclass
class TriggerEvent:
    """Trigger event that fires automation rules"""
    event_type: TriggerType
    deal_id: str
    tenant_id: str
    data: Dict[str, Any]
    timestamp: datetime


@dataclass
class AutomationAction:
    """Automation action to be executed"""
    action_type: ActionType
    parameters: Dict[str, Any]
    rule_id: str
    deal_id: str
    tenant_id: str
    executed_at: datetime
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class PipelineAutomationService:
    """Service for pipeline automation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.action_handlers = {
            ActionType.NOTIFICATION: self._handle_notification,
            ActionType.EMAIL: self._handle_email,
            ActionType.TASK: self._handle_task,
            ActionType.STAGE_CHANGE: self._handle_stage_change,
            ActionType.ASSIGNMENT: self._handle_assignment,
            ActionType.ALERT: self._handle_alert,
            ActionType.WEBHOOK: self._handle_webhook
        }
        
        # Default automation rules
        self.default_rules = self._initialize_default_rules()
        
        # Rule storage (in production, this would be in database)
        self.rules = {}
    
    def _initialize_default_rules(self) -> List[AutomationRule]:
        """Initialize default automation rules"""
        return [
            # Stage change rules
            AutomationRule(
                id="auto_stage_change_qualified_to_proposal",
                name="Auto Stage Change: Qualified to Proposal",
                description="Automatically move deals from Qualified to Proposal stage when conditions are met",
                trigger_type=TriggerType.STAGE_CHANGE,
                trigger_conditions={
                    "from_stage": "qualified",
                    "to_stage": "proposal",
                    "conditions": [
                        {"field": "total_value", "operator": ">", "value": 10000},
                        {"field": "days_in_stage", "operator": ">", "value": 3}
                    ]
                },
                actions=[
                    {
                        "type": "stage_change",
                        "parameters": {"target_stage": "proposal"}
                    },
                    {
                        "type": "notification",
                        "parameters": {
                            "message": "Deal automatically moved to Proposal stage",
                            "recipients": ["deal_owner", "sales_manager"]
                        }
                    },
                    {
                        "type": "task",
                        "parameters": {
                            "title": "Prepare proposal for {deal_title}",
                            "description": "Create and send proposal for {deal_title}",
                            "assignee": "deal_owner",
                            "due_date": "+3 days"
                        }
                    }
                ],
                is_active=True,
                priority=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            
            # Milestone due rules
            AutomationRule(
                id="milestone_due_reminder",
                name="Milestone Due Reminder",
                description="Send reminders when milestones are due",
                trigger_type=TriggerType.MILESTONE_DUE,
                trigger_conditions={
                    "days_before_due": [3, 1, 0],  # 3 days before, 1 day before, day of
                    "milestone_types": ["contract_signed", "payment_received", "delivery_date"]
                },
                actions=[
                    {
                        "type": "notification",
                        "parameters": {
                            "message": "Milestone '{milestone_title}' is due in {days_until} days",
                            "recipients": ["deal_owner", "assigned_to"]
                        }
                    },
                    {
                        "type": "email",
                        "parameters": {
                            "template": "milestone_reminder",
                            "recipients": ["deal_owner"],
                            "subject": "Milestone Due: {milestone_title}",
                            "data": {
                                "milestone_title": "{milestone_title}",
                                "days_until": "{days_until}",
                                "deal_title": "{deal_title}"
                            }
                        }
                    }
                ],
                is_active=True,
                priority=2,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            
            # Risk detection rules
            AutomationRule(
                id="high_risk_alert",
                name="High Risk Alert",
                description="Alert when high-risk deals are detected",
                trigger_type=TriggerType.RISK_DETECTED,
                trigger_conditions={
                    "risk_level": ["high", "critical"],
                    "score_threshold": 70
                },
                actions=[
                    {
                        "type": "notification",
                        "parameters": {
                            "message": "High risk detected in deal: {deal_title}",
                            "recipients": ["deal_owner", "risk_manager", "sales_manager"]
                        }
                    },
                    {
                        "type": "task",
                        "parameters": {
                            "title": "Review high risk factors for {deal_title}",
                            "description": "Review and mitigate high risk factors",
                            "assignee": "risk_manager",
                            "priority": "high"
                        }
                    },
                    {
                        "type": "alert",
                        "parameters": {
                            "level": "high",
                            "message": "High risk detected in deal {deal_title}",
                            "deal_id": "{deal_id}"
                        }
                    }
                ],
                is_active=True,
                priority=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            
            # Deal stalled rules
            AutomationRule(
                id="deal_stalled_alert",
                name="Deal Stalled Alert",
                description="Alert when deals have been in the same stage too long",
                trigger_type=TriggerType.DEAL_STALLED,
                trigger_conditions={
                    "days_in_stage": [7, 14, 30],  # 1 week, 2 weeks, 1 month
                    "stages": ["identified", "matching", "validating", "negotiating"]
                },
                actions=[
                    {
                        "type": "notification",
                        "parameters": {
                            "message": "Deal {deal_title} has been in {stage} stage for {days} days",
                            "recipients": ["deal_owner", "sales_manager"]
                        }
                    },
                    {
                        "type": "task",
                        "parameters": {
                            "title": "Review stalled deal: {deal_title}",
                            "description": "Deal has been in {stage} stage for {days} days - review and take action",
                            "assignee": "deal_owner",
                            "priority": "medium"
                        }
                    }
                ],
                is_active=True,
                priority=2,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            
            # Value threshold rules
            AutomationRule(
                id="high_value_deal_alert",
                name="High Value Deal Alert",
                description="Alert when high-value deals are created or updated",
                trigger_type=TriggerType.VALUE_THRESHOLD,
                trigger_conditions={
                    "value_threshold": 100000,
                    "conditions": [
                        {"field": "total_value", "operator": ">", "value": 100000}
                    ]
                },
                actions=[
                    {
                        "type": "notification",
                        "parameters": {
                            "message": "High value deal detected: {deal_title} (${total_value})",
                            "recipients": ["deal_owner", "sales_manager", "executive"]
                        }
                    },
                    {
                        "type": "assignment",
                        "parameters": {
                            "assign_to": "senior_sales_manager",
                            "reason": "High value deal requires senior oversight"
                        }
                    }
                ],
                is_active=True,
                priority=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            
            # Deadline approaching rules
            AutomationRule(
                id="deadline_approaching_alert",
                name="Deadline Approaching Alert",
                description="Alert when deal deadlines are approaching",
                trigger_type=TriggerType.DEADLINE_APPROACHING,
                trigger_conditions={
                    "days_before_deadline": [7, 3, 1],
                    "deadline_types": ["expected_delivery_date", "contract_expiry"]
                },
                actions=[
                    {
                        "type": "notification",
                        "parameters": {
                            "message": "Deadline {deadline_type} approaching for deal {deal_title}",
                            "recipients": ["deal_owner", "assigned_to"]
                        }
                    },
                    {
                        "type": "email",
                        "parameters": {
                            "template": "deadline_approaching",
                            "recipients": ["deal_owner"],
                            "subject": "Deadline Approaching: {deadline_type}",
                            "data": {
                                "deadline_type": "{deadline_type}",
                                "days_until": "{days_until}",
                                "deal_title": "{deal_title}"
                            }
                        }
                    }
                ],
                is_active=True,
                priority=2,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
    
    async def create_automation_rule(
        self,
        rule_data: Dict[str, Any],
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Create a custom automation rule
        """
        rule_id = f"custom_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        rule = AutomationRule(
            id=rule_id,
            name=rule_data.get("name", "Custom Rule"),
            description=rule_data.get("description", ""),
            trigger_type=TriggerType(rule_data.get("trigger_type")),
            trigger_conditions=rule_data.get("trigger_conditions", {}),
            actions=rule_data.get("actions", []),
            is_active=rule_data.get("is_active", True),
            priority=rule_data.get("priority", 5),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.rules[rule_id] = rule
        
        return {
            "rule_id": rule_id,
            "status": "created",
            "rule": {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "trigger_type": rule.trigger_type.value,
                "is_active": rule.is_active,
                "priority": rule.priority
            }
        }
    
    async def trigger_automation(
        self,
        trigger_event: TriggerEvent
    ) -> List[AutomationAction]:
        """
        Trigger automation based on event
        """
        actions = []
        
        # Get all active rules for the tenant
        active_rules = [
            rule for rule in self.default_rules + list(self.rules.values())
            if rule.is_active and rule.trigger_type == trigger_event.event_type
        ]
        
        # Check each rule's conditions
        for rule in active_rules:
            if await self._evaluate_conditions(rule, trigger_event):
                # Execute actions for this rule
                for action_config in rule.actions:
                    action = await self._execute_action(
                        action_config,
                        rule,
                        trigger_event
                    )
                    actions.append(action)
        
        return actions
    
    async def _evaluate_conditions(
        self,
        rule: AutomationRule,
        trigger_event: TriggerEvent
    ) -> bool:
        """Evaluate if trigger event meets rule conditions"""
        conditions = rule.trigger_conditions
        event_data = trigger_event.data
        
        # Get deal data
        deal = self.db.query(Deal).filter(
            Deal.id == trigger_event.deal_id,
            Deal.tenant_id == trigger_event.tenant_id
        ).first()
        
        if not deal:
            return False
        
        # Evaluate each condition
        for condition in conditions.get("conditions", []):
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if not await self._evaluate_condition(deal, field, operator, value, event_data):
                return False
        
        # Check special conditions
        if "days_in_stage" in conditions:
            days_in_stage = conditions["days_in_stage"]
            if isinstance(days_in_stage, list):
                actual_days = self._get_days_in_stage(deal)
                if actual_days not in days_in_stage:
                    return False
            else:
                actual_days = self._get_days_in_stage(deal)
                if actual_days < days_in_stage:
                    return False
        
        if "days_before_due" in conditions:
            days_before_due = conditions["days_before_due"]
            if isinstance(days_before_due, list):
                if not any(self._check_milestone_due(deal, days) for days in days_before_due):
                    return False
            else:
                if not self._check_milestone_due(deal, days_before_due):
                    return False
        
        if "days_before_deadline" in conditions:
            days_before_deadline = conditions["days_before_deadline"]
            if isinstance(days_before_deadline, list):
                if not any(self._check_deadline_approaching(deal, days) for days in days_before_deadline):
                    return False
            else:
                if not self._check_deadline_approaching(deal, days_before_deadline):
                    return False
        
        return True
    
    async def _evaluate_condition(
        self,
        deal: Deal,
        field: str,
        operator: str,
        value: Any,
        event_data: Dict[str, Any]
    ) -> bool:
        """Evaluate a single condition"""
        # Get field value
        if field == "total_value":
            field_value = deal.total_value or 0
        elif field == "status":
            field_value = deal.status
        elif field == "priority":
            field_value = deal.priority
        elif field == "created_at":
            field_value = deal.created_at
        elif field == "updated_at":
            field_value = deal.updated_at
        elif field in event_data:
            field_value = event_data[field]
        else:
            return False
        
        # Evaluate condition
        if operator == ">":
            return field_value > value
        elif operator == "<":
            return field_value < value
        elif operator == "==":
            return field_value == value
        elif operator == "!=":
            return field_value != value
        elif operator == ">=":
            return field_value >= value
        elif operator == "<=":
            return field_value <= value
        elif operator == "in":
            return field_value in value if isinstance(value, list) else False
        elif operator == "not_in":
            return field_value not in value if isinstance(value, list) else True
        
        return False
    
    def _get_days_in_stage(self, deal: Deal) -> int:
        """Calculate days deal has been in current stage"""
        if deal.updated_at and deal.status:
            return (datetime.utcnow() - deal.updated_at).days
        return 0
    
    def _check_milestone_due(self, deal: Deal, days_before: int) -> bool:
        """Check if any milestone is due within specified days"""
        # Mock implementation - in production, this would query DealMilestone
        return False  # Mock implementation
    
    def _check_deadline_approaching(self, deal: Deal, days_before: int) -> bool:
        """Check if any deadline is approaching within specified days"""
        # Mock implementation - in production, this would check expected_delivery_date, contract_expiry
        return False  # Mock implementation
    
    async def _execute_action(
        self,
        action_config: Dict[str, Any],
        rule: AutomationRule,
        trigger_event: TriggerEvent
    ) -> AutomationAction:
        """Execute an automation action"""
        action_type = ActionType(action_config.get("type"))
        parameters = action_config.get("parameters", {})
        
        action = AutomationAction(
            action_type=action_type,
            parameters=parameters,
            rule_id=rule.id,
            deal_id=trigger_event.deal_id,
            tenant_id=trigger_event.tenant_id,
            executed_at=datetime.utcnow()
        )
        
        try:
            handler = self.action_handlers[action_type]
            result = await handler(action, trigger_event)
            action.result = result
        except Exception as e:
            action.error = str(e)
        
        return action
    
    async def _handle_notification(
        self,
        action: AutomationAction,
        trigger_event: TriggerEvent
    ) -> Dict[str, Any]:
        """Handle notification action"""
        # Mock notification implementation
        message = action.parameters.get("message", "Automation notification")
        recipients = action.parameters.get("recipients", [])
        
        # In production, this would send actual notifications
        return {
            "type": "notification",
            "message": message,
            "recipients": recipients,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_email(
        self,
        action: AutomationAction,
        trigger_event: TriggerEvent
    ) -> Dict[str, Any]:
        """Handle email action"""
        # Mock email implementation
        template = action.parameters.get("template", "automation")
        recipients = action.parameters.get("recipients", [])
        subject = action.parameters.get("subject", "Automation Notification")
        data = action.parameters.get("data", {})
        
        # In production, this would send actual emails
        return {
            "type": "email",
            "template": template,
            "recipients": recipients,
            "subject": subject,
            "data": data,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_task(
        self,
        action: AutomationAction,
        trigger_event: TriggerEvent
    ) -> Dict[str, Any]:
        """Handle task creation action"""
        # Mock task creation implementation
        title = action.parameters.get("title", "Automation Task")
        description = action.parameters.get("description", "")
        assignee = action.parameters.get("assignee")
        due_date = action.parameters.get("due_date")
        priority = action.parameters.get("priority", "medium")
        
        # In production, this would create actual tasks
        return {
            "type": "task",
            "title": title,
            "description": description,
            "assignee": assignee,
            "due_date": due_date,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_stage_change(
        self,
        action: AutomationAction,
        trigger_event: TriggerEvent
    ) -> Dict[str, Any]:
        """Handle stage change action"""
        target_stage = action.parameters.get("target_stage")
        
        # Update deal stage
        deal = self.db.query(Deal).filter(
            Deal.id == trigger_event.deal_id,
            Deal.tenant_id == trigger_event.tenant_id
        ).first()
        
        if deal and target_stage:
            deal.status = target_stage
            deal.updated_at = datetime.utcnow()
            self.db.commit()
        
        return {
            "type": "stage_change",
            "target_stage": target_stage,
            "previous_stage": deal.status if deal else None,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_assignment(
        self,
        action: AutomationAction,
        trigger_event: TriggerEvent
    ) -> Dict[str, Any]:
        """Handle assignment action"""
        assign_to = action.parameters.get("assign_to")
        reason = action.parameters.get("reason", "")
        
        # Update deal assignment
        deal = self.db.query(Deal).filter(
            Deal.id == trigger_event.deal_id,
            Deal.tenant_id == trigger_event.tenant_id
        ).first()
        
        if deal and assign_to:
            # Find user by name or ID
            user = self.db.query(User).filter(
                or_(
                    User.id == assign_to,
                    User.full_name == assign_to
                )
            ).first()
            
            if user:
                deal.assigned_to = user.id
                deal.updated_at = datetime.utcnow()
                self.db.commit()
        
        return {
            "type": "assignment",
            "assigned_to": assign_to,
            "reason": reason,
            "updated_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_alert(
        self,
        action: AutomationAction,
        trigger_event: TriggerEvent
    ) -> Dict[str, Any]:
        """Handle alert action"""
        level = action.parameters.get("level", "info")
        message = action.parameters.get("message", "")
        deal_id = action.parameters.get("deal_id")
        
        # In production, this would create actual alerts
        return {
            "type": "alert",
            "level": level,
            "message": message,
            "deal_id": deal_id,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _handle_webhook(
        self,
        action: AutomationAction,
        trigger_event: TriggerEvent
    ) -> Dict[str, Any]:
        """Handle webhook action"""
        url = action.parameters.get("url")
        method = action.parameters.get("method", "POST")
        data = action.parameters.get("data", {})
        
        # In production, this would make actual webhook calls
        return {
            "type": "webhook",
            "url": url,
            "method": method,
            "data": data,
            "sent_at": datetime.utcnow().isoformat()
        }
    
    async def get_automation_rules(
        self,
        tenant_id: str,
        is_active: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Get automation rules for a tenant"""
        all_rules = list(self.default_rules.values()) + list(self.rules.values())
        
        # Filter by tenant (mock implementation)
        tenant_rules = all_rules  # In production, filter by tenant_id
        
        if is_active is not None:
            tenant_rules = [rule for rule in tenant_rules if rule.is_active == is_active]
        
        return [
            {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "trigger_type": rule.trigger_type.value,
                "is_active": rule.is_active,
                "priority": rule.priority,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat()
            }
            for rule in tenant_rules
        ]
    
    async def update_automation_rule(
        self,
        rule_id: str,
        updates: Dict[str, Any],
        tenant_id: str
    ) -> Dict[str, Any]:
        """Update an automation rule"""
        if rule_id in self.rules:
            rule = self.rules[rule_id]
            
            # Update fields
            if "name" in updates:
                rule.name = updates["name"]
            if "description" in updates:
                rule.description = updates["description"]
            if "is_active" in updates:
                rule.is_active = updates["is_active"]
            if "priority" in updates:
                rule.priority = updates["priority"]
            if "trigger_conditions" in updates:
                rule.trigger_conditions = updates["trigger_conditions"]
            if "actions" in updates:
                rule.actions = updates["actions"]
            
            rule.updated_at = datetime.utcnow()
            
            return {
                "rule_id": rule_id,
                "status": "updated",
                "updated_fields": list(updates.keys())
            }
        else:
            raise ValueError(f"Rule '{rule_id}' not found")
    
    async def delete_automation_rule(
        self,
        rule_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Delete an automation rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            return {
                "rule_id": rule_id,
                "status": "deleted"
            }
        else:
            raise ValueError(f"Rule '{rule_id}' not found")
    
    async def get_automation_history(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get automation execution history"""
        # Mock implementation - in production, this would query a history table
        history = [
            {
                "action_id": "action_1",
                "rule_id": "auto_stage_change_qualified_to_proposal",
                "action_type": "stage_change",
                "deal_id": "deal_123",
                "deal_title": "Sample Deal",
                "executed_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "result": {"success": True, "new_stage": "proposal"},
                "error": None
            },
            {
                "action_id": "action_2",
                "rule_id": "milestone_due_reminder",
                "action_type": "notification",
                "deal_id": "deal_456",
                "deal_title": "Another Deal",
                "executed_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                "result": {"success": True},
                "error": None
            }
        ]
        
        return {
            "history": history[offset:offset + limit],
            "total_count": len(history),
            "limit": limit,
            "offset": offset
        }


# Helper function to get pipeline automation service
def get_pipeline_automation_service(db: Session) -> PipelineAutomationService:
    """Get pipeline automation service instance"""
    return PipelineAutomationService(db)
