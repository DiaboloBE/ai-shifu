from email import utils

from .models import *
from .const import *
import uuid
from flask import Flask
from ...dao import db
from ...api.feishu import list_records
import json
from ...util.uuid import generate_id
from sqlalchemy import func


class AICourseDTO:
    def __init__(self, course_id, course_name, course_desc, course_price, course_status, course_feishu_id, status):
        self.course_id = course_id
        self.course_name = course_name
        self.course_desc = course_desc
        self.course_price = course_price
        self.course_status = course_status
        self.course_feishu_id = course_feishu_id
        self.status = status

class AILessonDTO:
    def __init__(self, lesson_id, course_id, lesson_name, lesson_desc, lesson_no, lesson_index, lesson_feishu_id, lesson_status, status):
        self.lesson_id = lesson_id
        self.course_id = course_id
        self.lesson_name = lesson_name
        self.lesson_desc = lesson_desc
        self.lesson_no = lesson_no
        self.lesson_index = lesson_index
        self.lesson_feishu_id = lesson_feishu_id
        self.lesson_status = lesson_status
        self.status = status
class AILessonInfoDTO:
    def __init__(self,lesson_no:str,lesson_name:str,lesson_id:str,feishu_id:str,lesson_type) -> None:
        self.lesson_no = lesson_no
        self.lesson_name = lesson_name
        self.lesson_id = lesson_id
        self.feishu_id = feishu_id
        self.lesson_type = lesson_type
    def __json__(self):
        return {
            'lesson_no':self.lesson_no,
            'lesson_name':self.lesson_name,
            'lesson_id':self.lesson_id,
            'feishu_id':self.feishu_id,
            'lesson_type':self.lesson_type
        }
class AIScriptDTO:
    def __init__(self, script_id, lesson_id, script_name, script_desc, script_index, script_feishu_id, script_version, script_no, script_type, script_content_type, script_prompt, script_model, script_profile, script_media_url, script_ui_type, script_ui_content, script_check_prompt, script_check_flag, script_ui_profile, script_end_action, script_other_conf, status):
        self.script_id = script_id
        self.lesson_id = lesson_id
        self.script_name = script_name
        self.script_desc = script_desc
        self.script_index = script_index
        self.script_feishu_id = script_feishu_id
        self.script_version = script_version
        self.script_no = script_no
        self.script_type = script_type
        self.script_content_type = script_content_type
        self.script_prompt = script_prompt
        self.script_model = script_model
        self.script_profile = script_profile
        self.script_media_url = script_media_url
        self.script_ui_type = script_ui_type
        self.script_ui_content = script_ui_content
        self.script_check_prompt = script_check_prompt
        self.script_check_flag = script_check_flag
        self.script_ui_profile = script_ui_profile
        self.script_end_action = script_end_action
        self.script_other_conf = script_other_conf
        self.status = status


DB_SAVE_MAP = {
    '剧本简述': 'script_name',
    '剧本类型': 'script_type',
    '内容格式': 'script_content_type',
    '模版内容': 'script_prompt',
    '模版变量': 'script_profile',
    '检查模版内容': 'script_check_prompt',
    '输入成功标识': 'script_check_flag',
    '自定义模型':'script_model',
    '解析用户输入内容':'script_ui_profile',
    '媒体URL':'script_media_url',
    '输入框提示': 'script_ui_content',
    '按钮组配置': 'script_other_conf',
    '后续交互':'script_ui_type',
    '按钮标题': 'script_ui_content'

}


DB_SAVE_DICT_MAP= {
    '剧本类型': SCRIPT_TYPES,
    '内容格式': CONTENT_TYPES,
    '后续交互': UI_TYPES
}

