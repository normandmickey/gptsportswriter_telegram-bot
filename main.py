import os
from telegram.ext import Application, MessageHandler, filters
from dotenv import load_dotenv
from openai import OpenAI
from asknews_sdk import AskNewsSDK
from groq import Groq

load_dotenv()
TELEGRAM_API_TOKEN=os.getenv("TELEGRAM_API_TOKEN")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
ASKNEWS_CLIENT_ID=os.getenv("ASKNEWS_CLIENT_ID")
ASKNEWS_CLIENT_SECRET=os.getenv("ASKNEWS_CLIENT_SECRET")
GROQ_GPT_MODEL = "llama-3.3-70b-versatile"
OPENAI_GPT_MODEL = "gpt-4o"

openai_client = OpenAI()

groq_client = Groq(
    api_key=os.environ.get(GROQ_API_KEY),
)

ask = AskNewsSDK(
        client_id=ASKNEWS_CLIENT_ID,
        client_secret=ASKNEWS_CLIENT_SECRET,
        scopes=["news"]
)

async def chat_completion(game):
    completion = openai_client.chat.completions.create(
        model="gpt-4o-search-preview",
        web_search_options={
            "user_location": {
                "type": "approximate",
                "approximate": {
                    "country": "US",
                    "city": "New York",
                    "region": "New York",
                }
            },
        },
        messages=[
            {
                "role": "user",
                "content": game,
            }
        ],
    )

    return completion.choices[0].message.content

async def chat_completion_request(messages):
    #print(messages)
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_GPT_MODEL,
            messages=messages,
            max_tokens=500
        )
        #print("Groq: " + str(response))
        return response.choices[0].message.content
    except:
        #print("Unable to generate ChatCompletion response")
        #print(f"Exception: {e}")
        response = openai_client.chat.completions.create(
           model=OPENAI_GPT_MODEL,
           messages=messages,
           max_tokens=500,
           temperature=0.3
        )
        #print("OpenAI: " + str(response))
        return response.choices[0].message.content
        
async def reply(update, context):
    context = ""
    match = update.message.text
    messages = []
    messages.append({"role": "system", "content": "You are the worlds best AI Sports Handicapper and sportswriter. You are smart, funny and accurate."})
    messages.append({"role": "user", "content": match})
    try:
      #newsArticles = ask.news.search_news("best prop bets for the text " + match, method='kw', return_type='dicts', n_articles=3, categories=["Sports"], premium=True, start_timestamp=int(start), end_timestamp=int(end)).as_dicts
      newsArticles = ask.news.search_news("best bet for the following matchup " + match, method='kw', return_type='dicts', n_articles=3, categories=["Sports"], premium=True).as_dicts
      context = ""
      for article in newsArticles:
        context += article.summary
      #print(context)
    except:
      context = ""
    messages.append({"role": "user", "content": "Write a short article outlining following matchup. List the odds and probability.  Give your best bet based on the context provided only mention bets and odds that are referenced in the context. " + context + " " + match})
    reply = await chat_completion_request(messages)
    await update.message.reply_text(reply)

def main():
    """
    Handles the initial launch of the program (entry point).
    """
    token = TELEGRAM_API_TOKEN
    application = Application.builder().token(token).concurrent_updates(True).read_timeout(30).write_timeout(30).build()
    application.add_handler(MessageHandler(filters.TEXT, reply)) # new text handler here
    print("Telegram Bot started!", flush=True)
    application.run_polling()


if __name__ == '__main__':
    main()