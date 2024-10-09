from urllib.parse import urljoin
import gradio as gr
import requests
import json
import time
import os
from langchain_community.document_loaders import WebBaseLoader
import re
#from langchain import HuggingFaceHub
from langchain_community.llms import HuggingFaceHub
from ldap3 import Server, Connection, ALL, NTLM

llm = HuggingFaceHub(huggingfacehub_api_token="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", repo_id="HuggingFaceH4/zephyr-7b-beta", model_kwargs={"temperature":0.6, "max_new_tokens":500})

os.environ['http_proxy'] = 'http://proxy-dmz.intel.com:912'
os.environ['HTTP_PROXY'] = 'http://proxy-dmz.intel.com:912'
os.environ['https_proxy'] = 'http://proxy-dmz.intel.com:912'
os.environ['HTTPS_PROXY'] = 'http://proxy-dmz.intel.com:912'
os.environ['NO_PROXY']='127.0.0.1,localhost,intel.com'


from tinydb import TinyDB, Query
db = TinyDB('./db.json')

EXTERNAL_URL="https://serving.mlops.intel.com/seldon/byashwan/backendv0/"
url = urljoin(EXTERNAL_URL, "api/v1.0//predictions")
TOKEN= os.environ['AUTH']
#TOKEN='hi'
bearer_token = f"Bearer {TOKEN}"
headers = {
    "Content-Type": "application/json",
    "Authorization": bearer_token
}
def llm_clone(input_q, history):
    history = history or []
    s = list(sum(history, ()))
    s.append(input_q)
    data_json = {'data': {"ndarray": [] }}
    data_json['data']['ndarray']=[input_q] 
    print(data_json)
    output = requests.post(url,json.dumps(data_json),headers = headers,timeout=120)
    data = output.json()
    history.append((input_q, data['jsonData']['Answer']))
    db.insert({'Question': input_q, 'Answer':data['jsonData']['Answer'] })
    return history, history

def helper(input):
    User = Query()
    result = db.search(User.case == int(input))
    return result[0]['summary']

def helper2(input):
    loader = WebBaseLoader(input)
    data = loader.load()
    result=data[0].page_content
    res=result.replace("\n\n", " ")
    res_list= res.split('Report Inappropriate Content ')
    data={}
    for i,item in enumerate(res_list):
        if i==0:
            print(item.split('- Intel Community')[0])
            data['title']=item.split('- Intel Community')[0].strip()
            continue
        if i==1:
            data['question']=re.sub('[\t\n\xa0]+', '',item.split('Kudos')[0])[:-2].strip()
            continue
        else:
            if 'discussion' in data:
                d=re.sub('[\t\n\xa0]+', '',item.split('Kudos')[0])[:-2]
                data['discussion'].append(d.strip())
            else:
                d=re.sub('[\t\n\xa0]+', '',item.split('Kudos')[0])[:-2]
                data['discussion']=[d.strip()]
    template = """You are an experienced developer familiar with handling FPGA customer issues.
    The following text was parsed from a Database of customer issues and its comments to solve the issue.
    Summarize the following information from the text provided:
    
    - Issue: A list with the following items: title, labels, and status (whether the issue is still open or closed).
    - Summary: A summary of the issue in precisely one short sentence of no more than 50 words.
    - Details: A longer summary of the issue. If code has been provided, list the pieces of code
      that cause the issue in the summary.
    - Rootcause: A short description identifying the underlying problem that led to the customer issue
    
    Don't waste words. Use short, clear, complete sentences. Use active voice. Maximize detail, meaning focus on the content. Say Thank you at the end.
    {text}
    ###Response
    """
    template=template.format(text=data)
    result = llm(template)
    print(result)
    response = re.findall('###Response(.*)',result,flags=re.S)
    return response[0]
    
