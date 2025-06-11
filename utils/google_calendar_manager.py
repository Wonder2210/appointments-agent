from datetime import datetime, timedelta, timezone
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import dotenv
dotenv.load_dotenv()

class GoogleCalendarManager:
    def __init__(self, service_account_file, calendar_id=None):
        """
        Initialize Google Calendar API client with service account
        
        Args:
            service_account_file (str): Path to service account JSON file
            calendar_id (str): Calendar ID to work with (defaults to primary)
        """
        self.calendar_id = calendar_id or 'primary'
        self.service = self._authenticate(service_account_file)
    
    def _authenticate(self, service_account_file):
        """Authenticate using service account credentials"""
        try:
            # Scopes required for calendar access
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            
            credentials = Credentials.from_service_account_file(
                service_account_file, 
                scopes=SCOPES
            )
            
            # Build the service
            service = build('calendar', 'v3', credentials=credentials)
            return service
            
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
    
    def get_events(self, time_min=None, time_max=None, max_results=10):
        """
        Get events from calendar
        
        Args:
            time_min (datetime): Start time for events (defaults to now)
            time_max (datetime): End time for events
            max_results (int): Maximum number of events to return
            
        Returns:
            list: List of calendar events
                """
        try:
            # Default to current time if not specified
            if time_min is None:
                time_min = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
            
            # Convert datetime to RFC3339 format - always ensure UTC
            if time_min.tzinfo is None:
                time_min = time_min.replace(tzinfo=timezone.utc)
            time_min_str = time_min.isoformat()
            
            if time_max:
                if time_max.tzinfo is None:
                    time_max = time_max.replace(tzinfo=timezone.utc)
                time_max_str = time_max.isoformat()
            else:
                time_max_str = None
            
            # Build the request
            events_request = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            )
            
            events_result = events_request.execute()
            events = events_result.get('items', [])
            
            return self._format_events(events)
                    
        except HttpError as error:
                    raise Exception(f"Failed to get events: {error}")
    
    def create_event(self, title, start_time, end_time, description=None, location=None):
        """
        Create a new calendar event
        
        Args:
            title (str): Event title
            start_time (datetime): Event start time
            end_time (datetime): Event end time
            description (str): Event description (optional)
            location (str): Event location (optional)
            
        Returns:
            dict: Created event details
        """
        try:
            event_body = {
                'summary': title,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                },
            }
            
            if description:
                event_body['description'] = description
            if location:
                event_body['location'] = location
            
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_body
            ).execute()
            
            return {
                'id': event['id'],
                'title': event['summary'],
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'link': event.get('htmlLink')
            }
            
        except HttpError as error:
            raise Exception(f"Failed to create event: {error}")
    
    def update_event(self, event_id, title=None, start_time=None, end_time=None, 
                    description=None, location=None, attendees_to_add=None):
        """
        Update an existing calendar event
        
        Args:
            event_id (str): ID of the event to update
            title (str): New event title (optional)
            start_time (datetime): New start time (optional)
            end_time (datetime): New end time (optional)
            description (str): New description (optional)
            location (str): New location (optional)
            attendees_to_add (list): List of attendee emails to add (optional)
            
        Returns:
            dict: Updated event details
        """
        try:
            # Get existing event first
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields if provided
            if title:
                event['summary'] = title
            if start_time:
                event['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'UTC',
                }
            if end_time:
                event['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'UTC',
                }
            if description is not None:
                event['description'] = description
            if location is not None:
                event['location'] = location
            
            # Add attendees if provided
            if attendees_to_add:
                # Initialize attendees list if it doesn't exist
                if 'attendees' not in event:
                    event['attendees'] = []
                    
                # Add new attendees
                for attendee in attendees_to_add:
                    if isinstance(attendee, str):
                        # If just an email is provided
                        event['attendees'].append({'email': attendee})
                    elif isinstance(attendee, dict) and 'email' in attendee:
                        # If attendee is provided as a dictionary
                        event['attendees'].append(attendee)
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            return {
                'id': updated_event['id'],
                'title': updated_event['summary'],
                'start': updated_event['start'].get('dateTime', updated_event['start'].get('date')),
                'end': updated_event['end'].get('dateTime', updated_event['end'].get('date')),
                'link': updated_event.get('htmlLink'),
                'attendees': updated_event.get('attendees', [])
            }
            
        except HttpError as error:
            raise Exception(f"Failed to update event: {error}")
    
    def delete_event(self, event_id):
        """
        Delete a calendar event
        
        Args:
            event_id (str): ID of the event to delete
            
        Returns:
            bool: True if successful
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return True
            
        except HttpError as error:
            raise Exception(f"Failed to delete event: {error}")
    
    def _format_events(self, events):
        """Format events for easier consumption"""
        formatted_events = []
        
        for event in events:
            formatted_event = {
                'id': event['id'],
                'title': event.get('summary', 'No Title'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'link': event.get('htmlLink', ''),
                'creator': event.get('creator', {}).get('email', ''),
                'status': event.get('status', ''),
            }
            formatted_events.append(formatted_event)
        
        return formatted_events

# Example usage and helper functions
# def example_usage():
#     """Example of how to use the GoogleCalendarManager"""
    
#     # Initialize the calendar manager
#     calendar_manager = GoogleCalendarManager(
#         service_account_file='./client_secrets.json',
#         calendar_id=os.getenv("CALENDAR_ID", "primary")
#     )
    
#     try:
#         # Get upcoming events
#         print("Getting upcoming events...")
#         events = calendar_manager.get_events(max_results=10)
#         for event in events:
#             print(f"- {event['title']}: {event['start']} to {event['end']}")
        
#         # Create a new event
#         # print("\nCreating new event...")
#         # start_time = datetime.utcnow() + timedelta(days=1)
#         # end_time = start_time + timedelta(hours=1)
        
#         # new_event = calendar_manager.create_event(
#         #     title="Team Meeting",
#         #     start_time=start_time,
#         #     end_time=end_time,
#         #     description="Weekly team sync",
#         #     location="Conference Room A"
#         # )
#         # print(f"Created event: {new_event['title']} (ID: {new_event['id']})")
        
#         # Update the event
#         # print("\nUpdating event...")
#         # updated_event = calendar_manager.update_event(
#         #     event_id=event['id'],
#         #     title="Updated Team Meeting",
#         #     description="Weekly team sync - Updated agenda",
#         #     attendees_to_add=["criptowder@gmail.com"]
#         # )
#         # print(f"Updated event: {updated_event['title']}")
        
#         # Delete the event (uncomment to test)
#         # print("\nDeleting event...")
#         # calendar_manager.delete_event(new_event['id'])
#         # print("Event deleted successfully")
        
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     example_usage()
