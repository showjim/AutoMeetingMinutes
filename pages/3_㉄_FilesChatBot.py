import streamlit as st
import os
from src.chat import ChatBot


work_path = os.path.abspath('.')
reset_db = False
chat = ChatBot(work_path + "/tempDir/output",
               work_path + "/index",
               work_path)
st.title("㉄ Chat with files")

def set_reload_flag():
    # st.write("New document need upload")
    st.session_state["vectorreloadflag"] = True

def is_upload_status_changed():
    # st.write("New document need upload")
    st.session_state["upload_changed"] = True

def main():
    # initial parameter & LLM
    if "vectorreloadflag" not in st.session_state:
        st.session_state["vectorreloadflag"] = None
    work_path = os.path.abspath('.')
    # Layout of output/setup containers
    setup_container = st.container()
    instruction_container = st.container()
    response_container = st.container()

    with st.sidebar:
        st.sidebar.expander("Settings")
        st.sidebar.subheader("Parameter for document chains")
        aa_combine_type = st.sidebar.radio(label="1.Types of combine document chains", options=["stuff", "map_reduce"],
                                           on_change=set_reload_flag)
        aa_temperature = st.sidebar.selectbox(label="2.Temperature (0~1)",
                                              options=["0", "0.2", "0.4", "0.6","0.8", "1.0"],
                                              index=1,
                                              on_change=set_reload_flag)
        aa_max_resp = st.sidebar.slider(label="3.Max response",
                                        min_value=256,
                                        max_value=2048,
                                        value=512,
                                        on_change=set_reload_flag)
        if st.session_state["vectorreloadflag"] == True:
            chat.initial_llm(aa_max_resp, float(aa_temperature))
            st.session_state["vectorreloadflag"] = False

    # main page
    with setup_container:
        st.write("Please upload your file below.")
        if "vectordb" not in st.session_state:
            st.session_state["vectordb"] = None
        # if "upload_changed" not in st.session_state:
        #     st.session_state["upload_changed"] = False
        file_path = st.file_uploader("Upload a document file", type=["pdf","txt","pptx","docx","html"])#, on_change=is_upload_status_changed)
        if st.button("Upload"):
            if file_path is not None:
                # save file
                with st.spinner('Reading file'):
                    uploaded_path = os.path.join(work_path + "/tempDir/output", file_path.name)
                    with open(uploaded_path, mode="wb") as f:
                        f.write(file_path.getbuffer())
                with st.spinner('Create vector DB'):
                    st.session_state["vectordb"] = chat.setup_vectordb(uploaded_path)
        if st.session_state["vectordb"] is not None:
            st.write(f"✅ {file_path.name} ")

    with instruction_container:
        query_input = st.text_area("Insert your instruction")
        uploaded_path = ""

        # Generate empty lists for generated and past.
        ## generated stores AI generated responses
        if 'answers' not in st.session_state:
            st.session_state['answers'] = []
        ## past stores User's questions
        if 'questions' not in st.session_state:
            st.session_state['questions'] = []

        if st.button("Submit", type="primary"):

            if file_path is not None:
                # work_path = os.path.abspath('.')
                # # save file
                # uploaded_path = os.path.join(work_path + "/tempDir/output", file_path.name)
                # with open(uploaded_path, mode="wb") as f:
                #     f.write(file_path.getvalue())
                # chat.setup_vectordb()

                ## generated stores langchain chain, to enable memory function of langchain in streamlit
                if ("QA_chain" not in st.session_state) or (st.session_state["vectorreloadflag"] == True):
                    if aa_combine_type == "stuff":
                        qa_chain = chat.chat_QA(st.session_state["vectordb"])
                    else:
                        qa_chain = chat.chat_QA_map_reduce(st.session_state["vectordb"])
                    st.session_state["QA_chain"] = qa_chain
                    st.session_state["vectorreloadflag"] = False

                # Query the agent.
                with st.spinner('preparing answer'):
                    response = st.session_state["QA_chain"]({"question": query_input})
                resp = response["answer"]
                st.session_state.questions.append(query_input)
                st.session_state.answers.append(resp)

    with response_container:
        if st.session_state['answers']:
            n = len(st.session_state['answers'])
            for i in range(n):
                st.markdown('-----------------')
                st.markdown('### ' + str(n-i-1) + '. ' + st.session_state['questions'][n-i-1])
                st.markdown(st.session_state["answers"][n-i-1])


if __name__ == "__main__":
    main()