import streamlit as st
from dotenv import load_dotenv
import openai
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import base64
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Streamlit 페이지 설정
st.set_page_config(page_title="ETF 질의응답 챗봇", page_icon=":robot:")

# 제목 및 설명
st.title("ETF 질의응답 챗봇")
st.markdown("ETF 관련 질문을 입력하고 PDF 문서를 업로드하세요.")

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 챗 히스토리 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 파일 업로드 위젯 (사이드바)
with st.sidebar:
    uploaded_file = st.file_uploader("PDF 파일 업로드", type="pdf") #pdf 외에도 다양한 형식으로 시도해 볼 수 있습니다.

# 환경 변수 로드 및 OpenAI API 키 설정 (숨김)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

# 여기서부터 2차,3차 업무를 거쳐 구현한 RAG 파이프라인입니다.
if uploaded_file and api_key:
    # 파일을 임시 파일로 저장
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    # 문서 로드
    loader = PyMuPDFLoader("temp.pdf")
    docs = loader.load()

    # 문서 미리보기
    st.sidebar.subheader("문서 미리보기")
    st.sidebar.write(docs[0].page_content[:500] + "...")

    # 문서 분할
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_documents = text_splitter.split_documents(docs)

    # 임베딩 생성
    embeddings = OpenAIEmbeddings()

    # 벡터 DB 생성 및 저장
    vectorstore = FAISS.from_documents(documents=split_documents, embedding=embeddings)

    # 검색기 생성
    retriever = vectorstore.as_retriever()

    # 프롬프트 템플릿
    prompt = PromptTemplate.from_template(
        """
        너는 AI를 활용한 자기주도 학습을 돕는 교육 전문가야.  
        다음과 같은 세부 사항을 포함해서 명확하고 친절하게 설명해줘.

        1. 참조한 강의자료 또는 보고서의 출처 및 페이지 정보
        2. 받은 질문과 유사한 학습자들이 자주 묻는 질문 3가지

        질문:  
        {question}

        검색된 문서:  
        {context}

        답변 예시:  
        질문: 'RAG가 뭐예요? 왜 쓰는 건가요?'  
        답변: RAG(Retrieval-Augmented Generation)는 AI가 답을 만들 때 관련 문서를 먼저 찾아 참고하는 방식입니다. 단순한 암기형 생성보다 더 정확하고 근거 있는 답변을 제공할 수 있어 교육용 AI 시스템에서 자주 활용돼요. 예를 들어 수업자료를 기반으로 질문에 정확히 답해줄 수 있는 거죠.

        출처:  
        강의자료: ‘생성형 AI 개론 강의안’  
        페이지: 15페이지

        유사한 질문:  
        - "벡터 DB는 왜 사용하는 거예요?"  
        - "LLM이 단독으로 답변하면 안 되나요?" 
        """
    )

    # LLM 생성
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    # 체인 생성
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )



# 여기서부터 Streamlit을 활용한 프론트엔드 구현 부분입니다. 자신이 기획한 서비스에 맞게 다양한 기능들을 추가해 보세요.
# 질의응답 입력 위젯
if prompt := st.chat_input("질문을 입력하세요:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)

        # 체인 실행 및 결과 출력
        with st.spinner("답변 생성 중..."):
            response = chain.invoke(prompt)

            # 답변 요약 (간단한 요약)
            summary = response.split('\n')[0][:200] + "..." if len(response) > 200 else response

            # 답변 및 요약 표시
            st.session_state.messages.append({"role": "assistant", "content": f"**요약:** {summary}\n\n**전체 답변:**\n{response}"})
            st.chat_message("assistant").markdown(f"**요약:** {summary}\n\n**전체 답변:**\n{response}")

            # 답변 다운로드 기능
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            c.drawString(100, 750, response)
            c.save()
            pdf_out = pdf_buffer.getvalue()

            st.download_button(
                label="답변 다운로드 (PDF)",
                data=pdf_out,
                file_name="response.pdf",
                mime="application/pdf"
            )

            # 검색 결과 시각화 (워드 클라우드)
            text = " ".join([doc.page_content for doc in retriever.invoke(prompt)])
            
            # 한글 폰트 설정 (macOS의 경우)
            import platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                font_path = "/System/Library/Fonts/AppleGothic.ttf"
            elif system == "Windows":
                font_path = "C:/Windows/Fonts/malgun.ttf"  # 맑은 고딕
            else:  # Linux
                font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
            
            try:
                wordcloud = WordCloud(
                    width=800, 
                    height=400, 
                    background_color="white",
                    font_path=font_path,
                    max_words=100,
                    colormap='Set3'
                ).generate(text)
                
                plt.figure(figsize=(10, 5))
                plt.imshow(wordcloud, interpolation="bilinear")
                plt.axis("off")
                st.pyplot(plt)
            except Exception as e:
                st.warning(f"워드클라우드 생성 중 오류 발생: {e}")
                st.text("텍스트 미리보기:")
                st.text(text[:500] + "...")

            # 사용자 맞춤 설정 (답변 길이)
            if st.checkbox("짧은 답변 보기"):
                st.write(f"**짧은 답변:** {summary}") 
else:
    st.info("사이드바에서 PDF 파일을 업로드해주세요.") 