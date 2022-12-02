"""Views for the USSD app."""
from django.views import View
import json
from django.http import JsonResponse
from .models import Session


class Index(View):
    """Handle USSD application logic"""

    """Allow only post requests"""
    http_method_names = ["post"]

    def setup(self, request):
        """Initialize attributes shared by all view methods."""

        """Convert the request body to json:"""
        json_data = json.loads(request.body)

        self.user_id = json_data.get("USERID")
        self.msg_type = json_data.get("MSGTYPE")
        self.phone_number = json_data.get("MSISDN")
        self.user_data = json_data.get("USERDATA")
        self.session_id = json_data.get("SESSIONID")
        self.request = request

    def post(self, request):
        """Post request handler."""
        if self.msg_type is False and self.user_data not in ["1", "2", "3"]:
            message, response_msg_type = self.invalid_selection_handler()
        elif self.msg_type is False or (
            self.msg_type is True and self.user_data == "*920*7868"
        ):
            message, response_msg_type = self.page_handler()
        elif self.msg_type is True and self.user_data.startswith("*920*7868"):
            message, response_msg_type = self.direct_dial_handler()

        """Return Json response with processed information"""
        return JsonResponse(
            {
                "USERID": self.user_id,
                "MSISDN": self.phone_number,
                "MSG": message,
                "MSGTYPE": response_msg_type,
            }
        )

    def invalid_selection_handler(self):
        """
        Returns error message, set response_msg_type to false and clear session
        from database on invalid user response.
        """
        session = Session.objects.filter(id=self.session_id)
        session.delete()
        message = "Your selection was invalid, session terminated."
        response_msg_type = False
        return message, response_msg_type

    def direct_dial_handler(self):
        """Handles a direct dial attempt from user."""

        """Remove main USSD code to get remaining choices"""
        self.user_data = self.user_data.replace("*920*7868", "")

        """Remove the asterisks(*) to get the choice numbers"""
        self.user_data = self.user_data.replace("*", "")

        if len(self.user_data) not in [1, 2]:
            """Return error message if number of choices are not 1 or 2"""
            message, response_msg_type = self.invalid_selection_handler()
            return message, response_msg_type

        for choice in self.user_data:
            """Ensure all choices are valid else, return error message."""
            if choice not in ["1", "2", "3"]:
                message, response_msg_type = self.invalid_selection_handler()
                return message, response_msg_type

        """Create session if user input passes validation."""
        session = Session.objects.create(id=self.session_id)

        """Set feeling to first choice:"""
        session.feeling = self.user_data[0]
        """Set session page to 2"""
        session.page = 2
        if len(self.user_data) == 2:
            """Set session page to 3 if there is a second choice."""
            session.page = 3
        session.save()
        message, response_msg_type = self.page_handler()
        return message, response_msg_type

    def page_handler(self):
        """Handle session based on current page."""
        session, created = Session.objects.get_or_create(id=self.session_id)
        message = ""
        response_msg_type = True

        if session.page == 1:
            """If user is at page 1(feeling page), request for feeling."""
            message = f"Welcome {self.phone_number}, to Solomon's USSD app!\n\n"  # noqa
            message += "How are you feeling?\n"
            message += "1. Not well.\n"
            message += "2. Feeling frisky.\n"
            message += "3. Sad.\n"
            """Set session page to 2 and save"""
            session.page = 2
            session.save()

        elif session.page == 2:
            """
            If user is at page 2(reasons page),
            set reason to user input(user_data) and
            set page to 3(result page) and
            and save the instance.
            """
            session.feeling = self.user_data
            session.page = 3
            session.save()
            session.refresh_from_db()
            message = f"Why are you {session.get_feeling_display()}?\n"
            message += "1. Health.\n"
            message += "2. Money.\n"
            message += "3. Relationship.\n"

        elif session.page == 3:
            """
            Handle session when user is at page 3.
            """
            if len(self.user_data) == 2:
                """
                Check if there was a second choice from direct dial and
                set reason accordingly.
                """
                session.reason = self.user_data[1]
            else:
                session.reason = self.user_data
            session.save()
            session.refresh_from_db()
            message = f"You are {session.get_feeling_display()} because of {session.get_reason_display()}.\n"  # noqa
            response_msg_type = False

        if session.page == 3 and response_msg_type is False:
            """Delete session from the database at the end of session"""
            session.delete()

        return message, response_msg_type
