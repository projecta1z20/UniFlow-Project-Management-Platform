import reflex as rx

import re
from datetime import date, datetime, time
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    JSON,
    MetaData,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    event,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    ORMExecuteState,
    Session,
    declared_attr,
    mapped_column,
    validates,
)


class Role(StrEnum):
    STUDENT = "student"
    FACULTY_ADVISOR = "faculty_advisor"
    SPONSOR = "sponsor"
    PROGRAM_ADMINISTRATOR = "program_administrator"
    SYSTEM_ADMINISTRATOR = "system_administrator"


class Lifecycle(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    MATCHING = "matching"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class ProjectStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Health(StrEnum):
    UNKNOWN = "unknown"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OFF_TRACK = "off_track"


class AvailabilityKind(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    PREFERRED = "preferred"


class RuleState(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    RETIRED = "retired"


class CriterionKind(StrEnum):
    STUDENT_PREFERENCE = "student_preference"
    SKILL_MATCH = "skill_match"
    AVAILABILITY_OVERLAP = "availability_overlap"
    TEAM_SIZE = "team_size"
    WORKLOAD_BALANCE = "workload_balance"
    ADVISOR_CAPACITY = "advisor_capacity"


class AssignmentState(StrEnum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class MemberRole(StrEnum):
    MEMBER = "member"
    LEAD = "lead"


class MilestoneState(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    CHANGES_REQUESTED = "changes_requested"
    ACCEPTED = "accepted"
    WAIVED = "waived"


class SubmissionState(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CHANGES_REQUESTED = "changes_requested"
    ACCEPTED = "accepted"
    WITHDRAWN = "withdrawn"


class FileState(StrEnum):
    PENDING = "pending"
    AVAILABLE = "available"
    QUARANTINED = "quarantined"
    DELETED = "deleted"


class MeetingState(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Attendance(StrEnum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    TENTATIVE = "tentative"
    DECLINED = "declined"
    ATTENDED = "attended"
    ABSENT = "absent"


class IssueKind(StrEnum):
    RISK = "risk"
    ISSUE = "issue"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueState(StrEnum):
    OPEN = "open"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ACCEPTED = "accepted"


class NotificationKind(StrEnum):
    GENERAL = "general"
    PROJECT_REVIEW = "project_review"
    ASSIGNMENT = "assignment"
    MILESTONE_DUE = "milestone_due"
    DELIVERABLE_REVIEW = "deliverable_review"
    MEETING = "meeting"
    RISK_ISSUE = "risk_issue"


class ProcessingState(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReadState(StrEnum):
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"


class ReportKind(StrEnum):
    PROJECTS = "projects"
    ASSIGNMENTS = "assignments"
    MILESTONES = "milestones"
    EVALUATIONS = "evaluations"
    RISKS = "risks"
    AUDIT = "audit"


class ExportFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    JSON = "json"


class ExportState(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    EXPIRED = "expired"


def enum_type(enum: type[StrEnum], name: str) -> Enum:
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [item.value for item in members],
    )


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Identity:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MutableRecord(Identity):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    @declared_attr.directive
    def __mapper_args__(cls):
        return {"version_id_col": cls.version}


class User(MutableRecord, Base):
    __tablename__ = "uniflow_user"
    __table_args__ = (
        UniqueConstraint("email"),
        CheckConstraint(
            "email = lower(trim(email)) AND length(email) > 3",
            name="normalized_email",
        ),
        CheckConstraint(
            "password_hash IS NULL OR length(password_hash) = 60",
            name="bcrypt_hash_length",
        ),
        CheckConstraint(
            "NOT is_active OR password_hash IS NOT NULL",
            name="active_has_password",
        ),
        Index(
            "ix_uniflow_user_active_name",
            "is_active",
            "last_name",
            "first_name",
        ),
    )
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    first_name: Mapped[str] = mapped_column(
        String(100), default="", server_default=""
    )
    last_name: Mapped[str] = mapped_column(
        String(100), default="", server_default=""
    )
    display_name: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    pronouns: Mapped[str] = mapped_column(
        String(80), default="", server_default=""
    )
    phone: Mapped[str] = mapped_column(
        String(40), default="", server_default=""
    )
    biography: Mapped[str] = mapped_column(Text, default="", server_default="")
    organization: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    department: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    degree_program: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    student_number: Mapped[str | None] = mapped_column(
        String(80), unique=True, nullable=True
    )
    graduation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    avatar_storage_key: Mapped[str | None] = mapped_column(
        String(512), nullable=True
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @validates("email")
    def normalize_email(self, key: str, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if len(normalized) > 254 or not re.fullmatch(
            r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized
        ):
            raise ValueError("A valid email address is required.")
        return normalized

    @validates("password_hash")
    def validate_password_hash(self, key: str, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(
            r"\$2[aby]\$(0[4-9]|[12][0-9]|3[01])\$[./A-Za-z0-9]{53}", value
        ):
            raise ValueError(
                "Only an encoded bcrypt password hash may be stored."
            )
        return value


class UserRole(MutableRecord, Base):
    __tablename__ = "uniflow_user_role"
    __table_args__ = (UniqueConstraint("user_id", "role"),)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    role: Mapped[Role] = mapped_column(
        enum_type(Role, "user_role"),
        default=Role.STUDENT,
        server_default="student",
    )
    granted_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, default="", server_default="")


class AdministratorBootstrap(Identity, Base):
    """A unique singleton claim, inserted with the first user's role in one future transaction."""

    __tablename__ = "uniflow_administrator_bootstrap"
    __table_args__ = (
        UniqueConstraint("singleton_key"),
        UniqueConstraint("user_id"),
        CheckConstraint("singleton_key = 1", name="singleton"),
        CheckConstraint("role = 'system_administrator'", name="system_role"),
        ForeignKeyConstraint(
            ["user_id", "role"],
            ["uniflow_user_role.user_id", "uniflow_user_role.role"],
            ondelete="RESTRICT",
        ),
    )
    singleton_key: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    role: Mapped[Role] = mapped_column(
        enum_type(Role, "bootstrap_role"),
        default=Role.SYSTEM_ADMINISTRATOR,
        server_default="system_administrator",
    )


class Skill(MutableRecord, Base):
    __tablename__ = "uniflow_skill"
    __table_args__ = (
        UniqueConstraint("name"),
        CheckConstraint(
            "name = lower(trim(name)) AND length(name) > 0",
            name="normalized_name",
        ),
    )
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )

    @validates("name")
    def normalize_name(self, key: str, value: str | None) -> str | None:
        if value is None:
            return None
        result = value.strip().lower()
        if not result or len(result) > 120:
            raise ValueError(
                "Skill names must contain between 1 and 120 characters."
            )
        return result


class UserSkill(MutableRecord, Base):
    __tablename__ = "uniflow_user_skill"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id"),
        CheckConstraint(
            "proficiency BETWEEN 1 AND 5", name="proficiency_range"
        ),
        CheckConstraint("years_experience >= 0", name="experience_nonnegative"),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    skill_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_skill.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    proficiency: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    years_experience: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), server_default="0"
    )


class SchedulingConstraint(MutableRecord, Base):
    __tablename__ = "uniflow_scheduling_constraint"
    __table_args__ = (
        UniqueConstraint("user_id"),
        CheckConstraint(
            "min_weekly_hours >= 0 AND max_weekly_hours >= min_weekly_hours AND max_weekly_hours <= 168",
            name="hours_range",
        ),
        CheckConstraint(
            "max_concurrent_projects >= 0 AND min_notice_hours >= 0",
            name="capacity_range",
        ),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="CASCADE"), nullable=True
    )
    timezone: Mapped[str] = mapped_column(
        String(80), default="UTC", server_default="UTC"
    )
    min_weekly_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), server_default="0"
    )
    max_weekly_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("40"), server_default="40"
    )
    max_concurrent_projects: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    min_notice_hours: Mapped[int] = mapped_column(
        Integer, default=24, server_default="24"
    )
    remote_only: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    notes: Mapped[str] = mapped_column(Text, default="", server_default="")

    @validates("timezone")
    def validate_timezone(self, key: str, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            import logging

            logging.exception(f"Error: {exc}")
            raise ValueError("Use a valid IANA timezone.") from exc
        return value


class AvailabilityWindow(MutableRecord, Base):
    __tablename__ = "uniflow_availability_window"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        CheckConstraint("end_time > start_time", name="time_order"),
        CheckConstraint(
            "effective_until IS NULL OR effective_from IS NULL OR effective_until >= effective_from",
            name="effective_order",
        ),
        Index("ix_uniflow_availability_user_day", "user_id", "weekday"),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="CASCADE"), nullable=True
    )
    weekday: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    kind: Mapped[AvailabilityKind] = mapped_column(
        enum_type(AvailabilityKind, "availability_kind"),
        default=AvailabilityKind.AVAILABLE,
        server_default="available",
    )
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)


class SchedulingException(MutableRecord, Base):
    __tablename__ = "uniflow_scheduling_exception"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="time_order"),
        Index("ix_uniflow_exception_user_start", "user_id", "starts_at"),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="CASCADE"), nullable=True
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    kind: Mapped[AvailabilityKind] = mapped_column(
        enum_type(AvailabilityKind, "exception_kind"),
        default=AvailabilityKind.UNAVAILABLE,
        server_default="unavailable",
    )
    reason: Mapped[str] = mapped_column(Text, default="", server_default="")