def helper3(info):
    template = """You are an experienced FPGA Grammar assistant who takes in the product description and rewrite it into an easy step by step customer user guide.

    ###Text
    The interface complies with the Avalon Streaming Interface specification, and adds the additional side condition that data valid must be held high from the start to the end of a packet, and must be low outside of a packet
    Packets always start on the leftmost byte of i_tx_data (they are SOP aligned)
    The core has a parameter called ready_latency that is set through the GUI (Ready Latency)
    When o_tx_ready is deasserted, i_tx_data must be paused for as many cycles as o_tx_ready is deasserted, starting exactly ready_latency cycles later
    For example, in the timing diagram above, ready_latency is 1, so the cycle after o_tx_ready is deasserted for 1 cycle, i_tx_data is paused for 1 cycle
    When the frame ends, i_tx_empty is set to the number of unused bytes in i_tx_data, starting from the right (byte 0)
    In this example, i_tx_data on the last cycle of the packet has 3 empty bytes The minumum number of bytes on the last cycle is 1
    
    ###Response
    Return the step by step user guide
    Hold i_tx_valid high from the start to end of a packet, and must be low outside
    of a packet.
    • Drive i_tx_startofpacket high on the first clock cycle of the frame transfer.
    Always start the packet on the MSB of the byte of i_tx_data, ensuring SOP
    aligned.
    • Hold the value on i_tx_data when o_tx_ready is deasserted. In this example,
    the Ready latency is configured to 1, therefore hold i_tx_data for 1 cycle after
    o_tx_ready is deasserted.
    • Drive i_tx_empty with the number of unused bytes in i_tx_data bus in the last
    clock cycle, coincident with i_tx_endofpacket, starting from the LSB (byte 0).
    — In this example, i_tx_data on the last cycle of the packet has 3 empty
    bytes.
    — The minimum number of valid bytes on the last cycle is 1.

    You are an experienced FPGA Grammar assistant who takes in the product description and rewrite it into an easy step by step customer user guide.

    ###Text
    {text}

    ###Response
    Return the step by step user guide 
    """
    template=template.format(text=info)
    result = llm(template)
    result = result.split('step by step user guide ')
    return result[-1]



def user(user_message, history):
        return "", history + [[user_message, None]]

def bot(history):
    input_q= history[-1][0]
    data_json = {'data': {"ndarray": [] }}
    data_json['data']['ndarray']=[input_q] 
    output = requests.post(url,json.dumps(data_json),headers=headers,timeout=120,verify=False)
    data = output.json()
    bot_message = data['jsonData']['Answer']
    history[-1][1] = ""
    for character in bot_message:
        history[-1][1] += character
        time.sleep(0.05)
        yield history


def vote(chatbot, data: gr.LikeData):
    if data.liked:
        return chatbot+[(None,"Thanks for your feedback!")]
    else:
        return chatbot+[(None,"Can you [write us](https://outlook.office.com/?path=/mail/action/compose&to=b.yashwanth.reddy@intel.com&subject=Altera_Chatbot_Feeback&body=body) on What was wrong with the response and How could it be improved? ")]
    


