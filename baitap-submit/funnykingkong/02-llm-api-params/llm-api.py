from openai import OpenAI
import os
from bs4 import BeautifulSoup
import requests
from datetime import datetime

class MyAssistant:
    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_WORD_LIMIT = 5000 # GPT-4o-mini max token 16,384
    MAX_MEMORIZED_MESSAGES = 10

    """
    self.messages: store the conversation history
    """
    def __init__(self):
        self.client = OpenAI(
            base_url="https://api.openai.com/v1",
            api_key=os.getenv('OPENAI_API_KEY'),
        )
        self.messages = []
    
    def chat_and_response(self, message, is_stream=False):
        # convert to a API message
        request_message ={
                            "role": "user",
                            "content": message,
                        }
        
        # store to conversation history
        if len(self.messages) >= self.MAX_MEMORIZED_MESSAGES:
            self.messages.pop(0)
        self.messages.append(request_message)
        
        #call api
        stream = self.client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=self.messages,
            stream=is_stream
        )
        msg = ""

        # get response and show to console
        print("Assistant: ")
        for chunk in stream:
            msg += chunk.choices[0].delta.content or ""
            print(chunk.choices[0].delta.content or "", end="")
        print("\n")
        #convert to API message
        response_message = {
                            "role": "assistant",
                            "content": msg,
                            } 
        # store to conversation history
        self.messages.append(response_message)

        # print to debug
        # print(f"\n\n{self.messages}")

    # parse website content
    def parse_from_url(self, url):
        content = ""
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            content_div = soup.find('div', id='main-detail') #Bạn có thể hardcode lấy thông tin từ div có id là main-detail
            if content_div:
                content = content_div.get_text(strip=True)
        else:
            print("Failed to read the website. Please check the URL and try again.")
        return content

    def summary(self, content, is_stream=False):
        # convert to a API message
        request_message ={
                            "role": "user",
                            "content": f"Hãy tóm tắt nội dung trong vòng 10 câu trở lại, với từ ngữ đơn giản mà trẻ em 6 tuổi cũng có thể hiểu. {content}" ,
                        }
        
        #call api
        stream = self.client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=[request_message],
            stream=is_stream
        )
        
        print("Assistant: ")
        for chunk in stream:
            print(chunk.choices[0].delta.content or "", end="")
        print("\n")
    
    def split_content(self, content, max_tokens=MAX_WORD_LIMIT):
        # Split content into paragraphs
        paragraphs = content.split('\n')
        parts = []
        
        for paragraph in paragraphs:
            words = paragraph.split()
            current_part = []
            current_length = 0
            
            for word in words:
                current_length += len(word) + 1  # +1 for the space
                if current_length > max_tokens:
                    parts.append(' '.join(current_part))
                    current_part = [word]
                    current_length = len(word) + 1
                else:
                    current_part.append(word)
            
            if current_part:
                parts.append(' '.join(current_part))
        
        return parts

    def translate(self, content, is_stream=False):
        parts = self.split_content(content)
        translated_content = ""
        for part in parts:
            if part.strip() == "":
                continue
            # convert to a API message
            request_message ={
                                "role": "user",
                                "content": f"Dịch sang tiếng Anh nội dung sau, dùng từ ngữ đơn giản thôi nha, tui mới học tiếng Anh hà.: {part}" ,
                            }
            
            #call api
            stream = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[request_message],
                stream=is_stream
            )
            
            print("Assistant: ")
            for chunk in stream:
                translated_content += chunk.choices[0].delta.content or ""
                print(chunk.choices[0].delta.content or "", end="")
            print("\n")
            
        user_input = input("########Do you want to save to file? Y/N ############\n")
        if user_input.lower() in ["yes", "y"]:
            filename = f"translated_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "a", encoding="utf-8") as file:
                file.write(translated_content + "\n")

    
    def extract_code_block(self, response):
        # Extract the code block from the response
        code_lines = []
        in_code_block = False
        for line in response.split('\n'):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                code_lines.append(line)
        return '\n'.join(code_lines)
    
    def coding_guide(self, content):
        # convert to a API message
        request_message ={
                            "role": "user",
                            "content": f"Write code in Python to solve the following problem: {content}. Just the code, no explanation or sample result needed." ,
                        }
        
        #call api
        chat_commpletion = self.client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=[request_message],
        )
        res = chat_commpletion.choices[0].message.content
        print(res)
        # Extract the code block from the response
        code_block = self.extract_code_block(res)

        filename = f"solution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        problem_txt = f"""# Problem: {content}"""
        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"{problem_txt}\n\n{code_block}")
        print("Assistant: check the file solution_YYYYMMDD_HHMMSS.py")
        

if __name__ == "__main__":
    assistant = MyAssistant()
    
    user_input = input("What can I help you?: 1.Chat 2.Website summary 3.Translate 4.Coding guide \n")

    # bài tập 1,2
    if user_input == "1":
        print("Welcome to my chat assistant. Have fun! \n")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["bye", "quit"]:
                break

            assistant.chat_and_response(user_input, is_stream=True)
    
    # bài tập 3
    elif user_input == "2":
        print("Welcome to my website summary assistant. Only support news on tuoitre.vn: \n")
        while True:
            content = ""
            user_input = input("Website: ")
            if user_input.lower() in ["bye", "quit"]:
                break
            
            content = assistant.parse_from_url(user_input)
            assistant.summary(content, is_stream=True)
    # bài tập 4
    elif user_input == "3":
        print("Welcome to my Website translation assistant. Only support news on tuoitre.vn: \n")
        while True:
            content = ""
            user_input = input("Website: ")
            if user_input.lower() in ["bye", "quit"]:
                break
            
            content = assistant.parse_from_url(user_input)
            assistant.translate(content, is_stream=True)
    # bài tập 5
    elif user_input == "4":
        print("Welcome to my coding guide assistant. Enter your problem, you will get a coding file to solve it!\n")
        while True:
            user_input = input("Problem: ")
            if user_input.lower() in ["bye", "quit"]:
                break
            
            assistant.coding_guide(user_input)
    else:
        print("Invalid choice. Please restart and choose from 1 to 4.")
        exit()

    
        