class Project(MutableRecord, Base):
    __tablename__ = "uniflow_project"
    __table_args__ = (
        CheckConstraint(
            "preferred_min_team_size >= 1 AND preferred_max_team_size >= preferred_min_team_size",
            name="team_size_range",
        ),
        CheckConstraint(
            "ends_on IS NULL OR starts_on IS NULL OR ends_on >= starts_on",
            name="date_order",
        ),
        CheckConstraint(
            "approved_at IS NULL OR approved_by_id IS NOT NULL",
            name="approval_actor",
        ),
        Index(
            "ix_uniflow_project_lifecycle_deadline",
            "lifecycle",
            "proposal_deadline",
        ),
        Index("ix_uniflow_project_status_health", "status", "health"),
    )
    title: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )
    summary: Mapped[str] = mapped_column(Text, default="", server_default="")
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    sponsor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    advisor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    preferred_min_team_size: Mapped[int] = mapped_column(
        Integer, default=3, server_default="3"
    )
    preferred_max_team_size: Mapped[int] = mapped_column(
        Integer, default=5, server_default="5"
    )
    proposal_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lifecycle: Mapped[Lifecycle] = mapped_column(
        enum_type(Lifecycle, "project_lifecycle"),
        default=Lifecycle.DRAFT,
        server_default="draft",
    )
    status: Mapped[ProjectStatus] = mapped_column(
        enum_type(ProjectStatus, "project_status"),
        default=ProjectStatus.NOT_STARTED,
        server_default="not_started",
    )
    health: Mapped[Health] = mapped_column(
        enum_type(Health, "project_health"),
        default=Health.UNKNOWN,
        server_default="unknown",
    )
    review_notes: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    approval_notes: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    starts_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    ends_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ProjectObjective(MutableRecord, Base):
    __tablename__ = "uniflow_project_objective"
    __table_args__ = (
        UniqueConstraint("project_id", "position"),
        CheckConstraint("position >= 1", name="positive_position"),
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    position: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    success_criteria: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )


