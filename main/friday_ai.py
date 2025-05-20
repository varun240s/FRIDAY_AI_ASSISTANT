from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage , AIMessage, FunctionMessage
from dotenv import load_dotenv
import os
import speech_recognition as sr
import pyttsx3
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory 
from langchain_core.output_parsers import StrOutputParser
import subprocess
import webbrowser
# from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
# from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()
engine = pyttsx3.init()
recognizer = sr.Recognizer()

# new
tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily = TavilySearchResults()

chat = ChatGroq(
    groq_api_key = os.getenv("GROQ_API_KEY"),
    model_name = "gemma2-9b-it"
)
# new
tools = [tavily]

conversation_history = {}


def set_history(session_id : str) -> BaseChatMessageHistory:
    if session_id not in conversation_history:
        conversation_history[session_id] = ChatMessageHistory()
        conversation_history[session_id].add_message(SystemMessage(content="you are Maya, a virtual intelligent ai assistant. When asked 'who are you', say 'I am Maya, a virtual intelligent ai assistant, I am ready to help you with your multiple tasks.'"))
    return conversation_history[session_id]
history = RunnableWithMessageHistory(
    runnable=chat,
    set_history=set_history,
    get_session_history=set_history,
    session_id="chat1"
)

config = {"configurable": {"session_id" : "chat1"}}  


def transcribe_audio():
    with sr.Microphone() as source:
        
        recognizer.adjust_for_ambient_noise(source)
        input_audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(input_audio)
        return text
    except sr.UnknownValueError:
        print("Could not understand the input_audio...")
        return ""
    except sr.RequestError:
        print("could not request the results .. please check the internet connection.")
        return ""

    
def speak(text):
    print("Assistant: "+ text)
    engine.say(text)
    engine.runAndWait()
    
# system commands ...
def execute_system_commands(command: str)-> bool:
    # so for now str is set to be False , but if command is not str and a system coomand then it will be True.
    command = command.lower()
    
    if "open youtube" in command:
        webbrowser.open("https://www.youtube.com/")
        speak("Opening youtube...")
        
    elif "open google" in command or "open google chrome" in command:
        try:
            if os.name == "nt":
                subprocess.Popen("C:\Program Files\Google\Chrome\Application\chrome.exe")
            else:
                subprocess.Popen(["google-chrome"])
            speak("Opening google chrome...")
        except Exception as e:
            print("Error in opening Google Chrome...")
        return True
    
    elif "play" in command and "youtube" in command:
        query = command.replace("play", "").replace("youtube", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        speak(f"playing {query} on youtube.")
        return True
    
    elif "open calculater" in command:
        if os.name == 'nt':
            subprocess.Popen("calc.exe")
        else:
            subprocess.Popen("open","-a", "Calculator")

        speak("Opening Calc...")
        return True
    
    # elif "open brave" in command:
    #     if os.name == 'nt':
    #         # subprocess.Popen("C:\Windows.old\Users\reddy\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe")
    #        
    #     else:
    #         subprocess.Popen("open" , "-a","Brave")
            
    elif "open whatsapp" in command.lower():
        try:
            if os.name == 'nt':  # Windows
                # Method 1: Direct .exe path (best)
                whatsapp_path = os.path.expanduser("~\\AppData\\Local\\WhatsApp\\WhatsApp.exe")
                if os.path.exists(whatsapp_path):
                    subprocess.Popen([whatsapp_path])  # Pass as list
                else:
                    # Method 2: Fallback to shortcut (requires shell=True)
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", r"C:\Users\reddy\Desktop\WhatsApp - Shortcut.lnk"],
                        shell=True
                    )
            else:  # macOS/Linux
                subprocess.Popen(["open", "-a", "WhatsApp"])  # macOS
            speak("Opening WhatsApp...")
        except Exception as e:
            print(f"Error: {e}")
            speak("Failed to open WhatsApp. Opening web version.")
            webbrowser.open("https://web.whatsapp.com")
        return True
        
    elif "open unigram" in command.lower() or "open telegram" in command.lower():
        try:
            if os.name == 'nt':  # Windows
                
                # method1..
                unigram_path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\WindowsApps\\Unigram.Native_8v5t7v6zq6q10!App")
                if os.path.exists(unigram_path):
                    subprocess.Popen([unigram_path])
                else:
                    subprocess.Popen(
                        ["cmd", "/c", "start", "", r"C:\Users\reddy\Desktop\Unigram - Shortcut.lnk"],
                        shell=True
                    )
                    
            else:  # macOS/Linux
                subprocess.Popen(["telegram"])  # Linux (if installed via Snap/Flatpak)
            speak("Opening Telegram...")
        except Exception as e:
            print(f"Error: {e}")
            speak("Failed to open Unigram. Opening Telegram Web.")
            webbrowser.open("https://web.telegram.org")
        return True
        
    return False






def chat_with_groq(config):
    # when the llm will not be able to answer the user query, it will use the tools to search for the answer in the internet.
    
    llm_with_tools = chat.bind_tools(tools)
    session_id = config["configurable"]["session_id"]
    initial_text = "Hello sir, I am Maya, I am here to help you..."
    speak(initial_text)
    
    while True:
        user_text = transcribe_audio()
        if not user_text:
            continue
        # if user_text.lower() in ["exit", "quit", "stop"]:
        if user_text.lower() == "exit":
            print("Exiting...")
            speak("Goodbye!...")
            break
        
        if execute_system_commands(user_text):
            continue # Skip the ai process
        
        try:
            # removing history and adding the new tools
            response = llm_with_tools.invoke(
                [HumanMessage(content=user_text)],
                config={"configurable": {"session_id": session_id}}
            )
            
             # Check if the LLM wants to use tools
            if hasattr(response, "tool_calls") and response.tool_calls:
                speak("Let me search for that...")
                results = []
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_input = tool_call["args"]
                    if tool_name == "tavily_search":
                        results.append(tools["tavily_search"].run(tool_input))
                
                # Send tool results back to the LLM for a final answer
                final_response = history.invoke(
                    [
                        HumanMessage(content=user_text),
                        AIMessage(content=str(response)),
                        FunctionMessage(content=str(results), name="tavily_search")
                    ],
                    config={"configurable": {"session_id": session_id}}
                )
                speak(final_response.content)
            else:
                # No tools needed, reply directly
                speak(response.content)
                
        except Exception as e:
            print(f"Error: {e}")
            speak("Sorry, I encountered an issue. Please try again.")

if __name__ == "__main__":
    chat_with_groq(config)