with gr.Blocks() as demo:
    ''''gr.Markdown("""<h1><center>PSG Chatbot</center></h1>
                <p>I am an Open Source Large Language Model (Zephyr) powered chatbot currently trained on Agilex 7 documents. 
                Ask me any technical questions in the Agilex 7 space and I'll try my best to give you an answer. However, do note that I am a work in progress and I can make mistakes in my responses. 
                Please verify my answers before using.</p>""")'''
    with gr.Tab("Chatbot"):
        chatbot = gr.Chatbot(value=[(None, "Welcome 👋. I'm Altera AI Chatbot trained on Agilex-7 and Agilex-5 Documents")],)
        state = gr.State()
        message = gr.Textbox(
                interactive=True,
                scale=4,
                show_label=False,
                placeholder="Enter your message",
                container=False,)
        submit = gr.Button("SEND")
        gr.Examples(["What is Platform Designer and how can I launch it?","What is NoC and how can I constrain it?","Generate the top 3 FAQs for Intel Agilex 7 SEU Mitigation"],inputs=message)
        #submit.click(llm_clone, inputs=[message, state], outputs=[chatbot, state])
        #message.submit(llm_clone, inputs=[message, state], outputs=[chatbot, state])
        submit.click(user, [message, chatbot], [message, chatbot], queue=False).then(
            bot, chatbot, chatbot)
        message.submit(user, [message, chatbot], [message, chatbot], queue=False).then(
            bot, chatbot, chatbot)
        chatbot.like(vote, [chatbot], [chatbot])
    
    with gr.Tab("IPS Summarization"):
        gr.Markdown("""Enter the ID of IPS Database
        """)
        with gr.Row() as row:
            with gr.Column():
                #query = gr.Textbox(label="Input your IPS ID")
                query=gr.Dropdown([342416,403819,433197,434896,441240,443153,443608,444764,447435,450824,451544,455509,461258,472373,473621,475797,483363,483612,486450,489486,489488,489494,489763,489955,491183,491284,491376,491926,492647,494044,497145,502702,504679,506234,508740,508779,511375,511594,518011,522841,523254,529049,531681,532461,535593,535834,537403,538320,540520,541390,541899,542408,542902,544213,544832,545927,547778,549451,550273,550357,550641,551186,551325,552745,553403,553751,554112,555531,557101,557706,557795,558776,559105,559111,573616,576529,577448,577693,581204,581771,583885,584290,584584,584746,585428,585506,586889,586890,586930,587231,587243,587996,588041,590351,591004,591179,591767,592347,592549,592622], label="Select from below IPS ID", info="Will add more IPS cases later!")
                search_btn = gr.Button("Search")
		        #search_btn.click(helper,inputs=[query],outputs=[wiki_title_box])
            with gr.Column():
                wiki_title_box = gr.Textbox(label="Summary")
            search_btn.click(helper,inputs=[query],outputs=[wiki_title_box])

    with gr.Tab("Forum Summarization"):
        gr.Markdown("""Enter the URL of Forum
        """)
        with gr.Row() as row:
            with gr.Column():
                query_forum = gr.Textbox("https://community.intel.com/t5/Programmable-Devices/Not-able-to-generate-hps-iws-handoff-folder/td-p/1598240",label="url here (example url below)")
                #query=gr.Dropdown( label="Select from below IPS ID", info="Will add more IPS cases later!")
                search_btn2 = gr.Button("Search")
		        #search_btn.click(helper,inputs=[query],outputs=[wiki_title_box])
            with gr.Column():
                forum_box = gr.Textbox(label="Summary")
            search_btn2.click(helper2,inputs=[query_forum],outputs=[forum_box])

    with gr.Tab("Writing assistant"):
        gr.Markdown("""Type the text below to enhance it using AI
        """)
        with gr.Row() as row:
            with gr.Column():
                query_forum3 = gr.Textbox(label="Type the text here")
                #query=gr.Dropdown( label="Select from below IPS ID", info="Will add more IPS cases later!")
                search_btn3 = gr.Button("Generate User Guide")
		        #search_btn.click(helper,inputs=[query],outputs=[wiki_title_box])
            with gr.Column():
                forum_box3 = gr.Textbox(label="Suggested text")
            search_btn3.click(helper3,inputs=[query_forum3],outputs=[forum_box3])
            #search_btn4.click(helper4,inputs=[query_forum3],outputs=[forum_box3])


def same_auth(username, password):
    server_address = 'ldaps://ldap-sc.altera.com:3269' # Intel is ldaps://corpldap.intel.com:3269
    user_samaccountname = 'altera\\byashwan' # Example in Intel is gar\idsid
    user_password = 'Shreyas@123456789' # idsid password
    server = Server(server_address, get_info=ALL, use_ssl=True)
    # # Create the Connection object
    conn = Connection(server,user=user_samaccountname,password=user_password,authentication=NTLM)
    # # Attempt to bind/authenticate to the server
    if not conn.bind():
        print('error in bind', conn.result)
        return True
    else:
        print('successfully bound to server')
        return False

if __name__ == "__main__":
    demo.queue()
    demo.launch(auth=same_auth,server_name="0.0.0.0", server_port=8080,debug = True)
# demo.queue()
# demo.startup_events()
#app = gr.mount_gradio_app(app, demo, f'/gradio')