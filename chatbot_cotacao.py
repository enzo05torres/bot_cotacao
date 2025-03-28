# -*- coding: utf-8 -*-
import os
import requests
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, filters

bot_telegram = os.getenv("bot_telegram")

nest_asyncio.apply()

# Dicionário para armazenar os dados do usuário (moeda de origem e destino)
user_data = {}

# Função para obter a taxa de conversão
async def obter_taxa(moeda_origem: str, moeda_destino: str):
    url = f"https://economia.awesomeapi.com.br/json/last/{moeda_origem}-{moeda_destino}"
    response = requests.get(url)
    dados = response.json()

    if f"{moeda_origem}{moeda_destino}" in dados:
        return float(dados[f"{moeda_origem}{moeda_destino}"]["bid"])
    else:
        return None

# Comando /start para iniciar a conversão
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Real (BRL)", callback_data='origem-BRL')],
        [InlineKeyboardButton("Dólar (USD)", callback_data='origem-USD')],
        [InlineKeyboardButton("Euro (EUR)", callback_data='origem-EUR')],
        [InlineKeyboardButton("Libra (GBP)", callback_data='origem-GBP')],
        [InlineKeyboardButton("Iene (JPY)", callback_data='origem-JPY')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Selecione a moeda de ORIGEM:", reply_markup=reply_markup)

# Escolher moeda de origem
async def escolher_moeda_origem(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    moeda_origem = query.data.split("-")[1]
    user_data[query.from_user.id] = {"origem": moeda_origem}

    keyboard = [
        [InlineKeyboardButton("Real (BRL)", callback_data='destino-BRL')],
        [InlineKeyboardButton("Dólar (USD)", callback_data='destino-USD')],
        [InlineKeyboardButton("Euro (EUR)", callback_data='destino-EUR')],
        [InlineKeyboardButton("Libra (GBP)", callback_data='destino-GBP')],
        [InlineKeyboardButton("Iene (JPY)", callback_data='destino-JPY')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text(f"Moeda de origem: {moeda_origem}\nAgora, escolha a moeda de DESTINO:", reply_markup=reply_markup)

# Escolher moeda de destino
async def escolher_moeda_destino(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    moeda_destino = query.data.split("-")[1]
    user_id = query.from_user.id

    if user_id in user_data and "origem" in user_data[user_id]:
        user_data[user_id]["destino"] = moeda_destino
        await query.answer()
        await query.edit_message_text(f"Moeda de destino: {moeda_destino}\nAgora, envie o valor que deseja converter.")
    else:
        await query.answer("Erro: Selecione a moeda de origem primeiro usando /start.")

# Receber valor e converter
async def receber_valor(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_data or "destino" not in user_data[user_id]:
        await update.message.reply_text("Erro: Selecione as moedas primeiro usando /start.")
        return

    moeda_origem = user_data[user_id]["origem"]
    moeda_destino = user_data[user_id]["destino"]
    taxa = await obter_taxa(moeda_origem, moeda_destino)

    try:
        valor_origem = float(update.message.text)
        valor_convertido = valor_origem * taxa
        resposta = f"{valor_origem:.2f} {moeda_origem} equivale a {valor_convertido:.2f} {moeda_destino}."
    except ValueError:
        resposta = "Erro: Insira um número válido."

    keyboard = [
        [InlineKeyboardButton("Nova conversão", callback_data='NOVA_CONVERSAO')],
        [InlineKeyboardButton("Encerrar", callback_data='ENCERRAR')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(resposta, reply_markup=reply_markup)

# Nova conversão
async def nova_conversao(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_data.pop(query.from_user.id, None)  # Limpa os dados armazenados

    keyboard = [
        [InlineKeyboardButton("Real (BRL)", callback_data='origem-BRL')],
        [InlineKeyboardButton("Dólar (USD)", callback_data='origem-USD')],
        [InlineKeyboardButton("Euro (EUR)", callback_data='origem-EUR')],
        [InlineKeyboardButton("Libra (GBP)", callback_data='origem-GBP')],
        [InlineKeyboardButton("Iene (JPY)", callback_data='origem-JPY')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    await query.edit_message_text("Selecione a moeda de ORIGEM:", reply_markup=reply_markup)

# Encerrar bot
async def encerrar(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Obrigado por usar o bot! Até a próxima.")

def main():
    TOKEN = bot_telegram
    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(escolher_moeda_origem, pattern='^origem-(BRL|USD|EUR|GBP|JPY)$'))
    app.add_handler(CallbackQueryHandler(escolher_moeda_destino, pattern='^destino-(BRL|USD|EUR|GBP|JPY)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receber_valor))
    app.add_handler(CallbackQueryHandler(nova_conversao, pattern='^NOVA_CONVERSAO$'))
    app.add_handler(CallbackQueryHandler(encerrar, pattern='^ENCERRAR$'))

    # Inicia o bot
    app.run_polling()

if __name__ == "__main__":
    main()
