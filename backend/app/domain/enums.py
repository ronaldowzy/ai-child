from enum import StrEnum


class IntentType(StrEnum):
    CASUAL_CHAT = "casual_chat"
    INTEREST_EXPLORATION = "interest_exploration"
    AFTER_SCHOOL_CHECKIN = "after_school_checkin"
    LEARNING_HELP = "learning_help"
    HOMEWORK_PROBLEM = "homework_problem"
    READING_EXPRESSION = "reading_expression"
    EMOTION_EXPRESSION = "emotion_expression"
    SOCIAL_ISSUE = "social_issue"
    BEDTIME_REFLECTION = "bedtime_reflection"
    AI_LITERACY = "ai_literacy"
    PRIVACY_QUESTION = "privacy_question"
    SAFETY_RISK = "safety_risk"
    UNKNOWN = "unknown"


class RiskLevel(StrEnum):
    NONE = "none"
    LOW = "low"
    WATCH = "watch"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(StrEnum):
    NONE = "none"
    PRIVACY = "privacy"
    BULLYING = "bullying"
    SELF_HARM = "self_harm"
    VIOLENCE = "violence"
    SEXUAL_CONTENT = "sexual_content"
    ADULT_SECRET = "adult_secret"
    STRANGER_CONTACT = "stranger_contact"
    MEDICAL = "medical"
    MENTAL_DISTRESS = "mental_distress"
    DANGEROUS_BEHAVIOR = "dangerous_behavior"
    UNKNOWN_RISK = "unknown_risk"