def update_lesson_info(app:Flask,doc_id:str,table_id:str,view_id:str,title:str=None,index:int=None,lesson_type:int = LESSON_TYPE_NORMAL):
    with app.app_context():
        # 检查课程
        course = AICourse.query.filter_by(course_feishu_id = doc_id).first()
        if course is None:
            course = AICourse()
            course.course_id = str(generate_id(app))
            course.course_feishu_id = doc_id
            course.status = 1
            course.course_name = 'AI Python'
            course.course_desc = 'AI Python'
            db.session.add(course)
        course_id = course.course_id        
        page_token = None
        lessons = []
        unconf_fields = []
        parent_lesson = AILesson.query.filter(AILesson.course_id ==course_id
                                                   ,AILesson.lesson_feishu_id==table_id,
                                                    func.char_length(AILesson.lesson_no)==2).first()
        lessonNo = str(index).zfill(2)
        if parent_lesson is None:
            parent_lesson = AILesson()
            parent_lesson.lesson_id = str(generate_id(app))
            parent_lesson.course_id = course.course_id
            parent_lesson.lesson_name = title
            parent_lesson.lesson_desc = ''
            parent_lesson.status = 1
            parent_lesson.lesson_no = lessonNo
            parent_lesson.lesson_feishu_id = table_id
            parent_lesson.lesson_type = lesson_type
            if int(index) > 1 :
                parent_lesson.pre_lesson_no = str(int(index) -1 ).zfill(2)
            else:
                parent_lesson.pre_lesson_no ="" 
            db.session.add(parent_lesson)
        else:
            parent_lesson.lesson_name = title
            parent_lesson.lesson_desc = ''
            parent_lesson.status = 1
            parent_lesson.lesson_no = lessonNo
            parent_lesson.status = 1
            parent_lesson.lesson_feishu_id = table_id
            parent_lesson.lesson_type = lesson_type
            if int(index) > 1 :
                parent_lesson.pre_lesson_no = str(int(index) -1 ).zfill(2)
            else:
                parent_lesson.pre_lesson_no ="" 
        subIndex = 0
        childLessons = [AILesson]
        script_index = 0
        while True:
            resp = list_records(app,doc_id,table_id,view_id=view_id,page_token=page_token,page_size=100)
            records = resp['data']['items']
            app.logger.info('records:'+str(len(records)))
            for record in records:
                if record['fields'].get('小节',None):
                    title = "".join(t['text'] for t in  record['fields']['小节']).strip()
                    if title is None:
                        app.logger.info('title is None')
                    if title is None or title == '' and lesson is not None:
                        pass
                    else:
                        lesson = next((l for l in childLessons if hasattr(l, 'lesson_name') and  l.lesson_name == title), None)
                else:
                    lesson = parent_lesson
                if lesson is None:
                    ## 新来的一个小节
                    script_index = 0
                    subIndex = subIndex+  1
                    lesson = AILesson.query.filter(AILesson.course_id == course_id,
                                               AILesson.lesson_feishu_id == table_id,
                                               AILesson.lesson_name == title).first()
                    if lesson is None:
                        lesson = AILesson()
                        lesson.lesson_id = str(generate_id(app))
                        lesson.course_id = course.course_id
                        lesson.lesson_name = title
                        lesson.lesson_desc = ''
                        lesson.status = 1
                        lesson.lesson_feishu_id = table_id
                        lesson.lesson_no = lessonNo + str(subIndex).zfill(2) 
                        lesson.lesson_type = lesson_type
                        if subIndex>1:
                            lesson.pre_lesson_no =  lessonNo + str(subIndex-1).zfill(2) 
                        else:
                            lesson.pre_lesson_no = ""
                        db.session.add(lesson)
                    else:
                        lesson.lesson_name = title
                        lesson.lesson_desc = ''
                        lesson.status = 1
                        lesson.lesson_feishu_id = table_id
                        lesson.lesson_type = lesson_type
                        lesson.lesson_no = lessonNo + str(subIndex).zfill(2) 
                        if subIndex>1:
                            lesson.pre_lesson_no =  lessonNo + str(subIndex-1).zfill(2) 
                        else:
                            lesson.pre_lesson_no = ""
                    childLessons.append(lesson)
                script_index = script_index + 1
                record_id = record['record_id']
                scripDb = {}
                scripDb['script_feishu_id'] = str(record_id)
                scripDb['lesson_id'] = lesson.lesson_id
                scripDb['script_desc'] = ''
                scripDb['script_prompt']=''
                scripDb['script_ui_profile']=''
                scripDb['script_end_action']=''
                scripDb['script_other_conf']=''
                scripDb['script_profile']=''
                scripDb['script_media_url']=''
                scripDb['script_ui_content']=''
                scripDb['script_check_prompt']=''
                scripDb['script_check_flag']=''
                scripDb['script_index']=script_index
                scripDb['script_ui_type']=UI_TYPE_CONTINUED
                scripDb['script_ui_content']='继续'
                scripDb['script_type']=SCRIPT_TYPE_FIX
                scripDb['script_content_type']=CONTENT_TYPE_TEXT
                scripDb['script_model']='ERNIE-Speed-8K'
                for field  in record['fields']:
                    val_obj = record['fields'][field]
                    db_field = DB_SAVE_MAP.get(field.strip())
                    val = ''
                    if isinstance(val_obj,str):
                        val = val_obj
                    elif isinstance(val_obj , list):
                        val = "".join( t["text"] if  isinstance(t,dict) else "["+t+"]"  for  t in val_obj)
                    elif isinstance(val_obj,dict):
                        val = val_obj.get('text')
                    else:
                        app.logger.info('val_obj:'+str(val_obj))
                    if db_field :
                        if field in DB_SAVE_DICT_MAP:
                            orig_val = val
                            val = DB_SAVE_DICT_MAP[field.strip()].get(orig_val.strip())
                            if val is None:
                                app.logger.info('val is None:'+field+",value:"+orig_val)
                        if val is not None:   
                            scripDb[db_field] = val
                    else:
                        if unconf_fields.count(field)==0:
                            unconf_fields.append(field)
                    continue
                scrip = AILessonScript.query.filter(AILessonScript.script_feishu_id == record_id).first()
                if scrip is None:
                    scripDb['script_id']= str(generate_id(app))
                    db.session.add(AILessonScript(**scripDb))
                else:
                    for key in scripDb:
                        setattr(scrip,key,scripDb[key])
            if resp['data']['has_more']:
                page_token = resp['data']['page_token']
            else:
                break
        app.logger.info('unconf_fields:'+str(unconf_fields))
        db.session.commit()
        return

def get_lesson_scripts(app:Flask,lesson_id:str):
    pass
# 运行课程脚本
# 1. 从数据库中获取脚本
# 2. 从数据库中获取脚本的内容
# 3. 从数据库中获取脚本的模型
def run_lesson_script(app:Flask,lesson_id:str,script_id:str):
    with app.app_context():
        script = AILessonScript.query.filter_by(script_id = script_id).first()
        if script is None:
            return None
        return script
# 得到课程列表
def get_lessons(app:Flask,feshu_doc_id)->list[AILessonInfoDTO]:
    with app.app_context():
        course = AICourse.query.filter(AICourse.course_feishu_id == feshu_doc_id).first()
        if course is None:
            return []
        lessons = AILesson.query.filter(AILesson.status==1,AILesson.course_id==course.course_id, func.length(AILesson.lesson_no) ==2).all()
        lessons = sorted(lessons, key=lambda x: (len(x.lesson_no), x.lesson_no))
        lessonInfos = []
        for lesson in lessons:
            lessonInfo = AILessonInfoDTO(lesson.lesson_no,lesson.lesson_name,lesson.lesson_id,lesson.lesson_feishu_id,lesson.lesson_type)
            lessonInfos.append(lessonInfo)
        return lessonInfos
     
    
