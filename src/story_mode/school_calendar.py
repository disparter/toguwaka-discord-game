from typing import Dict, List, Any, Optional, Union
import json
import logging
import os
from datetime import datetime, timedelta
from .interfaces import Event

logger = logging.getLogger('tokugawa_bot')

class SchoolCalendar:
    """
    Manages the academic calendar for the Academia Tokugawa.
    This class is responsible for tracking dates, scheduling events,
    and managing the academic cycle (classes, terms, semesters, holidays).

    Following the Single Responsibility Principle, this class only handles
    time-related aspects of the story mode.
    """
    def __init__(self, current_date: Optional[datetime] = None):
        """
        Initialize the school calendar.

        Args:
            current_date: The current date in the game world. If None, uses the current real-world date.
        """
        self.current_date = current_date or datetime.now()
        self.events = []  # List of scheduled events
        self.class_schedule = {}  # Weekly class schedule
        self.holidays = []  # List of holidays
        self.semester_start = None  # Start date of the current semester
        self.semester_end = None  # End date of the current semester
        self.term_start = None  # Start date of the current term
        self.term_end = None  # End date of the current term

        # Initialize the academic calendar
        self._initialize_calendar()

        logger.info("SchoolCalendar initialized")

    def _initialize_calendar(self):
        """
        Sets up the initial academic calendar based on the current date.
        Determines the current semester, term, and schedules regular classes.
        """
        # Determine current semester (assuming two semesters per year)
        current_year = self.current_date.year
        if self.current_date.month < 7:
            # First semester (January to June)
            self.semester_start = datetime(current_year, 2, 1)  # February 1st
            self.semester_end = datetime(current_year, 6, 30)   # June 30th

            # First term (February to April)
            self.term_start = datetime(current_year, 2, 1)      # February 1st
            self.term_end = datetime(current_year, 4, 15)       # April 15th
        else:
            # Second semester (July to December)
            self.semester_start = datetime(current_year, 8, 1)  # August 1st
            self.semester_end = datetime(current_year, 12, 15)  # December 15th

            # Third term (August to October)
            self.term_start = datetime(current_year, 8, 1)      # August 1st
            self.term_end = datetime(current_year, 10, 15)      # October 15th

        # Set up regular class schedule (Monday to Friday)
        self._setup_class_schedule()

        # Set up holidays
        self._setup_holidays(current_year)

        logger.info(f"Academic calendar initialized: Semester {self.get_current_semester()}, Term {self.get_current_term()}")

    def _setup_class_schedule(self):
        """
        Sets up the weekly class schedule.
        """
        # Load class schedule from JSON file
        try:
            schedule_path = "data/story_mode/class_schedule.json"
            with open(schedule_path, 'r') as f:
                self.class_schedule = json.load(f)
            logger.info("Loaded class schedule from JSON file")
        except Exception as e:
            logger.error(f"Error loading class schedule from JSON file: {e}")
            # Fallback to default schedule
            self.class_schedule = {
                0: [],  # Sunday - No classes
                1: ["Power Control", "History of Powers", "Combat Training"],  # Monday
                2: ["Ethics", "Science", "Club Activities"],  # Tuesday
                3: ["Power Theory", "Mathematics", "Physical Education"],  # Wednesday
                4: ["Literature", "Power Applications", "Club Activities"],  # Thursday
                5: ["Social Studies", "Elective", "Free Study"],  # Friday
                6: []  # Saturday - No classes
            }
            logger.warning("Using default class schedule")

        logger.info("Class schedule set up")

    def _setup_holidays(self, year: int):
        """
        Sets up holidays for the academic year.

        Args:
            year: The current year
        """
        # Load holidays from JSON file
        try:
            holidays_path = "data/story_mode/holidays.json"
            with open(holidays_path, 'r') as f:
                holidays_data = json.load(f)

            # Convert dates to datetime objects and update the year
            self.holidays = []
            for holiday in holidays_data:
                # Parse the date and update the year
                date_parts = holiday["date"].split("-")
                holiday_date = datetime(year, int(date_parts[1]), int(date_parts[2]))

                # Create the holiday entry
                self.holidays.append({
                    "date": holiday_date,
                    "name": holiday["name"],
                    "description": holiday["description"],
                    "is_school_holiday": holiday.get("is_school_holiday", True),
                    "event_id": holiday.get("event_id", None)
                })

            logger.info(f"Loaded {len(self.holidays)} holidays from JSON file")
        except Exception as e:
            logger.error(f"Error loading holidays from JSON file: {e}")
            # Fallback to default holidays
            self.holidays = [
                {"date": datetime(year, 1, 1), "name": "New Year's Day", "description": "Celebration of the new year."},
                {"date": datetime(year, 5, 1), "name": "Founders Day", "description": "Anniversary of the founding of Academia Tokugawa."},
                {"date": datetime(year, 7, 15), "name": "Power Manifestation Day", "description": "Celebration of the first documented power manifestation."},
                {"date": datetime(year, 12, 25), "name": "Winter Holiday", "description": "End of year celebrations."}
            ]
            logger.warning("Using default holidays")

        logger.info(f"Set up {len(self.holidays)} holidays for year {year}")

    def advance_day(self) -> Dict[str, Any]:
        """
        Advances the calendar by one day and returns events for the new day.

        Returns:
            Dict containing information about the new day, including any scheduled events,
            classes, or holidays.
        """
        # Advance to the next day
        self.current_date += timedelta(days=1)

        # Check if we need to update semester/term
        self._check_academic_period_change()

        # Get day information
        return self.get_day_info()

    def _check_academic_period_change(self):
        """
        Checks if the semester or term has changed and updates accordingly.
        """
        # Check if semester ended
        if self.current_date > self.semester_end:
            # Start new semester
            if self.semester_end.month < 7:
                # Start second semester
                self.semester_start = datetime(self.current_date.year, 8, 1)
                self.semester_end = datetime(self.current_date.year, 12, 15)
                self.term_start = datetime(self.current_date.year, 8, 1)
                self.term_end = datetime(self.current_date.year, 10, 15)
            else:
                # Start first semester of next year
                next_year = self.current_date.year + 1
                self.semester_start = datetime(next_year, 2, 1)
                self.semester_end = datetime(next_year, 6, 30)
                self.term_start = datetime(next_year, 2, 1)
                self.term_end = datetime(next_year, 4, 15)

            logger.info(f"New semester started: {self.get_current_semester()}")

        # Check if term ended but semester continues
        elif self.current_date > self.term_end and self.current_date <= self.semester_end:
            # Start new term within same semester
            if self.term_end.month < 5:
                # Start second term of first semester
                self.term_start = datetime(self.current_date.year, 4, 16)
                self.term_end = datetime(self.current_date.year, 6, 30)
            else:
                # Start fourth term of second semester
                self.term_start = datetime(self.current_date.year, 10, 16)
                self.term_end = datetime(self.current_date.year, 12, 15)

            logger.info(f"New term started: {self.get_current_term()}")

    def get_day_info(self) -> Dict[str, Any]:
        """
        Gets information about the current day.

        Returns:
            Dict containing information about the current day, including any scheduled events,
            classes, or holidays.
        """
        weekday = self.current_date.weekday()

        # Check if today is a holiday
        holiday = next((h for h in self.holidays if h["date"].date() == self.current_date.date()), None)

        # Get scheduled events for today
        todays_events = [event for event in self.events if event["date"].date() == self.current_date.date()]

        # Get classes for today (if not a holiday)
        todays_classes = [] if holiday else self.class_schedule.get(weekday, [])

        return {
            "date": self.current_date,
            "weekday": weekday,
            "is_holiday": holiday is not None,
            "holiday": holiday,
            "events": todays_events,
            "classes": todays_classes,
            "semester": self.get_current_semester(),
            "term": self.get_current_term(),
            "is_school_day": weekday < 5 and not holiday  # Monday-Friday and not a holiday
        }

    def add_event(self, event_date: datetime, event_name: str, event_type: str, event_description: str = "", event_data: Dict[str, Any] = None) -> None:
        """
        Adds a new event to the calendar.

        Args:
            event_date: Date of the event
            event_name: Name of the event
            event_type: Type of event (e.g., "club", "tournament", "special")
            event_description: Description of the event
            event_data: Additional data for the event
        """
        self.events.append({
            "date": event_date,
            "name": event_name,
            "type": event_type,
            "description": event_description,
            "data": event_data or {}
        })

        logger.info(f"Added event: {event_name} on {event_date.strftime('%Y-%m-%d')}")

    def get_current_semester(self) -> str:
        """
        Gets the name of the current semester.

        Returns:
            String representing the current semester (e.g., "Spring 2023")
        """
        year = self.semester_start.year
        if self.semester_start.month < 7:
            return f"Spring {year}"
        else:
            return f"Fall {year}"

    def get_current_term(self) -> str:
        """
        Gets the name of the current term.

        Returns:
            String representing the current term (e.g., "First Term")
        """
        if self.term_start.month < 5:
            return "First Term"
        elif self.term_start.month < 7:
            return "Second Term"
        elif self.term_start.month < 11:
            return "Third Term"
        else:
            return "Fourth Term"

    def is_exam_period(self) -> bool:
        """
        Checks if the current date is during an exam period.

        Returns:
            True if current date is during an exam period, False otherwise
        """
        # Exam periods are typically the last two weeks of each term
        exam_start = self.term_end - timedelta(days=14)
        return exam_start <= self.current_date <= self.term_end

    def is_vacation(self) -> bool:
        """
        Checks if the current date is during a vacation period.

        Returns:
            True if current date is during a vacation period, False otherwise
        """
        # Vacation periods are between semesters
        winter_vacation_start = datetime(self.current_date.year, 12, 16)
        winter_vacation_end = datetime(self.current_date.year + 1, 1, 31)

        summer_vacation_start = datetime(self.current_date.year, 7, 1)
        summer_vacation_end = datetime(self.current_date.year, 7, 31)

        return (winter_vacation_start <= self.current_date or self.current_date <= winter_vacation_end) or \
               (summer_vacation_start <= self.current_date <= summer_vacation_end)

    def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Gets upcoming events within the specified number of days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of upcoming events
        """
        end_date = self.current_date + timedelta(days=days)
        return [
            event for event in self.events 
            if self.current_date <= event["date"] <= end_date
        ]

    def get_class_attribute_bonus(self, class_name: str) -> Dict[str, int]:
        """
        Gets the attribute bonuses for attending a specific class.

        Args:
            class_name: Name of the class

        Returns:
            Dict of attribute bonuses (e.g., {"intellect": 1, "power_stat": 2})
        """
        # Load class attribute bonuses from JSON file
        try:
            bonuses_path = "data/story_mode/class_attribute_bonuses.json"
            with open(bonuses_path, 'r') as f:
                class_bonuses = json.load(f)
            logger.debug(f"Loaded class attribute bonuses from JSON file")
        except Exception as e:
            logger.error(f"Error loading class attribute bonuses from JSON file: {e}")
            # Fallback to default bonuses
            class_bonuses = {
                "Power Control": {"power_stat": 2},
                "History of Powers": {"intellect": 1, "charisma": 1},
                "Combat Training": {"power_stat": 1, "dexterity": 1},
                "Ethics": {"charisma": 2},
                "Science": {"intellect": 2},
                "Club Activities": {"power_stat": 1, "charisma": 1},
                "Power Theory": {"intellect": 2},
                "Mathematics": {"intellect": 2},
                "Physical Education": {"dexterity": 2},
                "Literature": {"intellect": 1, "charisma": 1},
                "Power Applications": {"power_stat": 1, "intellect": 1},
                "Social Studies": {"charisma": 2},
                "Elective": {"intellect": 1, "charisma": 1},
                "Free Study": {"intellect": 1}
            }
            logger.warning("Using default class attribute bonuses")

        return class_bonuses.get(class_name, {})

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the calendar to a dictionary for serialization.

        Returns:
            Dict representation of the calendar
        """
        return {
            "current_date": self.current_date.isoformat(),
            "semester_start": self.semester_start.isoformat(),
            "semester_end": self.semester_end.isoformat(),
            "term_start": self.term_start.isoformat(),
            "term_end": self.term_end.isoformat(),
            "events": [
                {
                    "date": event["date"].isoformat(),
                    "name": event["name"],
                    "type": event["type"],
                    "description": event["description"],
                    "data": event["data"]
                }
                for event in self.events
            ],
            "holidays": [
                {
                    "date": holiday["date"].isoformat(),
                    "name": holiday["name"],
                    "description": holiday["description"]
                }
                for holiday in self.holidays
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchoolCalendar':
        """
        Creates a calendar from a dictionary.

        Args:
            data: Dict representation of the calendar

        Returns:
            SchoolCalendar instance
        """
        calendar = cls(datetime.fromisoformat(data["current_date"]))

        calendar.semester_start = datetime.fromisoformat(data["semester_start"])
        calendar.semester_end = datetime.fromisoformat(data["semester_end"])
        calendar.term_start = datetime.fromisoformat(data["term_start"])
        calendar.term_end = datetime.fromisoformat(data["term_end"])

        calendar.events = [
            {
                "date": datetime.fromisoformat(event["date"]),
                "name": event["name"],
                "type": event["type"],
                "description": event["description"],
                "data": event["data"]
            }
            for event in data["events"]
        ]

        calendar.holidays = [
            {
                "date": datetime.fromisoformat(holiday["date"]),
                "name": holiday["name"],
                "description": holiday["description"]
            }
            for holiday in data["holidays"]
        ]

        return calendar
