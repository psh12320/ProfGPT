from telegram.ext import MessageHandler, CommandHandler, filters, ConversationHandler, ApplicationBuilder, ContextTypes, CallbackQueryHandler, CallbackContext
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import os
import openai

os.environ['OPENAI'] = 'YOUR_API_KEY'
openai.api_key = os.getenv("OPENAI")
TOKEN = YOUR_TOKEN"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
SYSTEM_BEHAVIOUR, QUESTION, FOLLOWUP, ENDCONVO = range(4)
messages = []
sample_dict = {"role": "",
               "content": ""}


async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Provide ProfGPT with the context of your question to set its behaviour.")
    # global messages
    # print("START CHAT Current Status of messages is:", messages)
    return SYSTEM_BEHAVIOUR


async def handle_sys_behaviour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    system_behaviour = update.message.text
    global messages
    global sample_dict
    system_dict = sample_dict
    system_dict['role'] = 'system'
    system_dict['content'] = system_behaviour
    messages += [system_dict]
    print("HANDLE SYS BEHAVIOUR Current Status of messages is:", messages)
    await update.message.reply_text("What is your question?")
    return QUESTION, messages


async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE, messages_list):
    query = update.callback_query
    question_content = update.message.text
    global sample_dict
    user_dict = sample_dict
    user_dict['role'] = 'user'
    user_dict['content'] = question_content
    messages_list += [user_dict]
    print("Current Status of messages is:", messages_list)
    response = get_response_api(messages_list)
    await update.message.reply_text(response['choices'][0]['message']['content'])
    keyboard = [
        InlineKeyboardButton("Follow-up with a question.", callback_data=str(FOLLOWUP)),
        InlineKeyboardButton("End Conversation.", callback_data=str(ENDCONVO))
    ]
    reply_markup = InlineKeyboardMarkup([keyboard])
    await query.message.reply_text("Pick a choice.", reply_markup=reply_markup)
    return messages_list


async def cancel(update: Update, context: CallbackContext):
    user = update.effective_user
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Conversation has been cancelled. Goodbye, {user.first_name}!",
    )

    return ConversationHandler.END


def get_response_api(messages_list):
    api_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages_list,
        temperature=1,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return api_response


def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    choice = int(query.data)

    if choice == FOLLOWUP:
        # User chose Follow-Up
        return QUESTION
    else:
        # Invalid choice, handle accordingly
        return ConversationHandler.END


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_chat)],
        states={
            SYSTEM_BEHAVIOUR: [MessageHandler(filters.TEXT, handle_sys_behaviour)],
            QUESTION: [MessageHandler(filters.TEXT, handle_question)],
            FOLLOWUP: [CallbackQueryHandler(handle_question)],
            ENDCONVO: [CallbackQueryHandler(cancel)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_callback))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

