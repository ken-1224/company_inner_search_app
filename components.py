'''
このファイルは、画面表示に特化した関数定義のファイルです。
'''

############################################################
# ライブラリの読み込み
############################################################
import streamlit as st
import utils
import constants as ct


############################################################
# 関数定義
############################################################

def display_app_title():
    """
    タイトル表示
    """
    st.markdown(f"## {ct.APP_NAME}")

def display_select_mode():
    """
    回答モードのラジオボタンを表示（サイドバーに移動）
    """
    st.sidebar.radio(
        label="利用目的を選択してください",
        options=[ct.ANSWER_MODE_1, ct.ANSWER_MODE_2],
        key="mode"
    )

def display_initial_ai_message():
    """
    AIメッセージの初期表示（メインエリア：案内文、サイドバー：各モードの説明）
    """
    # メインエリアに表示
    with st.chat_message("assistant"):
        st.success("こんにちは。私は社内文書の情報をもとに回答する生成AIチャットボットです。サイドバーで利用目的を選択し、画面下部のチャット欄からメッセージを送信してください。")
        st.warning("⚠️ 具体的に入力したほうが期待通りの回答を得やすいです。")

    # サイドバーに各モードの説明を表示
    with st.sidebar:
        st.markdown("### 『社内文書検索』を選択した場合")
        st.info("入力内容と関連性が高い社内文書のありかを検索できます。")
        st.markdown("【入力例】社員の育成方針に関するMTGの議事録")

        st.markdown("---")

        st.markdown("### 『社内問い合わせ』を選択した場合")
        st.info("質問・要望に対して、社内文書の情報をもとに回答を得られます。")
        st.markdown("【入力例】人事部に所属している従業員情報を一覧化して")

def display_conversation_log():
    """
    会話ログの一覧表示
    """
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                if message["content"]["mode"] == ct.ANSWER_MODE_1:
                    if not "no_file_path_flg" in message["content"]:
                        st.markdown(message["content"]["main_message"])
                        icon = utils.get_source_icon(message['content']['main_file_path'])
                        if "main_page_number" in message["content"]:
                            st.success(f"{message['content']['main_file_path']}（p.{message['content']['main_page_number']}）", icon=icon)
                        else:
                            st.success(f"{message['content']['main_file_path']}", icon=icon)

                        if "sub_message" in message["content"]:
                            st.markdown(message["content"]["sub_message"])
                            for sub_choice in message["content"]["sub_choices"]:
                                icon = utils.get_source_icon(sub_choice['source'])
                                if "page_number" in sub_choice:
                                    st.info(f"{sub_choice['source']}（p.{sub_choice['page_number']}）", icon=icon)
                                else:
                                    st.info(f"{sub_choice['source']}", icon=icon)
                    else:
                        st.markdown(message["content"]["answer"])
                else:
                    st.markdown(message["content"]["answer"])
                    if "file_info_list" in message["content"]:
                        st.divider()
                        st.markdown(f"##### {message['content']['message']}")
                        for file_info in message["content"]["file_info_list"]:
                            icon = utils.get_source_icon(file_info)
                            if isinstance(file_info, dict):
                                source = file_info.get("source", "")
                                page = file_info.get("page_number", None)
                                if source.endswith(".pdf") and page is not None:
                                    st.info(f"{source}（p.{page}）", icon=icon)
                                else:
                                    st.info(source or str(file_info), icon=icon)
                            else:
                                st.info(file_info, icon=icon)