class ProjectSkill(MutableRecord, Base):
    __tablename__ = "uniflow_project_skill"
    __table_args__ = (
        UniqueConstraint("project_id", "skill_id"),
        CheckConstraint(
            "minimum_proficiency BETWEEN 1 AND 5", name="proficiency_range"
        ),
        CheckConstraint("weight >= 0", name="nonnegative_weight"),
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    skill_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_skill.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    minimum_proficiency: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("1"), server_default="1"
    )


class FileMetadata(MutableRecord, Base):
    __tablename__ = "uniflow_file"
    __table_args__ = (
        UniqueConstraint("storage_key"),
        CheckConstraint("size_bytes >= 0", name="size_nonnegative"),
        CheckConstraint(
            "sha256 IS NULL OR length(sha256) = 64", name="checksum_length"
        ),
    )
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_filename: Mapped[str] = mapped_column(
        String(255), default="", server_default=""
    )
    content_type: Mapped[str] = mapped_column(
        String(160),
        default="application/octet-stream",
        server_default="application/octet-stream",
    )
    size_bytes: Mapped[Decimal] = mapped_column(
        Numeric(20, 0), default=Decimal("0"), server_default="0"
    )
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    uploaded_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    state: Mapped[FileState] = mapped_column(
        enum_type(FileState, "file_state"),
        default=FileState.PENDING,
        server_default="pending",
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @validates("sha256")
    def validate_sha256(self, key: str, value: str | None) -> str | None:
        if value is None:
            return None
        if not re.fullmatch(r"[0-9a-fA-F]{64}", value):
            raise ValueError("SHA-256 must be 64 hexadecimal characters.")
        return value.lower()


class ProjectDocument(MutableRecord, Base):
    __tablename__ = "uniflow_project_document"
    __table_args__ = (UniqueConstraint("project_id", "file_id"),)
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_file.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AssignmentRuleSet(MutableRecord, Base):
    __tablename__ = "uniflow_assignment_rule_set"
    __table_args__ = (
        UniqueConstraint("family_key", "revision"),
        CheckConstraint("revision >= 1", name="positive_revision"),
        CheckConstraint(
            "min_team_size >= 1 AND max_team_size >= min_team_size",
            name="team_size_range",
        ),
        CheckConstraint(
            "max_projects_per_student >= 1", name="positive_project_limit"
        ),
        CheckConstraint(
            "preference_closes_at IS NULL OR preference_opens_at IS NULL OR preference_closes_at > preference_opens_at",
            name="preference_window",
        ),
    )
    family_key: Mapped[UUID] = mapped_column(Uuid, default=uuid4, index=True)
    revision: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    name: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    state: Mapped[RuleState] = mapped_column(
        enum_type(RuleState, "rule_state"),
        default=RuleState.DRAFT,
        server_default="draft",
        index=True,
    )
    min_team_size: Mapped[int] = mapped_column(
        Integer, default=3, server_default="3"
    )
    max_team_size: Mapped[int] = mapped_column(
        Integer, default=5, server_default="5"
    )
    max_projects_per_student: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    require_all_skills: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    enforce_availability: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    allow_unranked_projects: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    preference_opens_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    preference_closes_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AssignmentCriterion(MutableRecord, Base):
    __tablename__ = "uniflow_assignment_criterion"
    __table_args__ = (
        UniqueConstraint("rule_set_id", "kind"),
        CheckConstraint("weight >= 0", name="nonnegative_weight"),
        CheckConstraint("position >= 1", name="positive_position"),
    )
    rule_set_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_assignment_rule_set.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    kind: Mapped[CriterionKind] = mapped_column(
        enum_type(CriterionKind, "criterion_kind"),
        default=CriterionKind.SKILL_MATCH,
        server_default="skill_match",
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("1"), server_default="1"
    )
    is_hard_constraint: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    position: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    minimum_score: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 4), nullable=True
    )
    parameters: Mapped[dict[str, str | int | float | bool]] = mapped_column(
        JSON, default=dict
    )


