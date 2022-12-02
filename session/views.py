"""Views for the USSD app."""

import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Session


def page_handler(phone_number, user_data, session_id, response_msg_type):
    """Handle session based on current page."""

    """Get session instance."""
    session = Session.objects.get(id=session_id)

    response = ""

    if session.page == 1:
        """If user is at page 1(feeling page)"""
        response = f"Welcome {phone_number}, to Solomon's USSD app!\n"
        response += "How are you feeling?\n"
        response += "1. Not well.\n"
        response += "2. Feeling frisky.\n"
        response += "3. Sad.\n"
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
        session.feeling = user_data
        session.page = 3
        session.save()
        session.refresh_from_db()
        response = f"Why are you {session.get_feeling_display()}?\n"
        response += "1. Health.\n"
        response += "2. Money.\n"
        response += "3. Relationship.\n"

    elif session.page == 3:
        """
        Handle session when user is at page 3
        """
        if len(user_data) == 2:
            """
            Check if there was a second choice from direct dial and
            set reason accordingly.
            """
            session.reason = user_data[1]
        else:
            session.reason = user_data
        session.save()
        session.refresh_from_db()
        response = f"You are {session.get_feeling_display()} because of {session.get_reason_display()}.\n"  # noqa
        response_msg_type = False

        if session.page == 3 and response_msg_type is False:
            """Delete session from the database at the end of session"""
            session.delete()

    return response_msg_type, response


@csrf_exempt
def index(request) -> JsonResponse:
    """POST request handler"""
    if request.method == "POST":
        """Convert the request body to json:"""
        json_data = json.loads(request.body)
        user_id = json_data.get("USERID")
        msg_type = json_data.get("MSGTYPE")
        phone_number = json_data.get("MSISDN")
        user_data = json_data.get("USERDATA")
        session_id = json_data.get("SESSIONID")

        response_msg_type = True

        """Set initial response"""
        response = "Your selection was invalid, session terminated."

        """Return error message and terminate session on invalid input"""
        if msg_type is False and user_data not in ["1", "2", "3"]:
            session = Session.objects.get(id=session_id)
            session.delete()
            return JsonResponse(
                {
                    "USERID": user_id,
                    "MSISDN": phone_number,
                    "MSG": response,
                    "MSGTYPE": False,
                }
            )

        """Handle a direct dial"""
        if msg_type is True and user_data.startswith("*920*7868"):
            session = Session.objects.create(id=session_id)

            """Remove main USSD code to get remaining choices"""
            user_data = user_data.replace("*920*7868", "")

            if len(user_data) > 0:
                """If more choices exist, remove the asterisks(*)"""
                user_data = user_data.replace("*", "")
                print(user_data)

                """Return error message if choices are not 1 or 2"""
                if len(user_data) not in [1, 2]:
                    session.delete()
                    return JsonResponse(
                        {
                            "USERID": user_id,
                            "MSISDN": phone_number,
                            "MSG": f"You entered {len(user_data)} choices, however the minimum is 1 and the maximum is 2.",  # noqa
                            "MSGTYPE": False,
                        }
                    )

                """Ensure all choices are valid else, return error message."""
                for choice in user_data:
                    if choice not in ["1", "2", "3"]:
                        session.delete()
                        return JsonResponse(
                            {
                                "USERID": user_id,
                                "MSISDN": phone_number,
                                "MSG": response,
                                "MSGTYPE": False,
                            }
                        )
                """Set feeling to first choice:"""
                session.feeling = user_data[0]
                """Set session page to 2"""
                session.page = 2
                if len(user_data) == 2:
                    """Set session page to 3 if there is a second choice."""
                    session.page = 3
                session.save()

        response_msg_type, response = page_handler(
            phone_number=phone_number,
            session_id=session_id,
            user_data=user_data,
            response_msg_type=response_msg_type,
        )

        """Return Json response with processed information"""
        return JsonResponse(
            {
                "USERID": user_id,
                "MSISDN": phone_number,
                "MSG": response,
                "MSGTYPE": response_msg_type,
            }
        )
