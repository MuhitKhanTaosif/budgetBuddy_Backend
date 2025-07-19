from typing import List, Optional
from datetime import datetime
import enum

from sqlmodel import Field, SQLModel, Relationship, Column, Enum

# --- Enums ---
# Using standard Python enums for controlled vocabulary in specific fields.

class UserRole(enum.Enum):
    """Defines the roles a user can have within the context of a trip."""
    MODERATOR = "moderator"
    PARTICIPANT = "participant"

class TripStatus(enum.Enum):
    """Defines the possible lifecycle states of a trip."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# --- Link Model for Many-to-Many Relationship ---

class TripParticipantLink(SQLModel, table=True):
    """
    Association table to create the many-to-many relationship between Users and Trips.
    This model tracks which users are part of which trips.
    """
    trip_id: int = Field(foreign_key="trip.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    is_active: bool = Field(default=True)

# --- Core Models ---

class User(SQLModel, table=True):
    """Represents a user account in the application."""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    phone: Optional[str] = None
    hashed_password: str = Field()
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow}, nullable=False)

    # --- Relationships ---
    # Trips where this user is the moderator (one-to-many)
    moderated_trips: List["Trip"] = Relationship(back_populates="moderator")
    
    # Association object for the trips this user is participating in
    trip_links: List[TripParticipantLink] = Relationship(back_populates="user")
    
    # Expenses within a trip that were paid by this user (one-to-many)
    paid_expenses: List["Expense"] = Relationship(back_populates="payer")
    
    # Personal expenses for this user, not related to a trip (one-to-many)
    personal_expenses: List["PersonalExpense"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class Trip(SQLModel, table=True):
    """Represents a single trip or tour."""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str = Field()
    description: Optional[str] = None
    destination: str = Field()
    start_date: datetime = Field()
    end_date: datetime = Field()
    estimated_budget: Optional[float] = None
    actual_budget: float = Field(default=0.0) # To be updated via API logic
    invitation_code: str = Field(unique=True)
    status: TripStatus = Field(sa_column=Column(Enum(TripStatus)), default=TripStatus.PLANNING)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow}, nullable=False)
    
    # Foreign Keys
    moderator_id: int = Field(foreign_key="user.id")
    
    # --- Relationships ---
    moderator: User = Relationship(back_populates="moderated_trips")
    participant_links: List[TripParticipantLink] = Relationship(back_populates="trip")
    days: List["TripDay"] = Relationship(back_populates="trip", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    expenses: List["Expense"] = Relationship(back_populates="trip", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class TripDay(SQLModel, table=True):
    """Represents a single day within a trip's itinerary."""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    day_number: int = Field()
    date: datetime = Field()
    title: Optional[str] = Field(default=None, description="e.g., Arrival at the destination")
    description: Optional[str] = None
    
    # Foreign Keys
    trip_id: int = Field(foreign_key="trip.id")
    
    # --- Relationships ---
    trip: Trip = Relationship(back_populates="days")
    activities: List["Activity"] = Relationship(back_populates="day", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class Activity(SQLModel, table=True):
    """Represents a specific activity planned for a TripDay."""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    name: str = Field()
    description: Optional[str] = None
    start_time: datetime = Field()
    end_time: Optional[datetime] = None
    tag: str = Field(description="e.g., 'food', 'travel', 'lodging'")
    location: Optional[str] = None
    notes: Optional[str] = None
    
    # Foreign Keys
    day_id: int = Field(foreign_key="tripday.id")
    
    # --- Relationships ---
    day: TripDay = Relationship(back_populates="activities")
    expenses: List["Expense"] = Relationship(back_populates="activity")


# --- Expense-Related Models ---

class Expense(SQLModel, table=True):
    """An expense paid by one user, associated with a trip and optionally an activity."""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    description: str = Field()
    amount: float = Field()
    receipt_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Foreign Keys
    trip_id: int = Field(foreign_key="trip.id")
    payer_id: int = Field(foreign_key="user.id", description="The user who paid for this expense")
    activity_id: Optional[int] = Field(default=None, foreign_key="activity.id")
    
    # --- Relationships ---
    trip: Trip = Relationship(back_populates="expenses")
    payer: User = Relationship(back_populates="paid_expenses")
    activity: Optional[Activity] = Relationship(back_populates="expenses")


class PersonalExpense(SQLModel, table=True):
    """An expense for a single user, not shared with or related to a trip."""
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str = Field()
    description: Optional[str] = None
    amount: float = Field()
    date: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    # Foreign Keys
    user_id: int = Field(foreign_key="user.id")
    
    # --- Relationships ---
    user: User = Relationship(back_populates="personal_expenses")
