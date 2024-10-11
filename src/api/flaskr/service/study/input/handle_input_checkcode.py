import time
from trace import Trace
from flask import Flask
from flaskr.service.common.models import AppException
from flaskr.service.lesson.models import AILessonScript
from flaskr.service.order.models import AICourseLessonAttend
from flaskr.service.profile.funcs import (
    get_user_profile_labels,
    update_user_profile_with_lable,
)
from flaskr.service.study.const import INPUT_TYPE_CHECKCODE, ROLE_TEACHER
from flaskr.service.study.input_funcs import BreakException
from flaskr.service.study.plugin import register_input_handler
from flaskr.service.study.utils import generation_attend, make_script_dto
from flaskr.service.user.common import verify_sms_code_without_phone
from flaskr.dao import db


@register_input_handler(input_type=INPUT_TYPE_CHECKCODE)
def handle_input_checkcode(
    app: Flask,
    user_id: str,
    attend: AICourseLessonAttend,
    script_info: AILessonScript,
    input: str,
    trace: Trace,
    trace_args,
):
    try:
        origin_user_id = user_id
        ret = verify_sms_code_without_phone(app, user_id, input)
        verify_user_id = ret.userInfo.user_id
        if origin_user_id != verify_user_id:
            app.logger.info(
                f"origin_user_id:{origin_user_id},verify_user_id:{verify_user_id} copy profile"
            )
            new_profiles = get_user_profile_labels(app, origin_user_id)
            update_user_profile_with_lable(app, verify_user_id, new_profiles)
        yield make_script_dto(
            "profile_update",
            {"key": "phone", "value": ret.userInfo.mobile},
            script_info.script_id,
        )
        yield make_script_dto(
            "user_login",
            {
                "phone": ret.userInfo.mobile,
                "user_id": ret.userInfo.user_id,
                "token": ret.token,
            },
            script_info.script_id,
        )
        input = None
        span = trace.span(name="user_input_phone", input=input)
        span.end()
    except AppException as e:
        for i in e.message:
            yield make_script_dto("text", i, script_info.script_id)
            time.sleep(0.01)
        yield make_script_dto("text_end", "", script_info.script_id)
        yield make_script_dto(
            INPUT_TYPE_CHECKCODE, script_info.script_ui_content, script_info.script_id
        )
        log_script = generation_attend(app, attend, script_info)
        log_script.script_content = e.message
        log_script.script_role = ROLE_TEACHER
        db.session.add(log_script)
        raise BreakException