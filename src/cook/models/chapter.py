import requests
import sqlite3

import streamlit

from init import cfg


class Chapter:
    def __init__(self, id, name, lark_table_id, lark_view_id, rank, chapter_type=None):
        self.id = id
        self.name = name
        self.lark_table_id = lark_table_id
        self.lark_view_id = lark_view_id
        self.rank = rank
        self.chapter_type = chapter_type

    def __repr__(self):
        return f'{self.name}  ({self.lark_table_id})'


def load_chapters_from_sqlite() -> list[Chapter]:
    chapters = []
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM `chapters`'
                   'ORDER BY `rank` ASC')
    for row in cursor.fetchall():
        chapters.append(Chapter(*row))
    conn.close()
    return chapters


def load_chapters_from_api() -> list[Chapter]:

    url = f'{cfg.API_URL}/lesson/get_chatper_info'
    params = {
        'doc_id': cfg.LARK_APP_TOKEN
    }

    response = requests.get(url, params=params)
    print("请求详细信息:")
    print(f"URL: {url}")
    print(f"参数: {params}")
    
    print("\n响应详细信息:")
    print(f"状态码: {response.status_code}")
    print(f"响应头: {response.headers}")
    print(f"响应内容: {response.text}")

    chapters = []
    if response.status_code == 200:
        data = response.json()
        print(data)
        for item in data['data']:
            print(item)
            chapters.append(Chapter(
                id=item['lesson_no'],
                name=item['lesson_name'],
                lark_table_id=item['feishu_id'],
                lark_view_id=cfg.DEF_LARK_VIEW_ID,
                rank=int(item['lesson_no']),
                chapter_type=item['lesson_type']
            ))

    else:
        print(f"Failed to retrieve data: {response.status_code}")

    return chapters


LESSON_TYPE_TRIAL = 401
LESSON_TYPE_NORMAL = 402
LESSON_TYPE_EXTEND = 403
LESSON_TYPE_BRANCH = 404
LESSON_TYPE_BRANCH_HIDDEN = 405
LESSON_TYPES = {
    "试用课": LESSON_TYPE_TRIAL,
    "正式课": LESSON_TYPE_NORMAL,
    # "延展课": LESSON_TYPE_EXTEND,
    # "分支课": LESSON_TYPE_BRANCH,
    "隐藏分支课": LESSON_TYPE_BRANCH_HIDDEN
}


def update_chapter_from_api(table_id, view_id, title, index, lesson_type):
    url = f'{cfg.API_URL}/lesson/update_lesson'
    params = {
        'doc_id': cfg.LARK_APP_TOKEN,
        'table_id': table_id,
        'view_id': view_id,
        'title': title,
        'index': index,
        'lesson_type': lesson_type,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        print(response.json())
        streamlit.toast(f"《{title}》更新成功", icon="🎉")
    else:
        print(f"Failed to update data: {response.status_code}")
        streamlit.toast(f"《{title}》更新失败，错误码: {response.status_code}", icon="🚨")


def delete_chapter_from_api(table_id):
    url = f'{cfg.API_URL}/lesson/delete_lesson'
    params = {
        # 'doc_id': cfg.LARK_APP_TOKEN,
        'table_id': table_id,
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        print(response.json())
        streamlit.toast("删除成功", icon="🎉")
    else:
        print(f"Failed to delete data: {response.status_code}")
        streamlit.toast(f"删除失败，错误码: {response.status_code}", icon="🚨")


def get_follow_up_ask_prompt_template(lark_table_id):
    conn = sqlite3.connect(cfg.SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM `chapters_follow_up_ask_prompt` WHERE lark_table_id=?',
                   (lark_table_id,))
    result = cursor.fetchone()
    result = result[2] if result else ''
    conn.close()
    return result


if __name__ == '__main__':
    prompt = get_follow_up_ask_prompt_template('tbldUsmPMh6vcBxh')
    print(len(prompt), prompt)


    # 从API获取章节信息
    # chapters = load_chapters_from_api()


    # 从本地数据库获取
    # chapters = load_chapters_from_sqlite()
    #
    # for chapter in chapters:
    #     print(chapter.id, chapter.name, chapter.lark_table_id, chapter.lark_view_id, chapter.rank)
    #
    # chapters_df = DataFrame([chapter.__dict__ for chapter in chapters])
    # print(chapters_df)


    # # 测试新增章节
    # update_chapter_from_api(
    #     table_id='tblkkj1WaozcngwQ',
    #     title='测试新增分支章节（index不连续）',
    #     index='20',
    #     lesson_type=405
    # )

    # # 测试新增正式章节
    # update_chapter_from_api(
    #     table_id='tbldoFfQAPZjFvzg',
    #     title='测试新增正式章节（index不连续）',
    #     index='23',
    #     lesson_type=402
    # )

    # 测试删除章节
    # delete_chapter_from_api('tblkkj1WaozcngwQ')
    # delete_chapter_from_api('tblQhi1ZutfUhW2T')