class AssignmentRound(MutableRecord, Base):
    __tablename__ = "uniflow_assignment_round"
    name: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    rule_set_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_assignment_rule_set.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    state: Mapped[AssignmentState] = mapped_column(
        enum_type(AssignmentState, "round_state"),
        default=AssignmentState.PROPOSED,
        server_default="proposed",
    )
    initiated_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    algorithm_version: Mapped[str] = mapped_column(
        String(80), default="", server_default=""
    )
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class StudentPreference(MutableRecord, Base):
    __tablename__ = "uniflow_student_preference"
    __table_args__ = (
        UniqueConstraint(
            "round_id",
            "student_id",
            "project_id",
            name="uq_preference_round_student_project",
        ),
        UniqueConstraint(
            "round_id",
            "student_id",
            "rank",
            name="uq_preference_round_student_rank",
        ),
        CheckConstraint("rank >= 1", name="positive_rank"),
    )
    round_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_assignment_round.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    student_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    rationale: Mapped[str] = mapped_column(Text, default="", server_default="")
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class TeamAssignment(MutableRecord, Base):
    __tablename__ = "uniflow_team_assignment"
    __table_args__ = (
        UniqueConstraint("round_id", "project_id"),
        UniqueConstraint("id", "project_id"),
        CheckConstraint(
            "NOT is_manual_override OR (overridden_by_id IS NOT NULL AND overridden_at IS NOT NULL AND length(trim(override_reason)) > 0)",
            name="override_metadata",
        ),
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    round_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_assignment_round.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    advisor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    state: Mapped[AssignmentState] = mapped_column(
        enum_type(AssignmentState, "assignment_state"),
        default=AssignmentState.PROPOSED,
        server_default="proposed",
        index=True,
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    assigned_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_manual_override: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    overridden_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    overridden_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    override_reason: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    supersedes_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_team_assignment.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )


class TeamMembership(MutableRecord, Base):
    __tablename__ = "uniflow_team_membership"
    __table_args__ = (
        UniqueConstraint("team_id", "student_id"),
        CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at", name="membership_dates"
        ),
        CheckConstraint(
            "NOT is_manual_override OR (overridden_by_id IS NOT NULL AND overridden_at IS NOT NULL AND length(trim(override_reason)) > 0)",
            name="override_metadata",
        ),
    )
    team_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_team_assignment.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    student_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    role: Mapped[MemberRole] = mapped_column(
        enum_type(MemberRole, "member_role"),
        default=MemberRole.MEMBER,
        server_default="member",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    assigned_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    is_manual_override: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    overridden_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    overridden_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    override_reason: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )


