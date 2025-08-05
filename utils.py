"""
このファイルは、画面表示以外の様々な関数定義のファイルです。
"""

############################################################
# ライブラリの読み込み
############################################################
import os
import time
from dotenv import load_dotenv
import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import constants as ct
import json

############################################################
# 設定関連
############################################################
load_dotenv()
DEBUG = False  # ← True にするとデバッグ情報表示

############################################################
# 関数定義
############################################################

def get_llm_response(chat_message):
    llm = ChatOpenAI(model_name=ct.MODEL, temperature=ct.TEMPERATURE)

    question_generator_prompt = ChatPromptTemplate.from_messages([
        ("system", ct.SYSTEM_PROMPT_CREATE_INDEPENDENT_TEXT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    question_answer_template = (
        ct.SYSTEM_PROMPT_DOC_SEARCH if st.session_state.mode == ct.ANSWER_MODE_1
        else ct.SYSTEM_PROMPT_INQUIRY
    )

    question_answer_prompt = ChatPromptTemplate.from_messages([
        ("system", question_answer_template),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

    history_aware_retriever = create_history_aware_retriever(
        llm, st.session_state.retriever, question_generator_prompt
    )
    question_answer_chain = create_stuff_documents_chain(llm, question_answer_prompt)
    chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    if DEBUG:
        st.write("🚩 chain.invoke 実行前")

    start_time = time.time()

    try:
        result = chain.invoke({
            "input": chat_message,
            "chat_history": st.session_state.chat_history
        })
    except Exception as e:
        st.error("❌ chain.invoke中にエラーが発生しました")
        st.exception(e)
        raise e

    if DEBUG:
        st.write("✅ chain.invoke 実行後")
        st.write("🕒 実行時間:", round(time.time() - start_time, 2), "秒")

    if result is None:
        st.error("❌ chain.invokeの結果が None でした。")
        st.stop()

    # JSON変換できるように整形
    def serialize_document(doc):
        return {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
        }

    result_serializable = result.copy()
    if isinstance(result, dict) and "context" in result:
        result_serializable["context"] = [serialize_document(doc) for doc in result["context"]]

    if DEBUG:
        with st.expander("🧪 デバッグ情報（開発者向け）"):
            st.write("📦 resultの型:", type(result))
            st.code(json.dumps(result_serializable, indent=2, ensure_ascii=False), language="json")

    docs = result.get("context", []) if isinstance(result, dict) else []
    if not isinstance(docs, list) or len(docs) == 0:
        raise ValueError("関連する文書が見つかりませんでした。PDFが読み込まれていないか、質問と一致する内容が含まれていない可能性があります。")

    answer_raw = result.get("answer", "回答を生成できませんでした。")
    answer_text = answer_raw.get("text", str(answer_raw)) if isinstance(answer_raw, dict) else str(answer_raw)

    st.session_state.chat_history.extend([
        HumanMessage(content=chat_message),
        HumanMessage(content=answer_text)
    ])

    sources = []
    for doc in result.get("context", []):
        metadata = doc.metadata
        source_path = metadata.get("source") or metadata.get("file_path") or "不明な出典"
        page_number = metadata.get("page")
        source_info = {"source": source_path}
        if isinstance(page_number, int):
            source_info["page_number"] = page_number + 1
        sources.append(source_info)

    # ✅ UIとしてシンプルな回答だけ返す
    if st.session_state.mode == ct.ANSWER_MODE_1:
        return {
            "mode": ct.ANSWER_MODE_1,
            "main_message": answer_text,
            "main_file_path": sources[0]["source"] if sources else None,
            "main_page_number": sources[0].get("page_number") if sources else None,
            "sub_message": "他の参考文書：",
            "sub_choices": sources[1:] if len(sources) > 1 else []
        }
    else:
        return {
            "mode": ct.ANSWER_MODE_2,
            "answer": answer_text,
            "message": "参考にした文書の一覧：",
            "file_info_list": [
                f"{s['source']}（p.{s['page_number']}）" if "page_number" in s else s["source"]
                for s in sources
            ]
        }
    

def build_error_message(message):
    """
    エラーメッセージと共通の管理者問い合わせメッセージを連結する
    """
    return "\n".join([message, ct.COMMON_ERROR_MESSAGE])