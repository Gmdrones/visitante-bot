from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import sqlite3

# Conexão com o banco de dados
conn = sqlite3.connect("visitantes.db", check_same_thread=False)
cursor = conn.cursor()

# Criação da tabela se não existir
cursor.execute("""
CREATE TABLE IF NOT EXISTS visitantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cpf TEXT,
    identidade TEXT,
    placa TEXT,
    bloco TEXT,
    apartamento TEXT,
    morador TEXT,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Estado dos usuários
user_state = {}

# Teclado principal
menu_principal = ReplyKeyboardMarkup(
    [["Novo Cadastro", "Buscar Visitante"]],
    resize_keyboard=True
)

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_chat.id] = {'step': 'menu'}
    await update.message.reply_text("Escolha uma opção:", reply_markup=menu_principal)

# Comando /buscar
async def buscar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_state[chat_id] = {'step': 'buscar'}
    await update.message.reply_text("Digite o nome, CPF ou identidade para buscar. Ex: João")

# Lógica principal do bot
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    state = user_state.get(chat_id, {'step': 'menu'})

    if state['step'] == 'menu':
        if text == "Novo Cadastro":
            user_state[chat_id] = {'step': 'nome'}
            await update.message.reply_text("Qual o nome do visitante?")
        elif text == "Buscar Visitante":
            user_state[chat_id] = {'step': 'buscar'}
            await update.message.reply_text("Digite o nome, CPF ou identidade para buscar. Ex: João")
        else:
            await update.message.reply_text("Escolha uma opção válida.", reply_markup=menu_principal)

    elif state['step'] == 'buscar':
        termo = text
        cursor.execute("""
            SELECT * FROM visitantes
            WHERE nome LIKE ? OR cpf LIKE ? OR identidade LIKE ?
            ORDER BY data_hora DESC LIMIT 1
        """, (f"%{termo}%", f"%{termo}%", f"%{termo}%"))
        resultado = cursor.fetchone()
        if resultado:
            resposta = f"""👤 Última visita encontrada:
Nome: {resultado[1]}
CPF: {resultado[2]}
Identidade: {resultado[3]}
Placa: {resultado[4]}
Bloco: {resultado[5]}
Apartamento: {resultado[6]}
Morador: {resultado[7]}
Data/Hora: {resultado[8]}"""
        else:
            resposta = "❌ Nenhum visitante encontrado com esse dado."
        user_state[chat_id] = {'step': 'menu'}
        await update.message.reply_text(resposta, reply_markup=menu_principal)

    elif state['step'] == 'nome':
        state['nome'] = text
        state['step'] = 'cpf'
        await update.message.reply_text("CPF?")
    elif state['step'] == 'cpf':
        state['cpf'] = text
        state['step'] = 'identidade'
        await update.message.reply_text("Identidade?")
    elif state['step'] == 'identidade':
        state['identidade'] = text
        state['step'] = 'placa'
        await update.message.reply_text("Placa do veículo?")
    elif state['step'] == 'placa':
        state['placa'] = text
        state['step'] = 'bloco'
        await update.message.reply_text("Bloco?")
    elif state['step'] == 'bloco':
        state['bloco'] = text
        state['step'] = 'apartamento'
        await update.message.reply_text("Apartamento?")
    elif state['step'] == 'apartamento':
        state['apartamento'] = text
        state['step'] = 'morador'
        await update.message.reply_text("Nome do morador?")
    elif state['step'] == 'morador':
        state['morador'] = text
        cursor.execute("""
            INSERT INTO visitantes (nome, cpf, identidade, placa, bloco, apartamento, morador)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            state['nome'],
            state['cpf'],
            state['identidade'],
            state['placa'],
            state['bloco'],
            state['apartamento'],
            state['morador']
        ))
        conn.commit()
        user_state[chat_id] = {'step': 'menu'}
        await update.message.reply_text("✅ Cadastro realizado com sucesso!", reply_markup=menu_principal)

# Inicialização do bot
app = ApplicationBuilder().token("7676763511:AAGpeT2sr3ILgDZHkm70NBmN4gD5aMYNBa8").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buscar", buscar_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