class MilestoneTemplate(MutableRecord, Base):
    __tablename__ = "uniflow_milestone_template"
    __table_args__ = (
        UniqueConstraint("family_key", "revision"),
        CheckConstraint("revision >= 1", name="positive_revision"),
    )
    family_key: Mapped[UUID] = mapped_column(Uuid, default=uuid4, index=True)
    revision: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    name: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )


class MilestoneTemplateItem(MutableRecord, Base):
    __tablename__ = "uniflow_milestone_template_item"
    __table_args__ = (
        UniqueConstraint("template_id", "position"),
        CheckConstraint(
            "position >= 1 AND due_offset_days >= 0",
            name="position_offset_range",
        ),
        CheckConstraint("weight >= 0", name="weight_nonnegative"),
    )
    template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_milestone_template.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    acceptance_criteria: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    position: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    due_offset_days: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    requires_deliverable: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("1"), server_default="1"
    )


class ProjectMilestone(MutableRecord, Base):
    __tablename__ = "uniflow_project_milestone"
    __table_args__ = (
        UniqueConstraint("project_id", "position"),
        UniqueConstraint("id", "project_id"),
        CheckConstraint(
            "position >= 1 AND weight >= 0", name="position_weight_range"
        ),
        Index("ix_uniflow_milestone_state_due", "state", "due_at"),
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    template_item_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_milestone_template_item.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    acceptance_criteria: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    position: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("1"), server_default="1"
    )
    requires_deliverable: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    state: Mapped[MilestoneState] = mapped_column(
        enum_type(MilestoneState, "milestone_state"),
        default=MilestoneState.NOT_STARTED,
        server_default="not_started",
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    original_due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    accepted_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )


