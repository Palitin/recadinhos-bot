import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
from os import getenv
from functools import wraps

# formatação de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# para evitar todos os métodos de serem logados
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# decorador para restringir o acesso de comandos a usuários autorizados
USUARIOS_AUTORIZADOS = [1456515969]
CANAIS_CADASTRADOS = [-1002021874904, -4026266836]

# váriaveis da função replicar
MENSAGEM, ASSINATURA = range(2)
recado = {'titulo': "RECADO IMPORTANTE!",'conteudo': '', 'Assinatura': 'Att. a direção'}

def restricted(func):
    # função de restrição de comandos
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in USUARIOS_AUTORIZADOS:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠ Você não está autorizado.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# comandos do bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # resposta ao comando /start
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Olá! 👋")

async def registrar_canal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    id_canal = update.message.text.replace("/registrar_canal ", "")
    id_canal = int(id_canal)
    CANAIS_CADASTRADOS.append(id_canal)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Canal registrado!")

@restricted
async def escrever_recado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # inicia a conversa
    await update.message.reply_text("Escreva o seu recado no chat\n\n" "Envie /cancelar para cancelar esta ação\n" "⚠️ Atenção\! Você enviará recados para *todos* os canais registrados\! ⚠️", parse_mode= constants.ParseMode.MARKDOWN_V2)
    return MENSAGEM

async def assinatura(update: Update, context: ContextTypes.DEFAULT_TYPE, recado=recado):
    # guarda os valores da mensagem
    usuario = update.message.from_user
    logger.info(f"Mensagem de {usuario.first_name}: {update.message.text}")
    recado.update({'conteudo':update.message.text})

    await update.message.reply_text("Gostaria de assinar o recado?\n\n" "*SIM*: envie o seu nome\n" "*NÃO*: envie /pular para o reacado ser enviado em nome da direção do IFC câmpus Brusque", parse_mode= constants.ParseMode.MARKDOWN_V2)
    return ASSINATURA

async def skip(update: Update, context:ContextTypes.DEFAULT_TYPE, recado=recado):
    # comando de pular os dados de preenchimento da assinatura e envia o recado
    usuario = update.message.from_user
    logger.info(f"Assinatura de {usuario.first_name}: Att. a direção")

    await update.message.reply_text("Tudo feito! O recado será enviado logo logo :)")

    msg = f"{recado['titulo']}\n\n{recado['conteudo']}\n{recado['assinatura']}"
    for canal in CANAIS_CADASTRADOS:
        # envio do recado
        await context.bot.send_message(chat_id=canal, text=msg)
    return ConversationHandler.END

async def enviar_recado(update: Update, context: ContextTypes.DEFAULT_TYPE, recado=recado):
    # guarda os valores da assinatura e envia o recado
    usuario = update.message.from_user
    logger.info(f'Assinatura de {usuario.first_name}: {update.message.text}')
    recado.update({'assinatura':f'Att. {update.message.text}'})

    await update.message.reply_text("Tudo feito! O recado será enviado logo logo :)")

    msg = f"{recado['titulo']}\n\n{recado['conteudo']}\n{recado['assinatura']}"
    for canal in CANAIS_CADASTRADOS:
        # envio do recado
        await context.bot.send_message(chat_id=canal, text=msg)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # cancelamento do comando
    usuario = update.message.from_user
    logger.info(f"{usuario.first_name} cancelou o comando RECADO")

    await update.message.reply_text("Ação cancelada...")
    return ConversationHandler.END

# for canal in CANAIS_CADASTRADOS:
# await context.bot.send_message(chat_id=canal, text=msg)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # resposta ao receber um comando não identificado
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, não tenho um comando assim :(")

if __name__ == '__main__':
    application = ApplicationBuilder().token(getenv('TOKEN')).build()
    
    # criando comandos
    start_handler = CommandHandler('start', start)
    registar_canal_handler = CommandHandler('registrar_canal', registrar_canal)
    recado_handler = ConversationHandler(
        entry_points = [CommandHandler('escrever_recado', escrever_recado)],
        states= {
            MENSAGEM: [MessageHandler(filters.TEXT, assinatura)],
            ASSINATURA: [MessageHandler(filters.TEXT, enviar_recado), CommandHandler("pular", skip)]
        },
        fallbacks = [CommandHandler("cancelar", cancel)]
    )
    no_command_handler = MessageHandler(filters.COMMAND, unknown)

    # add comandos ao app
    application.add_handler(start_handler)
    application.add_handler(registar_canal_handler)
    application.add_handler(recado_handler)
    application.add_handler(no_command_handler)
    
    application.run_polling()