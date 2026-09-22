import reflex as rx

import asyncio
import bcrypt
import csv
import hashlib
import io
import logging
import time as clock
from datetime import datetime, timedelta, timezone, time
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import reflex_xy
from sqlalchemy import select, delete, text
from sqlalchemy.orm import Session
from app import models as m


def now() -> datetime:
    return datetime.now(timezone.utc)


class StudioState(rx.State):
    _uid: str = ""
    _expires: float = 0.0
    _login_after: float = 0.0
    _preview_stamp: str = ""
    signed_in: bool = False
    name: str = ""
    roles: list[str] = []
    error: str = ""
    busy: bool = False
    registering: bool = False
    section_name: str = "dashboard"
    search: str = ""
    skill_filter: str = ""
    projects: list[dict[str, str]] = []
    selected: dict[str, str] = {
        "id": "",
        "title": "",
        "summary": "",
        "description": "",
        "skills": "",
        "objectives": "",
        "min": "3",
        "max": "5",
        "deadline": "",
        "version": "",
        "lifecycle": "",
        "sponsor": "",
        "advisor": "",
        "health": "unknown",
        "status": "not_started",
        "review": "",
        "editable": "no",
    }
    milestones: list[dict[str, str]] = []
    submissions: list[dict[str, str]] = []
    documents: list[dict[str, str]] = []
    roster: list[dict[str, str]] = []
    timeline: list[dict[str, str]] = []
    meetings: list[dict[str, str]] = []
    risks: list[dict[str, str]] = []
    feedback: list[dict[str, str]] = []
    people: list[dict[str, str]] = []
    students: list[dict[str, str]] = []
    advisors: list[dict[str, str]] = []
    preferences: list[dict[str, str]] = []
    templates: list[dict[str, str]] = []
    notifications: list[dict[str, str]] = []
    staged_files: list[dict[str, str]] = []
    preview: list[dict[str, str]] = []
    report_rows: list[dict[str, str]] = []
    faculty: list[str] = []
    loads: list[int] = []
    stats: dict[str, str] = {
        "projects": "0",
        "late": "0",
        "missing": "0",
        "choice": "—",
        "unstaffed": "0",
    }
    profile: dict[str, str] = {
        "name": "",
        "biography": "",
        "skills": "",
        "hours": "10",
        "availability": "",
    }
    round_info: dict[str, str] = {
        "id": "",
        "name": "No open round",
        "closes": "",
        "version": "",
    }
    queue_status: str = "Not scanned this session"
    scanning: bool = False
    pending_action: str = ""
    pending_target: str = ""
    pending_label: str = ""
    _pending_data: dict[str, str] = {}

    @rx.var
    def is_admin(self) -> bool:
        return bool(
            set(self.roles) & {"program_administrator", "system_administrator"}
        )

    @rx.var
    def is_system(self) -> bool:
        return "system_administrator" in self.roles

    @rx.var
    def is_student(self) -> bool:
        return "student" in self.roles

    @rx.var
    def can_propose(self) -> bool:
        return self.is_admin or "sponsor" in self.roles

    @rx.var
    def unread(self) -> int:
        return sum(n["read"] == "unread" for n in self.notifications)

    @rx.var
    def nav(self) -> list[dict[str, str]]:
        items = [
            ("dashboard", "Dashboard", "landmark"),
            ("marketplace", "Marketplace", "compass"),
            ("projects", "Projects", "folders"),
            ("notifications", "Notifications", "bell"),
        ]
        if self.is_student:
            items.insert(2, ("preferences", "Preferences", "list-ordered"))
        if self.is_admin:
            items.extend(
                [
                    ("reviews", "Reviews", "clipboard-check"),
                    ("assignments", "Assignments", "git-branch"),
                    ("templates", "Templates", "files"),
                    ("reports", "Reports", "chart-no-axes-combined"),
                ]
            )
        if self.is_system:
            items.append(("users", "User administration", "users"))
        return [{"id": a, "label": b, "icon": c} for a, b, c in items]

    @rx.var
    def visible_projects(self) -> list[dict[str, str]]:
        rows = self.projects
        if self.section_name == "marketplace":
            rows = [
                p
                for p in rows
                if p["lifecycle"] in ("approved", "matching")
                and p["assigned"] == "no"
            ]
        elif self.section_name == "reviews":
            rows = [
                p
                for p in rows
                if p["lifecycle"]
                in ("submitted", "under_review", "changes_requested")
            ]
        elif self.section_name == "projects":
            rows = [p for p in rows if p["workspace"] == "yes"]
        return [
            p
            for p in rows
            if self.search.lower()
            in f"{p['title']} {p['summary']} {p['sponsor']}".lower()
            and self.skill_filter.lower() in p["skills"].lower()
        ]

    @rx.var
    def filtered_reports(self) -> list[dict[str, str]]:
        return [
            r
            for r in self.report_rows
            if self.search.lower() in " ".join(r.values()).lower()
        ]

    @reflex_xy.data
    def faculty_data(self) -> dict[str, list[str] | list[int]]:
        return {"advisor": self.faculty, "projects": self.loads}

    def _lock(self, db: Session):
        db.execute(text("SELECT pg_advisory_xact_lock(74621031)"))

    def _actor(self, db: Session, uid: str = "") -> tuple[m.User, set[m.Role]]:
        identity = uid or self._uid
        if not identity or (not uid and self._expires < clock.time()):
            raise ValueError("Your session has expired. Please sign in again.")
        user = db.get(m.User, UUID(identity))
        if not user or not user.is_active:
            raise ValueError("Please sign in with an active account.")
        roles = set(
            db.scalars(
                select(m.UserRole.role).where(
                    m.UserRole.user_id == user.id,
                    m.UserRole.revoked_at.is_(None),
                )
            )
        )
        return user, roles

    def _admin(self, roles: set[m.Role]):
        if not roles & {
            m.Role.SYSTEM_ADMINISTRATOR,
            m.Role.PROGRAM_ADMINISTRATOR,
        }:
            raise ValueError("Administrator permission is required.")

    def _team(self, db: Session, pid: UUID):
        return db.scalar(
            select(m.TeamAssignment).where(
                m.TeamAssignment.project_id == pid,
                m.TeamAssignment.state == m.AssignmentState.CONFIRMED,
            )
        )

    def _members(self, db: Session, team) -> list[UUID]:
        if not team:
            return []
        return list(
            db.scalars(
                select(m.TeamMembership.student_id).where(
                    m.TeamMembership.team_id == team.id,
                    m.TeamMembership.left_at.is_(None),
                )
            )
        )

    def _access(
        self,
        db: Session,
        p: m.Project,
        user: m.User,
        roles: set[m.Role],
        workspace: bool = False,
    ):
        if not p:
            raise ValueError("Project not found.")
        if (
            roles & {m.Role.SYSTEM_ADMINISTRATOR, m.Role.PROGRAM_ADMINISTRATOR}
            or (user.id == p.sponsor_id and m.Role.SPONSOR in roles)
            or (user.id == p.advisor_id and m.Role.FACULTY_ADVISOR in roles)
            or (
                m.Role.STUDENT in roles
                and user.id in self._members(db, self._team(db, p.id))
            )
        ):
            return
        if not workspace and p.lifecycle in (
            m.Lifecycle.APPROVED,
            m.Lifecycle.MATCHING,
        ):
            return
        raise ValueError("This project is not available to your account.")

    def _audit(
        self,
        db: Session,
        actor: UUID,
        action: str,
        pid: UUID | None = None,
        reason: str = "",
        entity: UUID | None = None,
    ):
        db.add(
            m.AuditEvent(
                actor_id=actor,
                project_id=pid,
                action=action,
                entity_type="project" if pid else "studio",
                entity_id=entity or pid,
                reason=reason,
            )
        )

    def _notice(
        self,
        db: Session,
        recipient: UUID | None,
        title: str,
        pid: UUID | None,
        key: str,
        queued: bool = False,
    ):
        if recipient and not db.scalar(
            select(m.Notification.id).where(
                m.Notification.recipient_id == recipient,
                m.Notification.deduplication_key == key,
            )
        ):
            db.add(
                m.Notification(
                    recipient_id=recipient,
                    project_id=pid,
                    title=title,
                    body=title,
                    deduplication_key=key,
                    action_path="/studio/projects",
                    processing_state=m.ProcessingState.PENDING
                    if queued
                    else m.ProcessingState.DELIVERED,
                    delivered_at=None if queued else now(),
                )
            )
            db.flush()

    def _date(self, value: str) -> datetime | None:
        return (
            datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
            if value
            else None
        )

    def _round(self, db: Session, required: bool = True):
        row = db.scalar(
            select(m.AssignmentRound)
            .where(m.AssignmentRound.state == m.AssignmentState.PROPOSED)
            .order_by(m.AssignmentRound.created_at.desc())
        )
        if required and not row:
            raise ValueError(
                "An administrator must open a preference round first."
            )
        return row

    def _preference_open(self, db: Session):
        row = self._round(db)
        rule = db.get(m.AssignmentRuleSet, row.rule_set_id)
        if rule.preference_opens_at and now() < rule.preference_opens_at:
            raise ValueError("Preferences are not open yet.")
        if rule.preference_closes_at and now() >= rule.preference_closes_at:
            raise ValueError("The preference deadline has passed.")
        return row

    @rx.event
    def toggle_registration(self):
        self.registering = not self.registering
        self.error = ""

    @rx.event
    async def authenticate(self, data: dict[str, Any]):
        self.error = ""
        if clock.time() < self._login_after:
            self.error = "Please wait a moment before trying again."
            return
        self.busy = True
        yield
        try:
            email = str(data.get("email", "")).strip().lower()
            password = str(data.get("password", ""))
            if not email or not password or len(password.encode()) > 72:
                raise ValueError(
                    "Enter an email and a password of at most 72 bytes."
                )
            encoded = (
                await asyncio.to_thread(
                    bcrypt.hashpw, password.encode(), bcrypt.gensalt()
                )
                if self.registering
                else b""
            )
            async with rx.asession() as db:
                await db.run_sync(lambda sync_db: self._lock(sync_db))
                user = await db.scalar(
                    select(m.User).where(m.User.email == email)
                )
                if self.registering:
                    if (
                        len(password) < 10
                        or not str(data.get("name", "")).strip()
                    ):
                        raise ValueError(
                            "Enter your name and a password of at least 10 characters."
                        )
                    if user:
                        raise ValueError(
                            "Unable to register this email. Try signing in instead."
                        )
                    user = m.User(
                        email=email,
                        password_hash=encoded.decode(),
                        is_active=True,
                        display_name=str(data["name"]).strip()[:200],
                        password_changed_at=now(),
                    )
                    db.add(user)
                    await db.flush()
                    first = not await db.scalar(
                        select(m.AdministratorBootstrap.id)
                    )
                    db.add(
                        m.UserRole(
                            user_id=user.id,
                            role=m.Role.SYSTEM_ADMINISTRATOR
                            if first
                            else m.Role.STUDENT,
                            granted_by_id=user.id,
                        )
                    )
                    await db.flush()
                    if first:
                        db.add(
                            m.AdministratorBootstrap(
                                singleton_key=1,
                                user_id=user.id,
                                role=m.Role.SYSTEM_ADMINISTRATOR,
                            )
                        )
                    await db.run_sync(
                        lambda sync_db: self._audit(
                            sync_db, user.id, "account.registered"
                        )
                    )
                elif (
                    not user
                    or not user.is_active
                    or not user.password_hash
                    or not bcrypt.checkpw(
                        password.encode(), user.password_hash.encode()
                    )
                ):
                    raise ValueError("Email or password is incorrect.")
                user.last_login_at = now()
                identity = str(user.id)
                await db.commit()
            self._uid = identity
            self._expires = clock.time() + 43200
            self.signed_in = True
            yield StudioState.load
            yield rx.redirect("/studio/dashboard")
        except ValueError as e:
            self.error = str(e)
            self._login_after = clock.time() + 2
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "Unable to sign in. Please try again."
            self._login_after = clock.time() + 2
        finally:
            self.busy = False

    @rx.event
    def logout(self):
        self._uid = ""
        self._expires = 0
        self.signed_in = False
        self.roles = []
        self.projects = []
        self.people = []
        self.notifications = []
        self.staged_files = []
        self.preview = []
        self.report_rows = []
        self.error = ""
        return rx.redirect("/")

    @rx.event
    def set_search(self, value: str):
        self.search = value

    @rx.event
    def set_skill_filter(self, value: str):
        self.skill_filter = value

    @rx.event
    def load(self):
        if not self._uid:
            self.signed_in = False
            return
        try:
            section = str(self.router.page.params.get("section", "dashboard"))
            with rx.session() as db:
                user, roles = self._actor(db)
                self.name = user.display_name or user.email or "Member"
                self.roles = sorted(r.value for r in roles)
                self.signed_in = True
                allowed = {n["id"] for n in self.nav}
                self.section_name = (
                    section if section in allowed else "dashboard"
                )
                self._load_data(db, user, roles)
            self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                str(e)
                if isinstance(e, ValueError)
                else "Could not load the workspace. Please refresh."
            )
            if isinstance(e, ValueError):
                self.signed_in = False

    def _load_data(self, db: Session, user: m.User, roles: set[m.Role]):
        admin = bool(
            roles & {m.Role.SYSTEM_ADMINISTRATOR, m.Role.PROGRAM_ADMINISTRATOR}
        )
        users = {
            u.id: u
            for u in db.scalars(
                select(m.User).where(m.User.is_active.is_(True))
            )
        }
        all_projects = list(
            db.scalars(select(m.Project).order_by(m.Project.created_at.desc()))
        )
        self.projects = []
        for p in all_projects:
            team = self._team(db, p.id)
            mine = (
                admin
                or user.id in (p.sponsor_id, p.advisor_id)
                or user.id in self._members(db, team)
            )
            if not mine and p.lifecycle not in (
                m.Lifecycle.APPROVED,
                m.Lifecycle.MATCHING,
            ):
                continue
            skills = list(
                db.scalars(
                    select(m.Skill.name)
                    .join(m.ProjectSkill, m.ProjectSkill.skill_id == m.Skill.id)
                    .where(m.ProjectSkill.project_id == p.id)
                )
            )
            self.projects.append(
                {
                    "id": str(p.id),
                    "title": p.title,
                    "summary": p.summary,
                    "lifecycle": p.lifecycle.value,
                    "label": "assigned"
                    if team and p.lifecycle == m.Lifecycle.MATCHING
                    else p.lifecycle.value.replace(
                        "matching", "open for preferences"
                    ).replace("_", " "),
                    "health": p.health.value,
                    "status": p.status.value,
                    "sponsor": users[p.sponsor_id].display_name
                    if p.sponsor_id in users
                    else "Unassigned",
                    "advisor": users[p.advisor_id].display_name
                    if p.advisor_id in users
                    else "Unassigned",
                    "skills": ", ".join(skills),
                    "capacity": f"{len(self._members(db, team))} / {p.preferred_max_team_size}",
                    "team_size": f"{p.preferred_min_team_size}–{p.preferred_max_team_size}",
                    "assigned": "yes" if team else "no",
                    "workspace": "yes" if mine else "no",
                }
            )
        r = self._round(db, False)
        self.round_info = {
            "id": "",
            "name": "No open round",
            "closes": "",
            "version": "",
        }
        self.preferences = []
        if r:
            rule = db.get(m.AssignmentRuleSet, r.rule_set_id)
            self.round_info = {
                "id": str(r.id),
                "name": r.name,
                "closes": rule.preference_closes_at.strftime(
                    "%d %b %Y, %H:%M UTC"
                )
                if rule.preference_closes_at
                else "No deadline",
                "version": str(r.version),
            }
            for pref in db.scalars(
                select(m.StudentPreference)
                .where(
                    m.StudentPreference.round_id == r.id,
                    m.StudentPreference.student_id == user.id,
                )
                .order_by(m.StudentPreference.rank)
            ):
                p = db.get(m.Project, pref.project_id)
                self.preferences.append(
                    {
                        "id": str(pref.id),
                        "title": p.title,
                        "rank": str(pref.rank),
                    }
                )
        skill_names = list(
            db.scalars(
                select(m.Skill.name)
                .join(m.UserSkill, m.UserSkill.skill_id == m.Skill.id)
                .where(m.UserSkill.user_id == user.id)
            )
        )
        schedule = db.scalar(
            select(m.SchedulingConstraint).where(
                m.SchedulingConstraint.user_id == user.id
            )
        )
        windows = list(
            db.scalars(
                select(m.AvailabilityWindow)
                .where(m.AvailabilityWindow.user_id == user.id)
                .order_by(m.AvailabilityWindow.weekday)
            )
        )
        self.profile = {
            "name": user.display_name,
            "biography": user.biography,
            "skills": ", ".join(skill_names),
            "hours": str(schedule.max_weekly_hours) if schedule else "10",
            "availability": "\n".join(
                f"{w.weekday} {w.start_time:%H:%M} {w.end_time:%H:%M}"
                for w in windows
                if w.start_time and w.end_time
            ),
        }
        self.notifications = [
            {
                "id": str(n.id),
                "title": n.title,
                "body": n.body,
                "read": n.read_state.value,
                "date": n.created_at.strftime("%d %b · %H:%M"),
                "project": str(n.project_id or ""),
            }
            for n in db.scalars(
                select(m.Notification)
                .where(
                    m.Notification.recipient_id == user.id,
                    m.Notification.processing_state
                    == m.ProcessingState.DELIVERED,
                )
                .order_by(m.Notification.created_at.desc())
            )
        ]
        self.templates = (
            [
                {"id": str(t.id), "name": t.name, "description": t.description}
                for t in db.scalars(
                    select(m.MilestoneTemplate).where(
                        m.MilestoneTemplate.is_active.is_(True)
                    )
                )
            ]
            if admin
            else []
        )
        self.people = []
        self.students = []
        self.advisors = []
        if admin:
            for u in users.values():
                ur = list(
                    db.scalars(
                        select(m.UserRole.role).where(
                            m.UserRole.user_id == u.id,
                            m.UserRole.revoked_at.is_(None),
                        )
                    )
                )
                item = {
                    "id": str(u.id),
                    "name": u.display_name or u.email or "Member",
                    "email": u.email or "",
                    "roles": ", ".join(role.value for role in ur),
                }
                if m.Role.SYSTEM_ADMINISTRATOR in roles:
                    self.people.append(item)
                if m.Role.STUDENT in ur:
                    self.students.append(item)
                if m.Role.FACULTY_ADVISOR in ur:
                    self.advisors.append(item)
            self._reports(db, all_projects, users)
        else:
            self.report_rows = []
            self.faculty = []
            self.loads = []
            self.stats = {
                "projects": str(
                    sum(p["workspace"] == "yes" for p in self.projects)
                ),
                "late": "0",
                "missing": "0",
                "choice": "—",
                "unstaffed": "0",
            }
        if self.selected["id"]:
            p = db.get(m.Project, UUID(self.selected["id"]))
            try:
                self._access(db, p, user, roles)
                self._detail(db, p, user, roles, users)
            except ValueError:
                self.selected = {**self.selected, "id": ""}

    def _reports(
        self, db: Session, projects: list[m.Project], users: dict[UUID, m.User]
    ):
        late = set()
        missing = 0
        self.report_rows = []
        staffed = set()
        total = 0
        top = 0
        for p in projects:
            team = self._team(db, p.id)
            members = self._members(db, team)
            if members:
                staffed.add(p.id)
            missed = 0
            for milestone in db.scalars(
                select(m.ProjectMilestone).where(
                    m.ProjectMilestone.project_id == p.id
                )
            ):
                if (
                    milestone.due_at
                    and milestone.due_at < now()
                    and milestone.state
                    not in (m.MilestoneState.ACCEPTED, m.MilestoneState.WAIVED)
                ):
                    late.add(p.id)
                    submission = db.scalar(
                        select(m.DeliverableSubmission.id)
                        .join(
                            m.Deliverable,
                            m.Deliverable.id
                            == m.DeliverableSubmission.deliverable_id,
                        )
                        .where(m.Deliverable.milestone_id == milestone.id)
                    )
                    if milestone.requires_deliverable and not submission:
                        missed += len(members)
            missing += missed
            for uid in members:
                total += 1
                pref = db.scalar(
                    select(m.StudentPreference).where(
                        m.StudentPreference.student_id == uid,
                        m.StudentPreference.project_id == p.id,
                        m.StudentPreference.round_id == team.round_id,
                    )
                )
                if pref and pref.rank <= 3:
                    top += 1
            self.report_rows.append(
                {
                    "project": p.title,
                    "lifecycle": p.lifecycle.value,
                    "schedule": "Behind schedule"
                    if p.id in late
                    else "No overdue milestones",
                    "missing": str(missed),
                    "advisor": users[p.advisor_id].display_name
                    if p.advisor_id in users
                    else "Unassigned",
                    "members": str(len(members)),
                    "staffing": "Staffed" if members else "Unstaffed",
                }
            )
        self.stats = {
            "projects": str(len(projects)),
            "late": str(len(late)),
            "missing": str(missing),
            "choice": f"{100 * top / total:.1f}%" if total else "—",
            "unstaffed": str(
                sum(
                    p.id not in staffed
                    and p.lifecycle
                    not in (
                        m.Lifecycle.ARCHIVED,
                        m.Lifecycle.CANCELLED,
                        m.Lifecycle.COMPLETED,
                    )
                    for p in projects
                )
            ),
        }
        self.faculty = [a["name"] for a in self.advisors]
        self.loads = [
            sum(
                str(p.advisor_id) == a["id"]
                and p.lifecycle
                not in (
                    m.Lifecycle.ARCHIVED,
                    m.Lifecycle.COMPLETED,
                    m.Lifecycle.CANCELLED,
                )
                for p in projects
            )
            for a in self.advisors
        ]

    @rx.event
    def open_project(self, project_id: str):
        try:
            with rx.session() as db:
                user, roles = self._actor(db)
                p = db.get(m.Project, UUID(project_id))
                self._access(db, p, user, roles)
                users = {u.id: u for u in db.scalars(select(m.User))}
                self._detail(db, p, user, roles, users)
            self.staged_files = []
            self.error = ""
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                str(e)
                if isinstance(e, ValueError)
                else "Could not open project."
            )

    @rx.event
    def close_project(self):
        self.selected = {**self.selected, "id": ""}
        self.staged_files = []

    def _detail(
        self,
        db: Session,
        p: m.Project,
        user: m.User,
        roles: set[m.Role],
        users: dict[UUID, m.User],
    ):
        admin = bool(
            roles & {m.Role.SYSTEM_ADMINISTRATOR, m.Role.PROGRAM_ADMINISTRATOR}
        )
        team = self._team(db, p.id)
        workspace = (
            admin
            or user.id in (p.sponsor_id, p.advisor_id)
            or user.id in self._members(db, team)
        )
        skills = list(
            db.scalars(
                select(m.Skill.name)
                .join(m.ProjectSkill, m.ProjectSkill.skill_id == m.Skill.id)
                .where(m.ProjectSkill.project_id == p.id)
            )
        )
        self.selected = {
            "id": str(p.id),
            "title": p.title,
            "summary": p.summary,
            "description": p.description,
            "skills": ", ".join(skills),
            "objectives": "\n".join(
                db.scalars(
                    select(m.ProjectObjective.description)
                    .where(m.ProjectObjective.project_id == p.id)
                    .order_by(m.ProjectObjective.position)
                )
            ),
            "min": str(p.preferred_min_team_size),
            "max": str(p.preferred_max_team_size),
            "deadline": p.proposal_deadline.strftime("%Y-%m-%dT%H:%M")
            if p.proposal_deadline
            else "",
            "version": str(p.version),
            "lifecycle": "assigned"
            if team and p.lifecycle == m.Lifecycle.MATCHING
            else p.lifecycle.value,
            "sponsor": users[p.sponsor_id].display_name
            if p.sponsor_id in users
            else "Unassigned",
            "advisor": users[p.advisor_id].display_name
            if p.advisor_id in users
            else "Unassigned",
            "health": p.health.value,
            "status": p.status.value,
            "review": p.review_notes if workspace else "",
            "editable": "yes"
            if admin
            or (
                m.Role.SPONSOR in roles
                and p.sponsor_id == user.id
                and p.lifecycle
                in (m.Lifecycle.DRAFT, m.Lifecycle.CHANGES_REQUESTED)
                and (not p.proposal_deadline or now() < p.proposal_deadline)
            )
            else "no",
        }
        self.documents = [
            {
                "id": str(f.id),
                "name": f.original_filename,
                "key": f.storage_key or "",
            }
            for f in db.scalars(
                select(m.FileMetadata)
                .join(
                    m.ProjectDocument,
                    m.ProjectDocument.file_id == m.FileMetadata.id,
                )
                .where(
                    m.ProjectDocument.project_id == p.id,
                    m.ProjectDocument.withdrawn_at.is_(None),
                )
            )
        ]
        (
            self.milestones,
            self.submissions,
            self.roster,
            self.timeline,
            self.meetings,
            self.risks,
            self.feedback,
        ) = [], [], [], [], [], [], []
        if not workspace:
            return
        self.roster = [
            {
                "id": str(uid),
                "name": users[uid].display_name if uid in users else "Member",
            }
            for uid in self._members(db, team)
        ]
        for milestone in db.scalars(
            select(m.ProjectMilestone)
            .where(m.ProjectMilestone.project_id == p.id)
            .order_by(m.ProjectMilestone.position)
        ):
            self.milestones.append(
                {
                    "id": str(milestone.id),
                    "title": milestone.title,
                    "state": milestone.state.value,
                    "due": milestone.due_at.strftime("%d %b %Y %H:%M UTC")
                    if milestone.due_at
                    else "Not scheduled",
                    "version": str(milestone.version),
                    "criteria": milestone.acceptance_criteria,
                }
            )
        for sub in db.scalars(
            select(m.DeliverableSubmission)
            .where(m.DeliverableSubmission.project_id == p.id)
            .order_by(m.DeliverableSubmission.created_at.desc())
        ):
            d = db.get(m.Deliverable, sub.deliverable_id)
            files = list(
                db.scalars(
                    select(m.FileMetadata.original_filename)
                    .join(
                        m.SubmissionFile,
                        m.SubmissionFile.file_id == m.FileMetadata.id,
                    )
                    .where(m.SubmissionFile.submission_id == sub.id)
                )
            )
            self.submissions.append(
                {
                    "id": str(sub.id),
                    "title": f"{d.title} · version {sub.revision}",
                    "notes": sub.content,
                    "files": ", ".join(files),
                    "date": sub.submitted_at.strftime("%d %b %Y %H:%M UTC")
                    if sub.submitted_at
                    else "",
                }
            )
        self.timeline = [
            {
                "title": a.action.replace(".", " · ").replace("_", " "),
                "notes": a.reason,
                "date": a.created_at.strftime("%d %b %Y %H:%M"),
                "actor": users[a.actor_id].display_name
                if a.actor_id in users
                else "System",
            }
            for a in db.scalars(
                select(m.AuditEvent)
                .where(m.AuditEvent.project_id == p.id)
                .order_by(m.AuditEvent.created_at.desc())
                .limit(100)
            )
        ]
        self.meetings = [
            {
                "title": x.title,
                "notes": x.minutes,
                "date": x.starts_at.strftime("%d %b %Y %H:%M UTC")
                if x.starts_at
                else "",
                "location": x.location,
            }
            for x in db.scalars(
                select(m.Meeting)
                .where(m.Meeting.project_id == p.id)
                .order_by(m.Meeting.starts_at.desc())
            )
        ]
        self.risks = [
            {
                "id": str(x.id),
                "title": x.title,
                "severity": x.severity.value,
                "state": x.state.value,
                "notes": x.resolution or x.description,
                "owner": users[x.owner_id].display_name
                if x.owner_id in users
                else "Unassigned",
                "due": x.due_at.strftime("%d %b %Y")
                if x.due_at
                else "No due date",
            }
            for x in db.scalars(
                select(m.RiskIssue).where(m.RiskIssue.project_id == p.id)
            )
        ]
        self.feedback = [
            {"title": "Sponsor feedback", "notes": x.comments, "score": ""}
            for x in db.scalars(
                select(m.SponsorFeedback).where(
                    m.SponsorFeedback.project_id == p.id
                )
            )
        ]
        self.feedback.extend(
            {
                "title": "Advisor evaluation",
                "notes": x.comments,
                "score": f"{x.score:.2f} / {x.maximum_score:.2f}"
                if x.score is not None
                else "Not scored",
            }
            for x in db.scalars(
                select(m.AdvisorEvaluation).where(
                    m.AdvisorEvaluation.project_id == p.id
                )
            )
        )

    @rx.event
    def request_action(self, action: str, target: str, label: str):
        self.pending_action, self.pending_target, self.pending_label = (
            action,
            target,
            label,
        )
        self._pending_data = {}

    @rx.event
    def cancel_action(self):
        self.pending_action = ""
        self._pending_data = {}

    @rx.event
    def confirm_action(self):
        data = {
            **self._pending_data,
            "action": self.pending_action,
            "target": self.pending_target,
            "confirmed": "yes",
        }
        self.pending_action = ""
        self._pending_data = {}
        return StudioState.save(data)

    @rx.event
    def save(self, data: dict[str, Any]):
        self.error = ""
        action = str(data.get("action", ""))
        if (
            action in ("transition", "publish", "override", "role")
            and data.get("confirmed") != "yes"
        ):
            self.pending_action = action
            self.pending_target = str(data.get("target", ""))
            self.pending_label = (
                "Confirm this change? It will be recorded in the audit history."
            )
            self._pending_data = {str(k): str(v) for k, v in data.items()}
            return
        try:
            with rx.session() as db:
                self._lock(db)
                user, roles = self._actor(db)
                self._mutate(db, user, roles, action, data)
                db.commit()
            self.load()
            return rx.toast.success("Changes saved")
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                str(e)
                if isinstance(e, ValueError)
                else "The change could not be saved. Refresh and try again; another edit may have occurred."
            )

    def _mutate(
        self,
        db: Session,
        user: m.User,
        roles: set[m.Role],
        action: str,
        data: dict[str, Any],
    ):
        admin = bool(
            roles & {m.Role.SYSTEM_ADMINISTRATOR, m.Role.PROGRAM_ADMINISTRATOR}
        )
        target = str(data.get("target", ""))
        if action == "role":
            if m.Role.SYSTEM_ADMINISTRATOR not in roles:
                raise ValueError("Only system administrators can manage roles.")
            uid, role = UUID(str(data["user"])), m.Role(str(data["role"]))
            if not db.get(m.User, uid):
                raise ValueError("User not found.")
            row = db.scalar(
                select(m.UserRole).where(
                    m.UserRole.user_id == uid, m.UserRole.role == role
                )
            )
            if data.get("operation") == "revoke":
                if not row or row.revoked_at:
                    raise ValueError("This role is not active.")
                active = list(
                    db.scalars(
                        select(m.UserRole)
                        .join(m.User, m.User.id == m.UserRole.user_id)
                        .where(
                            m.UserRole.role == m.Role.SYSTEM_ADMINISTRATOR,
                            m.UserRole.revoked_at.is_(None),
                            m.User.is_active.is_(True),
                        )
                    )
                )
                if role == m.Role.SYSTEM_ADMINISTRATOR and len(active) <= 1:
                    raise ValueError(
                        "The last active system administrator cannot be revoked."
                    )
                row.revoked_at = now()
            elif row:
                row.revoked_at = None
                row.granted_by_id = user.id
                row.granted_at = now()
            else:
                db.add(
                    m.UserRole(user_id=uid, role=role, granted_by_id=user.id)
                )
            self._audit(
                db,
                user.id,
                "role.changed",
                reason=f"{data.get('operation', 'grant')} {role.value}",
                entity=uid,
            )
            return
        if action == "profile":
            if m.Role.STUDENT not in roles:
                raise ValueError("Student permission is required.")
            user.display_name = (
                str(data.get("name", "")).strip()[:200] or user.display_name
            )
            user.biography = str(data.get("biography", ""))[:10000]
            self._skills(db, user.id, str(data.get("skills", "")), False)
            hours = Decimal(str(data.get("hours", "10")))
            if not 0 <= hours <= 168:
                raise ValueError("Weekly hours must be between 0 and 168.")
            schedule = db.scalar(
                select(m.SchedulingConstraint).where(
                    m.SchedulingConstraint.user_id == user.id
                )
            )
            if not schedule:
                schedule = m.SchedulingConstraint(user_id=user.id)
                db.add(schedule)
            schedule.timezone, schedule.max_weekly_hours = "UTC", hours
            db.execute(
                delete(m.AvailabilityWindow).where(
                    m.AvailabilityWindow.user_id == user.id
                )
            )
            for line in str(data.get("availability", "")).splitlines():
                if not line.strip():
                    continue
                day, start, end = line.split()
                start_time, end_time = (
                    time.fromisoformat(start),
                    time.fromisoformat(end),
                )
                if not 0 <= int(day) <= 6 or end_time <= start_time:
                    raise ValueError(
                        "Use weekday 0–6 and an end time after start time."
                    )
                db.add(
                    m.AvailabilityWindow(
                        user_id=user.id,
                        weekday=int(day),
                        start_time=start_time,
                        end_time=end_time,
                    )
                )
            self._audit(db, user.id, "profile.updated")
            return
        if action in ("preference", "up", "down", "remove"):
            if m.Role.STUDENT not in roles:
                raise ValueError("Student permission is required.")
            r = self._preference_open(db)
            prefs = list(
                db.scalars(
                    select(m.StudentPreference)
                    .where(
                        m.StudentPreference.round_id == r.id,
                        m.StudentPreference.student_id == user.id,
                    )
                    .order_by(m.StudentPreference.rank)
                )
            )
            if action == "preference":
                p = db.get(m.Project, UUID(target))
                if (
                    not p
                    or p.lifecycle != m.Lifecycle.MATCHING
                    or self._team(db, p.id)
                ):
                    raise ValueError(
                        "This project is not open for preferences."
                    )
                if any(x.project_id == p.id for x in prefs):
                    raise ValueError(
                        "This project is already in your preferences."
                    )
                db.add(
                    m.StudentPreference(
                        round_id=r.id,
                        student_id=user.id,
                        project_id=p.id,
                        rank=len(prefs) + 1,
                        submitted_at=now(),
                    )
                )
            else:
                idx = next(
                    (i for i, x in enumerate(prefs) if str(x.id) == target), -1
                )
                if idx < 0:
                    raise ValueError("Preference not found.")
                if action == "remove":
                    db.delete(prefs.pop(idx))
                else:
                    other = idx - 1 if action == "up" else idx + 1
                    if 0 <= other < len(prefs):
                        prefs[idx], prefs[other] = prefs[other], prefs[idx]
                for i, pref in enumerate(prefs):
                    pref.rank = 10000 + i
                db.flush()
                for i, pref in enumerate(prefs):
                    pref.rank = i + 1
            r.algorithm_version = f"draft-{uuid4()}"
            self._audit(db, user.id, f"preference.{action}")
            return
        if action == "round":
            self._admin(roles)
            if self._round(db, False):
                raise ValueError(
                    "Publish the current round before creating another."
                )
            deadline = self._date(str(data.get("deadline", "")))
            if not deadline or deadline <= now():
                raise ValueError("Choose a future preference deadline.")
            rule = m.AssignmentRuleSet(
                name=str(data.get("name", "Preference round")),
                state=m.RuleState.ACTIVE,
                preference_opens_at=now(),
                preference_closes_at=deadline,
                created_by_id=user.id,
                published_at=now(),
                min_team_size=1,
                max_team_size=100,
            )
            db.add(rule)
            db.flush()
            for i, (kind, key) in enumerate(
                [
                    (m.CriterionKind.STUDENT_PREFERENCE, "preference"),
                    (m.CriterionKind.SKILL_MATCH, "skill"),
                    (m.CriterionKind.AVAILABILITY_OVERLAP, "schedule"),
                    (m.CriterionKind.TEAM_SIZE, "capacity"),
                ]
            ):
                weight = Decimal(str(data.get(key, "1")))
                if not weight.is_finite() or not 0 <= weight <= 1000:
                    raise ValueError("Weights must be between 0 and 1000.")
                db.add(
                    m.AssignmentCriterion(
                        rule_set_id=rule.id,
                        kind=kind,
                        weight=weight,
                        position=i + 1,
                    )
                )
            db.add(
                m.AssignmentRound(
                    name=rule.name,
                    rule_set_id=rule.id,
                    initiated_by_id=user.id,
                    algorithm_version="uniflow-deterministic-v1",
                )
            )
            self._audit(db, user.id, "round.opened")
            return
        if action in ("preview", "publish", "override"):
            self._admin(roles)
            if action == "override":
                self._override(db, user, data)
                return
            r = self._round(db)
            rows, stamp = self._matching(db, r)
            if action == "preview":
                self.preview = rows
                self._preview_stamp = stamp
                return
            if not rows:
                raise ValueError(
                    "No feasible teams. Add preferences or adjust project team sizes."
                )
            if not self._preview_stamp or stamp != self._preview_stamp:
                raise ValueError(
                    "Matching inputs changed. Generate and review a new preview."
                )
            rule = db.get(m.AssignmentRuleSet, r.rule_set_id)
            if rule.preference_closes_at and now() < rule.preference_closes_at:
                raise ValueError(
                    "Wait until preferences close before publishing assignments."
                )
            for pid in sorted({x["project_id"] for x in rows}):
                p = db.get(m.Project, UUID(pid))
                members = [x for x in rows if x["project_id"] == pid]
                team = m.TeamAssignment(
                    project_id=p.id,
                    round_id=r.id,
                    name=p.title,
                    state=m.AssignmentState.CONFIRMED,
                    assigned_by_id=user.id,
                    advisor_id=p.advisor_id,
                    confirmed_at=now(),
                    score=Decimal(str(sum(float(x["score"]) for x in members))),
                )
                db.add(team)
                db.flush()
                for member in members:
                    uid = UUID(member["student_id"])
                    db.add(
                        m.TeamMembership(
                            team_id=team.id,
                            student_id=uid,
                            assigned_by_id=user.id,
                        )
                    )
                    self._notice(
                        db,
                        uid,
                        f"You have been assigned to {p.title}",
                        p.id,
                        f"assignment:{team.id}:{uid}",
                    )
                self._audit(db, user.id, "team.assigned", p.id)
            r.state, r.published_at, r.completed_at = (
                m.AssignmentState.CONFIRMED,
                now(),
                now(),
            )
            self.preview = []
            self._preview_stamp = ""
            return
        if action == "template":
            self._admin(roles)
            title = str(data.get("name", "")).strip()
            lines = [
                x for x in str(data.get("items", "")).splitlines() if x.strip()
            ]
            if not title or not lines:
                raise ValueError(
                    "Provide a template name and at least one milestone."
                )
            t = m.MilestoneTemplate(
                name=title,
                description=str(data.get("description", "")),
                created_by_id=user.id,
            )
            db.add(t)
            db.flush()
            for i, line in enumerate(lines):
                parts = line.split("|")
                if len(parts) < 2 or not parts[0].strip() or int(parts[1]) < 0:
                    raise ValueError(
                        "Each milestone needs Title | days after start | acceptance criteria."
                    )
                db.add(
                    m.MilestoneTemplateItem(
                        template_id=t.id,
                        title=parts[0].strip(),
                        due_offset_days=int(parts[1]),
                        position=i + 1,
                        acceptance_criteria=parts[2].strip()
                        if len(parts) > 2
                        else "",
                    )
                )
            self._audit(db, user.id, "template.created", entity=t.id)
            return
        if action in ("read", "read_all"):
            query = select(m.Notification).where(
                m.Notification.recipient_id == user.id,
                m.Notification.read_state == m.ReadState.UNREAD,
            )
            if action == "read":
                query = query.where(m.Notification.id == UUID(target))
            for n in db.scalars(query):
                n.read_state, n.read_at = m.ReadState.READ, now()
            return
        if action == "proposal":
            if not admin and m.Role.SPONSOR not in roles:
                raise ValueError("Sponsor permission is required.")
            p = (
                db.get(m.Project, UUID(target))
                if target
                else m.Project(sponsor_id=user.id)
            )
            if target:
                self._editable(p, user, admin)
                if str(p.version) != str(data.get("version", "")):
                    raise ValueError(
                        "This proposal changed. Reopen it before saving."
                    )
            title = str(data.get("title", "")).strip()
            minimum, maximum = (
                int(str(data.get("min", "3"))),
                int(str(data.get("max", "5"))),
            )
            if (
                not title
                or not str(data.get("summary", "")).strip()
                or not 1 <= minimum <= maximum <= 100
            ):
                raise ValueError(
                    "Enter a title, summary, and team size between 1 and 100."
                )
            old_deadline = p.proposal_deadline
            deadline = self._date(str(data.get("deadline", "")))
            if target and not admin and deadline != old_deadline:
                raise ValueError(
                    "Only administrators can change an existing deadline."
                )
            p.title, p.summary, p.description = (
                title[:240],
                str(data.get("summary", "")),
                str(data.get("description", "")),
            )
            (
                p.preferred_min_team_size,
                p.preferred_max_team_size,
                p.proposal_deadline,
            ) = minimum, maximum, deadline
            db.add(p)
            db.flush()
            db.execute(
                delete(m.ProjectObjective).where(
                    m.ProjectObjective.project_id == p.id
                )
            )
            for i, objective in enumerate(
                x.strip()
                for x in str(data.get("objectives", "")).splitlines()
                if x.strip()
            ):
                db.add(
                    m.ProjectObjective(
                        project_id=p.id, position=i + 1, description=objective
                    )
                )
            self._skills(db, p.id, str(data.get("skills", "")), True)
            self._audit(db, user.id, "proposal.saved", p.id)
            self.selected = {**self.selected, "id": str(p.id)}
            return
        pid = str(data.get("project", "")) or self.selected["id"]
        if not pid:
            raise ValueError("Open a project first.")
        p = db.get(m.Project, UUID(pid))
        self._access(db, p, user, roles, True)
        if action == "transition":
            transition = str(data.get("state", target))
            destinations = {
                "draft": {"submitted"},
                "changes_requested": {"submitted"},
                "submitted": {"under_review"},
                "under_review": {"approved", "rejected", "changes_requested"},
                "approved": {"matching"},
                "matching": {"active"},
                "active": {"completed"},
                "completed": {"archived"},
                "rejected": {"archived"},
            }
            if transition not in destinations.get(p.lifecycle.value, set()):
                raise ValueError("This lifecycle transition is not allowed.")
            if str(data.get("version", "")) != str(p.version):
                raise ValueError(
                    "The project changed. Reopen it before continuing."
                )
            if transition == "submitted":
                self._editable(p, user, admin)
                if (
                    not p.title
                    or not p.summary
                    or not db.scalar(
                        select(m.ProjectObjective.id).where(
                            m.ProjectObjective.project_id == p.id
                        )
                    )
                ):
                    raise ValueError(
                        "Add a title, summary and at least one objective before submitting."
                    )
                p.submitted_at = now()
            else:
                self._admin(roles)
                if (
                    transition in ("rejected", "changes_requested")
                    and not str(data.get("reason", "")).strip()
                ):
                    raise ValueError("Explain the decision for the sponsor.")
                if transition == "approved":
                    p.approved_at, p.approved_by_id = now(), user.id
                if transition in ("approved", "rejected", "changes_requested"):
                    p.reviewed_at, p.reviewed_by_id, p.review_notes = (
                        now(),
                        user.id,
                        str(data.get("reason", "")),
                    )
                    self._notice(
                        db,
                        p.sponsor_id,
                        f"{p.title}: {transition.replace('_', ' ')}",
                        p.id,
                        f"review:{p.id}:{p.version}:{transition}",
                    )
                if transition == "active":
                    team = self._team(db, p.id)
                    if (
                        not team
                        or not p.advisor_id
                        or len(self._members(db, team))
                        < p.preferred_min_team_size
                    ):
                        raise ValueError(
                            "Assign a valid team and advisor before starting delivery."
                        )
                    p.status, p.health = (
                        m.ProjectStatus.IN_PROGRESS,
                        m.Health.ON_TRACK,
                    )
                if transition == "completed":
                    unfinished = db.scalar(
                        select(m.ProjectMilestone.id).where(
                            m.ProjectMilestone.project_id == p.id,
                            m.ProjectMilestone.state.notin_(
                                [
                                    m.MilestoneState.ACCEPTED,
                                    m.MilestoneState.WAIVED,
                                ]
                            ),
                        )
                    )
                    if unfinished:
                        raise ValueError(
                            "Accept all milestones before completing the project."
                        )
                    p.completed_at, p.status = now(), m.ProjectStatus.COMPLETED
                    team = self._team(db, p.id)
                    if team:
                        for member in db.scalars(
                            select(m.TeamMembership).where(
                                m.TeamMembership.team_id == team.id,
                                m.TeamMembership.left_at.is_(None),
                            )
                        ):
                            member.left_at = now()
                        team.state = m.AssignmentState.SUPERSEDED
                if transition == "archived":
                    p.archived_at = now()
            p.lifecycle = m.Lifecycle(transition)
        elif action == "configure":
            self._admin(roles)
            if str(p.version) != str(data.get("version", "")):
                raise ValueError("Project changed; reopen it first.")
            advisor = UUID(str(data["advisor"]))
            if not db.scalar(
                select(m.UserRole.id).where(
                    m.UserRole.user_id == advisor,
                    m.UserRole.role == m.Role.FACULTY_ADVISOR,
                    m.UserRole.revoked_at.is_(None),
                )
            ):
                raise ValueError("Select an active faculty advisor.")
            if str(data["status"]) not in (
                "not_started",
                "in_progress",
                "on_hold",
            ):
                raise ValueError(
                    "Use lifecycle decisions to complete or cancel a project."
                )
            p.advisor_id, p.health, p.status = (
                advisor,
                m.Health(str(data["health"])),
                m.ProjectStatus(str(data["status"])),
            )
            team = self._team(db, p.id)
            if team:
                team.advisor_id = advisor
        elif action == "instantiate":
            self._admin(roles)
            t = db.get(m.MilestoneTemplate, UUID(str(data["template"])))
            start = self._date(str(data.get("start", "")))
            if not t or not start:
                raise ValueError("Select a template and start date.")
            position = max(
                list(
                    db.scalars(
                        select(m.ProjectMilestone.position).where(
                            m.ProjectMilestone.project_id == p.id
                        )
                    )
                ),
                default=0,
            )
            for i, item in enumerate(
                db.scalars(
                    select(m.MilestoneTemplateItem)
                    .where(m.MilestoneTemplateItem.template_id == t.id)
                    .order_by(m.MilestoneTemplateItem.position)
                )
            ):
                due = start + timedelta(days=item.due_offset_days)
                milestone = m.ProjectMilestone(
                    project_id=p.id,
                    template_item_id=item.id,
                    title=item.title,
                    description=item.description,
                    acceptance_criteria=item.acceptance_criteria,
                    position=position + i + 1,
                    due_at=due,
                    original_due_at=due,
                )
                db.add(milestone)
                db.flush()
                db.add(
                    m.Deliverable(
                        project_id=p.id,
                        milestone_id=milestone.id,
                        title=item.title,
                    )
                )
        elif action == "deadline":
            self._admin(roles)
            milestone = db.get(m.ProjectMilestone, UUID(str(data["milestone"])))
            if (
                not milestone
                or milestone.project_id != p.id
                or str(milestone.version) != str(data.get("version", ""))
            ):
                raise ValueError(
                    "Milestone changed or is unavailable. Refresh first."
                )
            if not str(data.get("reason", "")).strip():
                raise ValueError("A deadline-change reason is required.")
            milestone.due_at = self._date(str(data.get("due", "")))
            if not milestone.due_at:
                raise ValueError("A due date is required.")
        elif action == "submission":
            team = self._team(db, p.id)
            if (
                m.Role.STUDENT not in roles
                or user.id not in self._members(db, team)
                or p.lifecycle != m.Lifecycle.ACTIVE
            ):
                raise ValueError(
                    "Only assigned students can submit for an active project."
                )
            milestone = db.get(m.ProjectMilestone, UUID(str(data["milestone"])))
            if (
                not milestone
                or milestone.project_id != p.id
                or milestone.state
                in (m.MilestoneState.ACCEPTED, m.MilestoneState.WAIVED)
            ):
                raise ValueError("This milestone cannot receive submissions.")
            d = db.scalar(
                select(m.Deliverable).where(
                    m.Deliverable.milestone_id == milestone.id
                )
            )
            files = [
                db.get(m.FileMetadata, UUID(x["id"])) for x in self.staged_files
            ]
            if not files or any(
                not f or f.uploaded_by_id != user.id for f in files
            ):
                raise ValueError("Upload at least one file before submitting.")
            revision = (
                max(
                    list(
                        db.scalars(
                            select(m.DeliverableSubmission.revision).where(
                                m.DeliverableSubmission.deliverable_id == d.id
                            )
                        )
                    ),
                    default=0,
                )
                + 1
            )
            sub = m.DeliverableSubmission(
                project_id=p.id,
                deliverable_id=d.id,
                team_id=team.id,
                revision=revision,
                state=m.SubmissionState.SUBMITTED,
                submitted_by_id=user.id,
                submitted_at=now(),
                content=str(data.get("notes", "")),
            )
            db.add(sub)
            db.flush()
            for f in files:
                db.add(m.SubmissionFile(submission_id=sub.id, file_id=f.id))
            milestone.state = m.MilestoneState.SUBMITTED
            self._notice(
                db,
                p.advisor_id,
                f"New submission: {p.title} / {d.title}",
                p.id,
                f"submission:{sub.id}",
            )
            self.staged_files = []
        elif action == "evaluate":
            if not admin and not (
                m.Role.FACULTY_ADVISOR in roles and p.advisor_id == user.id
            ):
                raise ValueError(
                    "Only the assigned advisor can evaluate this project."
                )
            sub = db.get(m.DeliverableSubmission, UUID(str(data["submission"])))
            if not sub or sub.project_id != p.id:
                raise ValueError("Submission not found.")
            d = db.get(m.Deliverable, sub.deliverable_id)
            latest = max(
                db.scalars(
                    select(m.DeliverableSubmission.revision).where(
                        m.DeliverableSubmission.deliverable_id == d.id
                    )
                )
            )
            if sub.revision != latest:
                raise ValueError("Evaluate the most recent submission version.")
            score = Decimal(str(data.get("score", "0")))
            if not score.is_finite() or not 0 <= score <= 100:
                raise ValueError("Score must be between 0 and 100.")
            result = str(data.get("decision", "changes_requested"))
            if result not in ("accepted", "changes_requested"):
                raise ValueError("Choose accept or request revisions.")
            db.add(
                m.AdvisorEvaluation(
                    project_id=p.id,
                    advisor_id=user.id,
                    submission_id=sub.id,
                    milestone_id=d.milestone_id,
                    score=score,
                    comments=f"{result.replace('_', ' ')}: {data.get('notes', '')}",
                    finalized_at=now(),
                )
            )
            milestone = db.get(m.ProjectMilestone, d.milestone_id)
            milestone.state = m.MilestoneState(result)
            if result == "accepted":
                milestone.accepted_at, milestone.accepted_by_id = now(), user.id
            for uid in self._members(db, self._team(db, p.id)):
                self._notice(
                    db,
                    uid,
                    f"Advisor feedback: {p.title}",
                    p.id,
                    f"evaluation:{uuid4()}:{uid}",
                )
        elif action == "feedback":
            if not admin and not (
                m.Role.SPONSOR in roles and p.sponsor_id == user.id
            ):
                raise ValueError(
                    "Only this project's sponsor can add sponsor feedback."
                )
            notes = str(data.get("notes", "")).strip()
            if not notes:
                raise ValueError("Enter feedback before saving.")
            row = m.SponsorFeedback(
                project_id=p.id,
                sponsor_id=user.id,
                comments=notes,
                submitted_at=now(),
            )
            db.add(row)
            db.flush()
            for uid in self._members(db, self._team(db, p.id)):
                self._notice(
                    db,
                    uid,
                    f"Sponsor feedback: {p.title}",
                    p.id,
                    f"feedback:{row.id}:{uid}",
                )
        elif action == "meeting":
            start, end = (
                self._date(str(data.get("start", ""))),
                self._date(str(data.get("end", ""))),
            )
            if (
                not start
                or not end
                or end <= start
                or not str(data.get("title", "")).strip()
            ):
                raise ValueError(
                    "Provide a title and an end time after the start time."
                )
            meeting = m.Meeting(
                project_id=p.id,
                organizer_id=user.id,
                title=str(data["title"]),
                minutes=str(data.get("notes", "")),
                location=str(data.get("location", "")),
                starts_at=start,
                ends_at=end,
            )
            db.add(meeting)
            db.flush()
            attendees = set(self._members(db, self._team(db, p.id))) | {user.id}
            for uid in attendees:
                db.add(m.MeetingAttendee(meeting_id=meeting.id, user_id=uid))
        elif action == "risk":
            if not str(data.get("title", "")).strip():
                raise ValueError("Enter a risk or issue title.")
            owner_id = UUID(str(data.get("owner", user.id)))
            allowed = set(self._members(db, self._team(db, p.id))) | {
                user.id,
                p.advisor_id,
                p.sponsor_id,
            }
            if owner_id not in allowed:
                raise ValueError("The owner must belong to the project.")
            db.add(
                m.RiskIssue(
                    project_id=p.id,
                    reported_by_id=user.id,
                    owner_id=owner_id,
                    title=str(data["title"]),
                    description=str(data.get("notes", "")),
                    severity=m.Severity(str(data["severity"])),
                    kind=m.IssueKind(str(data["kind"])),
                    due_at=self._date(str(data.get("due", ""))),
                )
            )
        elif action == "resolve":
            risk = db.get(m.RiskIssue, UUID(str(data["risk"])))
            if (
                not risk
                or risk.project_id != p.id
                or (not admin and user.id not in (risk.owner_id, p.advisor_id))
            ):
                raise ValueError(
                    "Only the owner or advisor can resolve this issue."
                )
            if not str(data.get("notes", "")).strip():
                raise ValueError("Provide a resolution note.")
            (
                risk.resolution,
                risk.state,
                risk.resolved_at,
                risk.resolved_by_id,
            ) = str(data["notes"]), m.IssueState.RESOLVED, now(), user.id
        else:
            raise ValueError("Unknown action.")
        self._audit(
            db,
            user.id,
            f"project.{action}",
            p.id,
            str(data.get("reason", data.get("notes", "")))[:2000],
        )

    def _editable(self, p: m.Project, user: m.User, admin: bool):
        if not p:
            raise ValueError("Proposal not found.")
        if admin:
            return
        if (
            p.sponsor_id != user.id
            or p.lifecycle
            not in (m.Lifecycle.DRAFT, m.Lifecycle.CHANGES_REQUESTED)
            or (p.proposal_deadline and now() >= p.proposal_deadline)
        ):
            raise ValueError(
                "This proposal is no longer editable by its sponsor."
            )

    def _skills(self, db: Session, identity: UUID, raw: str, project: bool):
        if project:
            db.execute(
                delete(m.ProjectSkill).where(
                    m.ProjectSkill.project_id == identity
                )
            )
        else:
            db.execute(
                delete(m.UserSkill).where(m.UserSkill.user_id == identity)
            )
        for name in sorted(
            {x.strip().lower() for x in raw.split(",") if x.strip()}
        ):
            skill = db.scalar(select(m.Skill).where(m.Skill.name == name))
            if not skill:
                skill = m.Skill(name=name)
                db.add(skill)
                db.flush()
            db.add(
                m.ProjectSkill(project_id=identity, skill_id=skill.id)
                if project
                else m.UserSkill(user_id=identity, skill_id=skill.id)
            )

    def _matching(
        self, db: Session, r: m.AssignmentRound
    ) -> tuple[list[dict[str, str]], str]:
        projects = list(
            db.scalars(
                select(m.Project)
                .where(m.Project.lifecycle == m.Lifecycle.MATCHING)
                .order_by(m.Project.id)
            )
        )
        projects = [p for p in projects if not self._team(db, p.id)]
        students = list(
            db.scalars(
                select(m.User)
                .join(m.UserRole, m.UserRole.user_id == m.User.id)
                .where(
                    m.UserRole.role == m.Role.STUDENT,
                    m.UserRole.revoked_at.is_(None),
                    m.User.is_active.is_(True),
                )
                .order_by(m.User.id)
            )
        )
        occupied = set(
            db.scalars(
                select(m.TeamMembership.student_id)
                .join(
                    m.TeamAssignment,
                    m.TeamAssignment.id == m.TeamMembership.team_id,
                )
                .where(
                    m.TeamAssignment.state == m.AssignmentState.CONFIRMED,
                    m.TeamMembership.left_at.is_(None),
                )
            )
        )
        students = [s for s in students if s.id not in occupied]
        prefs = list(
            db.scalars(
                select(m.StudentPreference).where(
                    m.StudentPreference.round_id == r.id
                )
            )
        )
        ranks = {(x.student_id, x.project_id): x.rank for x in prefs}
        weights = {
            x.kind: float(x.weight)
            for x in db.scalars(
                select(m.AssignmentCriterion).where(
                    m.AssignmentCriterion.rule_set_id == r.rule_set_id
                )
            )
        }
        skills = list(db.scalars(select(m.UserSkill)))
        requirements = list(db.scalars(select(m.ProjectSkill)))
        windows = list(db.scalars(select(m.AvailabilityWindow)))
        inputs = [
            f"{type(x).__name__}:{x.id}:{x.version}"
            for x in [
                r,
                *projects,
                *students,
                *prefs,
                *skills,
                *requirements,
                *windows,
            ]
        ]
        inputs.extend(str(x) for x in sorted(occupied))
        stamp = hashlib.sha256("|".join(sorted(inputs)).encode()).hexdigest()
        edges = []
        for p in projects:
            candidates = []
            needed = {x.skill_id for x in requirements if x.project_id == p.id}
            for student in students:
                rank = ranks.get((student.id, p.id))
                if not rank:
                    continue
                owned = {x.skill_id for x in skills if x.user_id == student.id}
                skill = len(needed & owned) / len(needed) if needed else 1.0
                student_windows = [
                    w for w in windows if w.user_id == student.id
                ]
                sponsor_windows = [
                    w for w in windows if w.user_id == p.sponsor_id
                ]
                overlap = any(
                    a.weekday == b.weekday
                    and a.start_time
                    and b.start_time
                    and max(a.start_time, b.start_time)
                    < min(a.end_time, b.end_time)
                    for a in student_windows
                    for b in sponsor_windows
                )
                schedule = 1.0 if overlap else 0.0
                capacity = 1.0 / p.preferred_max_team_size
                score = (
                    weights.get(m.CriterionKind.STUDENT_PREFERENCE, 1) / rank
                    + weights.get(m.CriterionKind.SKILL_MATCH, 1) * skill
                    + weights.get(m.CriterionKind.AVAILABILITY_OVERLAP, 1)
                    * schedule
                    + weights.get(m.CriterionKind.TEAM_SIZE, 1) * capacity
                )
                candidates.append(
                    {
                        "student_id": str(student.id),
                        "student": student.display_name,
                        "project_id": str(p.id),
                        "project": p.title,
                        "score": f"{score:.4f}",
                        "explanation": f"Choice #{rank} · skills {skill:.0%} · schedule {'overlap' if overlap else 'unknown / no overlap'} · capacity {p.preferred_min_team_size}–{p.preferred_max_team_size}",
                    }
                )
            edges.extend(candidates)
        edges.sort(
            key=lambda x: (-float(x["score"]), x["student_id"], x["project_id"])
        )
        by_project = {str(p.id): p for p in projects}
        banned: set[str] = set()
        rows: list[dict[str, str]] = []
        while True:
            rows = []
            assigned: set[str] = set()
            counts: dict[str, int] = {}
            for edge in edges:
                pid = edge["project_id"]
                if (
                    pid in banned
                    or edge["student_id"] in assigned
                    or counts.get(pid, 0)
                    >= by_project[pid].preferred_max_team_size
                ):
                    continue
                rows.append(edge)
                assigned.add(edge["student_id"])
                counts[pid] = counts.get(pid, 0) + 1
            undersized = [
                pid
                for pid, count in counts.items()
                if count < by_project[pid].preferred_min_team_size
            ]
            if not undersized:
                break
            banned.add(
                sorted(
                    undersized,
                    key=lambda pid: (
                        counts[pid] / by_project[pid].preferred_min_team_size,
                        pid,
                    ),
                )[0]
            )
        return rows, stamp

    def _override(self, db: Session, user: m.User, data: dict[str, Any]):
        uid, pid = UUID(str(data["student"])), UUID(str(data["project"]))
        reason = str(data.get("reason", "")).strip()
        if not reason:
            raise ValueError("An override reason is required.")
        if not db.scalar(
            select(m.UserRole.id).where(
                m.UserRole.user_id == uid,
                m.UserRole.role == m.Role.STUDENT,
                m.UserRole.revoked_at.is_(None),
            )
        ):
            raise ValueError("Select an active student.")
        p = db.get(m.Project, pid)
        if not p or p.lifecycle not in (
            m.Lifecycle.MATCHING,
            m.Lifecycle.ACTIVE,
        ):
            raise ValueError("Select a project in matching or delivery.")
        teams = list(
            db.scalars(
                select(m.TeamAssignment).where(
                    m.TeamAssignment.state == m.AssignmentState.CONFIRMED
                )
            )
        )
        old = next((t for t in teams if uid in self._members(db, t)), None)
        dest = self._team(db, pid)
        if old and dest and old.id == dest.id:
            raise ValueError("The student already belongs to this project.")
        destination = self._members(db, dest)
        destination.append(uid)
        if (
            not p.preferred_min_team_size
            <= len(destination)
            <= p.preferred_max_team_size
        ):
            raise ValueError(
                "This move would violate the destination team size."
            )
        affected = [(dest, p, destination)]
        if old:
            origin = db.get(m.Project, old.project_id)
            remaining = [x for x in self._members(db, old) if x != uid]
            if len(remaining) < origin.preferred_min_team_size:
                raise ValueError(
                    "This move would leave the original team below its minimum size."
                )
            affected.append((old, origin, remaining))
        r = m.AssignmentRound(
            name="Manual override",
            state=m.AssignmentState.CONFIRMED,
            initiated_by_id=user.id,
            published_at=now(),
            algorithm_version="manual-v1",
        )
        db.add(r)
        db.flush()
        for previous, project, members in affected:
            if previous:
                previous.state = m.AssignmentState.SUPERSEDED
                for membership in db.scalars(
                    select(m.TeamMembership).where(
                        m.TeamMembership.team_id == previous.id,
                        m.TeamMembership.left_at.is_(None),
                    )
                ):
                    membership.left_at = now()
            replacement = m.TeamAssignment(
                project_id=project.id,
                round_id=r.id,
                name=project.title,
                advisor_id=project.advisor_id,
                state=m.AssignmentState.CONFIRMED,
                confirmed_at=now(),
                assigned_by_id=user.id,
                supersedes_id=previous.id if previous else None,
                is_manual_override=True,
                overridden_by_id=user.id,
                overridden_at=now(),
                override_reason=reason,
            )
            db.add(replacement)
            db.flush()
            for member in members:
                db.add(
                    m.TeamMembership(
                        team_id=replacement.id,
                        student_id=member,
                        assigned_by_id=user.id,
                        is_manual_override=True,
                        overridden_by_id=user.id,
                        overridden_at=now(),
                        override_reason=reason,
                    )
                )
                self._notice(
                    db,
                    member,
                    f"Team assignment updated: {project.title}",
                    project.id,
                    f"override:{replacement.id}:{member}",
                )
            self._audit(
                db, user.id, "assignment.overridden", project.id, reason
            )

    @rx.event
    async def upload(self, files: list[rx.UploadFile]):
        try:
            if not 1 <= len(files) <= 5:
                raise ValueError("Select between one and five documents.")
            async with rx.asession() as db:
                self._lock(db)
                user, roles = self._actor(db)
                p = db.get(m.Project, UUID(self.selected["id"]))
                self._access(db, p, user, roles, True)
                admin = bool(
                    roles
                    & {
                        m.Role.SYSTEM_ADMINISTRATOR,
                        m.Role.PROGRAM_ADMINISTRATOR,
                    }
                )
                proposal = admin or (
                    m.Role.SPONSOR in roles and p.sponsor_id == user.id
                )
                if proposal:
                    self._editable(p, user, admin)
                elif (
                    m.Role.STUDENT not in roles
                    or user.id not in self._members(db, self._team(db, p.id))
                    or p.lifecycle != m.Lifecycle.ACTIVE
                ):
                    raise ValueError("You cannot upload to this project.")
                for file in files:
                    filename = Path(file.name or "document").name[:255]
                    suffix = Path(filename).suffix.lower()
                    if suffix not in (".pdf", ".docx", ".txt", ".csv"):
                        raise ValueError("Use PDF, DOCX, TXT or CSV documents.")
                    content = await file.read(10 * 1024 * 1024 + 1)
                    if not content or len(content) > 10 * 1024 * 1024:
                        raise ValueError(
                            "Each document must be nonempty and at most 10 MB."
                        )
                    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
                        raise ValueError(
                            "This file is not a valid PDF document."
                        )
                    if suffix == ".docx" and not content.startswith(b"PK"):
                        raise ValueError(
                            "This file is not a valid DOCX document."
                        )
                    key = f"{uuid4().hex}{suffix}"
                    directory = rx.get_upload_dir()
                    directory.mkdir(parents=True, exist_ok=True)
                    (directory / key).write_bytes(content)
                    f = m.FileMetadata(
                        storage_key=key,
                        original_filename=filename,
                        content_type=file.content_type
                        or "application/octet-stream",
                        size_bytes=len(content),
                        sha256=hashlib.sha256(content).hexdigest(),
                        uploaded_by_id=user.id,
                        state=m.FileState.AVAILABLE,
                        verified_at=now(),
                    )
                    db.add(f)
                    db.flush()
                    if proposal:
                        db.add(
                            m.ProjectDocument(
                                project_id=p.id, file_id=f.id, title=filename
                            )
                        )
                    else:
                        self.staged_files.append(
                            {"id": str(f.id), "name": filename}
                        )
                self._audit(db, user.id, "documents.uploaded", p.id)
                db.commit()
            self.load()
            return rx.clear_selected_files("documents")
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.staged_files = []
            self.error = (
                str(e)
                if isinstance(e, ValueError)
                else "Upload failed. Please try again."
            )

    @rx.event
    def download_submission(self, submission_id: str):
        try:
            import zipfile

            with rx.session() as db:
                user, roles = self._actor(db)
                sub = db.get(m.DeliverableSubmission, UUID(submission_id))
                if not sub:
                    raise ValueError("Submission not found.")
                self._access(
                    db, db.get(m.Project, sub.project_id), user, roles, True
                )
                files = list(
                    db.scalars(
                        select(m.FileMetadata)
                        .join(
                            m.SubmissionFile,
                            m.SubmissionFile.file_id == m.FileMetadata.id,
                        )
                        .where(m.SubmissionFile.submission_id == sub.id)
                    )
                )
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w") as archive:
                    for i, file in enumerate(files):
                        archive.writestr(
                            f"{i + 1}_{Path(file.original_filename).name}",
                            (
                                rx.get_upload_dir() / file.storage_key
                            ).read_bytes(),
                        )
                return rx.download(
                    data=buffer.getvalue(),
                    filename=f"submission_{uuid4().hex}.zip",
                )
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = (
                "Could not download this submission. It may be unavailable."
            )

    @rx.event
    def export(self):
        try:
            with rx.session() as db:
                user, roles = self._actor(db)
                self._admin(roles)
                self._load_data(db, user, roles)
                output = io.StringIO()
                fields = [
                    "project",
                    "lifecycle",
                    "schedule",
                    "missing",
                    "advisor",
                    "members",
                    "staffing",
                ]
                writer = csv.DictWriter(output, fieldnames=fields)
                writer.writeheader()
                for row in self.filtered_reports:
                    writer.writerow(
                        {
                            k: f"'{v}"
                            if v.startswith(("=", "+", "-", "@", "\t", "\r"))
                            else v
                            for k, v in row.items()
                        }
                    )
                self._audit(
                    db,
                    user.id,
                    "report.exported",
                    reason=f"Projects report; {len(self.filtered_reports)} rows",
                )
                db.commit()
                return rx.download(
                    data=output.getvalue(),
                    filename=f"uniflow_report_{uuid4().hex}.csv",
                )
        except Exception as e:
            logging.exception(f"Error: {e}")
            self.error = "The report could not be exported."

    @rx.event
    def start_scan(self):
        if not self.scanning:
            return StudioState.scan

    def _scan_database(self, uid: str) -> str:
        with rx.session() as db:
            self._lock(db)
            actor, roles = self._actor(db, uid)
            self._admin(roles)
            due = list(
                db.scalars(
                    select(m.ProjectMilestone)
                    .join(
                        m.Project, m.Project.id == m.ProjectMilestone.project_id
                    )
                    .where(
                        m.Project.lifecycle == m.Lifecycle.ACTIVE,
                        m.ProjectMilestone.due_at <= now() + timedelta(days=3),
                        m.ProjectMilestone.state.notin_(
                            [m.MilestoneState.ACCEPTED, m.MilestoneState.WAIVED]
                        ),
                    )
                )
            )
            for milestone in due:
                p = db.get(m.Project, milestone.project_id)
                recipients = set(self._members(db, self._team(db, p.id))) | {
                    p.advisor_id,
                    p.sponsor_id,
                }
                status = "overdue" if milestone.due_at < now() else "due soon"
                for uid in recipients:
                    self._notice(
                        db,
                        uid,
                        f"{milestone.title} is {status} · {p.title}",
                        p.id,
                        f"deadline:{milestone.id}:{milestone.due_at.isoformat()}:{status}",
                        True,
                    )
            actor_id = str(actor.id)
            db.commit()
        with rx.session() as db:
            _, roles = self._actor(db, actor_id)
            self._admin(roles)
            queued = list(
                db.scalars(
                    select(m.Notification)
                    .where(
                        m.Notification.processing_state
                        == m.ProcessingState.PENDING,
                        m.Notification.scheduled_at <= now(),
                    )
                    .with_for_update(skip_locked=True)
                )
            )
            for notice in queued:
                notice.processing_state = m.ProcessingState.DELIVERED
                notice.attempts += 1
                notice.processed_at, notice.delivered_at = now(), now()
            db.commit()
            return f"Scan complete · {len(due)} due milestones checked · {len(queued)} notices delivered"

    @rx.event(background=True)
    async def scan(self):
        async with self:
            if self.scanning or not self._uid or self._expires < clock.time():
                return
            self.scanning = True
            uid = self._uid
        try:
            result = await asyncio.to_thread(self._scan_database, uid)
            async with self:
                self.queue_status = result
        except Exception as e:
            logging.exception(f"Error: {e}")
            async with self:
                self.queue_status = (
                    "Scan failed. An administrator can safely retry."
                )
        finally:
            async with self:
                self.scanning = False
        yield StudioState.load