class Deliverable(MutableRecord, Base):
    __tablename__ = "uniflow_deliverable"
    __table_args__ = (
        UniqueConstraint("id", "project_id"),
        ForeignKeyConstraint(
            ["milestone_id", "project_id"],
            [
                "uniflow_project_milestone.id",
                "uniflow_project_milestone.project_id",
            ],
            ondelete="RESTRICT",
        ),
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    milestone_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )


class DeliverableSubmission(MutableRecord, Base):
    __tablename__ = "uniflow_deliverable_submission"
    __table_args__ = (
        UniqueConstraint("deliverable_id", "revision"),
        UniqueConstraint("id", "project_id"),
        CheckConstraint("revision >= 1", name="positive_revision"),
        ForeignKeyConstraint(
            ["deliverable_id", "project_id"],
            ["uniflow_deliverable.id", "uniflow_deliverable.project_id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["team_id", "project_id"],
            [
                "uniflow_team_assignment.id",
                "uniflow_team_assignment.project_id",
            ],
            ondelete="RESTRICT",
        ),
        Index("ix_uniflow_submission_state_time", "state", "submitted_at"),
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    deliverable_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    team_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    revision: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    state: Mapped[SubmissionState] = mapped_column(
        enum_type(SubmissionState, "submission_state"),
        default=SubmissionState.DRAFT,
        server_default="draft",
    )
    submitted_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, default="", server_default="")
    revision_notes: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    reviewed_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_notes: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )


class SubmissionFile(Identity, Base):
    __tablename__ = "uniflow_submission_file"
    __table_args__ = (UniqueConstraint("submission_id", "file_id"),)
    submission_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_deliverable_submission.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_file.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    caption: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )


class AdvisorEvaluation(MutableRecord, Base):
    __tablename__ = "uniflow_advisor_evaluation"
    __table_args__ = (
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= maximum_score)",
            name="score_range",
        ),
        CheckConstraint(
            "maximum_score > 0 AND revision >= 1", name="maximum_revision_range"
        ),
        UniqueConstraint("evaluation_key", "revision"),
        ForeignKeyConstraint(
            ["submission_id", "project_id"],
            [
                "uniflow_deliverable_submission.id",
                "uniflow_deliverable_submission.project_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["milestone_id", "project_id"],
            [
                "uniflow_project_milestone.id",
                "uniflow_project_milestone.project_id",
            ],
            ondelete="RESTRICT",
        ),
    )
    evaluation_key: Mapped[UUID] = mapped_column(Uuid, default=uuid4)
    revision: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    advisor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    student_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    milestone_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    submission_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    maximum_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("100"), server_default="100"
    )
    comments: Mapped[str] = mapped_column(Text, default="", server_default="")
    rubric_name: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    finalized_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class EvaluationCriterionScore(Identity, Base):
    __tablename__ = "uniflow_evaluation_criterion_score"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "criterion"),
        CheckConstraint(
            "maximum_score > 0 AND score >= 0 AND score <= maximum_score AND weight >= 0",
            name="score_weight_range",
        ),
    )
    evaluation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_advisor_evaluation.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    criterion: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0"), server_default="0"
    )
    maximum_score: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("100"), server_default="100"
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("1"), server_default="1"
    )
    comments: Mapped[str] = mapped_column(Text, default="", server_default="")


