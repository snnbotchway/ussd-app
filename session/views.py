"""Views for the USSD app."""

import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Session


@csrf_exempt
def index(request) -> JsonResponse:
    """POST request handler"""
    if request.method == "POST":
        json_data = json.loads(request.body)
        user_id = json_data.get("USERID")
        msg_type = json_data.get("MSGTYPE")
        phone_number = json_data.get("MSISDN")
        user_data = json_data.get("USERDATA")
        session_id = json_data.get("SESSIONID")

        response_msg_type = True
        response = "Your selection was invalid, session terminated."

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

        if msg_type is True and user_data.startswith("*920*7868"):
            session = Session.objects.create(id=session_id)
            user_data = user_data.replace("*920*7868", "")

            if len(user_data) > 0:
                user_data = user_data.replace("*", "")

                if len(user_data) > 2 or len(user_data) < 1:
                    session.delete()
                    return JsonResponse(
                        {
                            "USERID": user_id,
                            "MSISDN": phone_number,
                            "MSG": f"You entered {len(user_data)} choices, however the minimum is 1 and the maximum is 2.",  # noqa
                            "MSGTYPE": False,
                        }
                    )
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
                session.feeling = user_data[0]
                session.page = 2
                if len(user_data) == 2:
                    session.page = 3
                session.save()

        session = Session.objects.get(id=session_id)

        response = ""

        if session.page == 1:
            response = f"Welcome {phone_number}, to Solomon's USSD app.\n"
            response += "How are you feeling?"
            response += "1. Not well \n"
            response += "2. Feeling frisky \n"
            response += "3. Sad  \n"
            session.page = 2
            session.save()

        elif session.page == 2:
            session.feeling = user_data
            session.page = 3
            session.save()
            session.refresh_from_db()
            response = f"Why are you {session.get_feeling_display()}?\n"
            response += "1. Health \n"
            response += "2. Money \n"
            response += "3. Relationship \n"

        elif session.page == 3:
            if len(user_data) == 2:
                session.reason = user_data[1]
            else:
                session.reason = user_data
            session.save()
            session.refresh_from_db()
            response = f"You are {session.get_feeling_display()} because of {session.get_reason_display()}.\n"  # noqa
            response_msg_type = False

        if session.page == 3 and response_msg_type is False:
            session.delete()

        return JsonResponse(
            {
                "USERID": user_id,
                "MSISDN": phone_number,
                "MSG": response,
                "MSGTYPE": response_msg_type,
            }
        )