class SponsorFeedback(MutableRecord, Base):
    __tablename__ = "uniflow_sponsor_feedback"
    __table_args__ = (
        UniqueConstraint("feedback_key", "revision"),
        CheckConstraint(
            "rating IS NULL OR rating BETWEEN 1 AND 5", name="rating_range"
        ),
        CheckConstraint("revision >= 1", name="positive_revision"),
        ForeignKeyConstraint(
            ["milestone_id", "project_id"],
            [
                "uniflow_project_milestone.id",
                "uniflow_project_milestone.project_id",
            ],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["submission_id", "project_id"],
            [
                "uniflow_deliverable_submission.id",
                "uniflow_deliverable_submission.project_id",
            ],
            ondelete="RESTRICT",
        ),
    )
    feedback_key: Mapped[UUID] = mapped_column(Uuid, default=uuid4)
    revision: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1"
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    sponsor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    milestone_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    submission_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comments: Mapped[str] = mapped_column(Text, default="", server_default="")
    requested_changes: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Meeting(MutableRecord, Base):
    __tablename__ = "uniflow_meeting"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="time_order"),
        Index("ix_uniflow_meeting_project_start", "project_id", "starts_at"),
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"), nullable=True
    )
    organizer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )
    agenda: Mapped[str] = mapped_column(Text, default="", server_default="")
    minutes: Mapped[str] = mapped_column(Text, default="", server_default="")
    location: Mapped[str] = mapped_column(
        String(500), default="", server_default=""
    )
    conference_url: Mapped[str | None] = mapped_column(
        String(2048), nullable=True
    )
    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    state: Mapped[MeetingState] = mapped_column(
        enum_type(MeetingState, "meeting_state"),
        default=MeetingState.SCHEDULED,
        server_default="scheduled",
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_reason: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )


class MeetingAttendee(MutableRecord, Base):
    __tablename__ = "uniflow_meeting_attendee"
    __table_args__ = (UniqueConstraint("meeting_id", "user_id"),)
    meeting_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_meeting.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    attendance: Mapped[Attendance] = mapped_column(
        enum_type(Attendance, "attendance_state"),
        default=Attendance.INVITED,
        server_default="invited",
    )
    is_required: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RiskIssue(MutableRecord, Base):
    __tablename__ = "uniflow_risk_issue"
    __table_args__ = (
        CheckConstraint(
            "likelihood BETWEEN 1 AND 5 AND impact BETWEEN 1 AND 5",
            name="risk_score_range",
        ),
        Index(
            "ix_uniflow_risk_project_state", "project_id", "state", "severity"
        ),
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"), nullable=True
    )
    reported_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    kind: Mapped[IssueKind] = mapped_column(
        enum_type(IssueKind, "issue_kind"),
        default=IssueKind.RISK,
        server_default="risk",
    )
    severity: Mapped[Severity] = mapped_column(
        enum_type(Severity, "issue_severity"),
        default=Severity.MEDIUM,
        server_default="medium",
    )
    state: Mapped[IssueState] = mapped_column(
        enum_type(IssueState, "issue_state"),
        default=IssueState.OPEN,
        server_default="open",
    )
    title: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    likelihood: Mapped[int] = mapped_column(
        Integer, default=3, server_default="3"
    )
    impact: Mapped[int] = mapped_column(Integer, default=3, server_default="3")
    mitigation_plan: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    resolution: Mapped[str] = mapped_column(Text, default="", server_default="")
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Notification(MutableRecord, Base):
    __tablename__ = "uniflow_notification"
    __table_args__ = (
        UniqueConstraint("recipient_id", "deduplication_key"),
        CheckConstraint(
            "attempts >= 0 AND max_attempts >= 1", name="attempt_range"
        ),
        CheckConstraint(
            "read_state != 'read' OR read_at IS NOT NULL", name="read_timestamp"
        ),
        CheckConstraint(
            "processing_state != 'processing' OR (locked_at IS NOT NULL AND lock_token IS NOT NULL)",
            name="processing_lease",
        ),
        Index(
            "ix_uniflow_notification_queue",
            "processing_state",
            "scheduled_at",
            "next_attempt_at",
        ),
        Index(
            "ix_uniflow_notification_inbox",
            "recipient_id",
            "read_state",
            "created_at",
        ),
    )
    recipient_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"), nullable=True
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    kind: Mapped[NotificationKind] = mapped_column(
        enum_type(NotificationKind, "notification_kind"),
        default=NotificationKind.GENERAL,
        server_default="general",
    )
    title: Mapped[str] = mapped_column(
        String(240), default="", server_default=""
    )
    body: Mapped[str] = mapped_column(Text, default="", server_default="")
    action_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    deduplication_key: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    processing_state: Mapped[ProcessingState] = mapped_column(
        enum_type(ProcessingState, "notification_processing"),
        default=ProcessingState.PENDING,
        server_default="pending",
    )
    read_state: Mapped[ReadState] = mapped_column(
        enum_type(ReadState, "notification_read"),
        default=ReadState.UNREAD,
        server_default="unread",
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    attempts: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, default=5, server_default="5"
    )
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lock_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    lock_token: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AuditEvent(Identity, Base):
    __tablename__ = "uniflow_audit_event"
    __table_args__ = (
        Index(
            "ix_uniflow_audit_target_time",
            "entity_type",
            "entity_id",
            "created_at",
        ),
        Index("ix_uniflow_audit_actor_time", "actor_id", "created_at"),
        CheckConstraint("length(trim(action)) > 0", name="nonempty_action"),
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"), nullable=True
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_project.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(120), default="record.created", server_default="record.created"
    )
    entity_type: Mapped[str] = mapped_column(
        String(120), default="", server_default=""
    )
    entity_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    request_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(Text, default="", server_default="")
    before_values: Mapped[dict[str, str | int | float | bool | None]] = (
        mapped_column(JSON, default=dict)
    )
    after_values: Mapped[dict[str, str | int | float | bool | None]] = (
        mapped_column(JSON, default=dict)
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


@event.listens_for(AuditEvent, "before_update")
@event.listens_for(AuditEvent, "before_delete")
def prevent_audit_mutation(mapper, connection, target) -> None:
    raise ValueError("Audit events are append-only.")


@event.listens_for(Session, "do_orm_execute")
def prevent_bulk_audit_mutation(execute_state: ORMExecuteState) -> None:
    if execute_state.is_update or execute_state.is_delete:
        table = getattr(execute_state.statement, "table", None)
        if table is not None and table.name == AuditEvent.__tablename__:
            raise ValueError("Audit events are append-only.")


class SavedReport(MutableRecord, Base):
    __tablename__ = "uniflow_saved_report"
    __table_args__ = (UniqueConstraint("owner_id", "name"),)
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200), default="", server_default=""
    )
    description: Mapped[str] = mapped_column(
        Text, default="", server_default=""
    )
    kind: Mapped[ReportKind] = mapped_column(
        enum_type(ReportKind, "report_kind"),
        default=ReportKind.PROJECTS,
        server_default="projects",
    )
    filters: Mapped[dict[str, str | int | float | bool | list[str]]] = (
        mapped_column(JSON, default=dict)
    )
    columns: Mapped[list[str]] = mapped_column(JSON, default=list)
    sort_fields: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )


class ReportExport(MutableRecord, Base):
    __tablename__ = "uniflow_report_export"
    __table_args__ = (
        CheckConstraint(
            "row_count IS NULL OR row_count >= 0", name="row_count_nonnegative"
        ),
        CheckConstraint(
            "state != 'ready' OR (file_id IS NOT NULL AND completed_at IS NOT NULL)",
            name="ready_artifact",
        ),
        Index("ix_uniflow_export_state_created", "state", "created_at"),
    )
    saved_report_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_saved_report.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    requested_by_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_user.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("uniflow_file.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    kind: Mapped[ReportKind] = mapped_column(
        enum_type(ReportKind, "export_report_kind"),
        default=ReportKind.PROJECTS,
        server_default="projects",
    )
    format: Mapped[ExportFormat] = mapped_column(
        enum_type(ExportFormat, "export_format"),
        default=ExportFormat.CSV,
        server_default="csv",
    )
    state: Mapped[ExportState] = mapped_column(
        enum_type(ExportState, "export_state"),
        default=ExportState.QUEUED,
        server_default="queued",
    )
    filters_snapshot: Mapped[
        dict[str, str | int | float | bool | list[str]]
    ] = mapped_column(JSON, default=dict)
    columns_snapshot: Mapped[list[str]] = mapped_column(JSON, default=list)
    sort_snapshot: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_as_of: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
