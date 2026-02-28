import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import threading
import time
import random
from datetime import datetime
import json
import os
import itertools

# =====================================================
# CONFIGURAÇÕES
# =====================================================
ARQUIVO_CONFIG = "config_bot.json"
ARQUIVO_COMBINACOES = "combinacoes_usadas.json"

# =====================================================
# VARIÁVEIS GLOBAIS
# =====================================================
bot_ativo = False
bot_pausado = False
driver_instance = None

# =====================================================
# FUNÇÕES DE CONFIGURAÇÃO
# =====================================================
def carregar_config():
    padrao = {
        "usuario": "",
        "senha": "",
        "post_url": "https://www.instagram.com/p/",
        "palavras": [],
        "qtd_comentarios": "8"
    }
    
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                for chave in padrao:
                    if chave not in dados:
                        dados[chave] = padrao[chave]
                return dados
        except:
            return padrao
    return padrao

def salvar_config():
    dados = {
        "usuario": entry_usuario.get().strip(),
        "senha": entry_senha.get().strip(),
        "post_url": entry_post.get().strip(),
        "palavras": list(lista_palavras.get(0, tk.END)),
        "qtd_comentarios": entry_qtd_comentarios.get().strip()
    }
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_combinacoes_usadas():
    if os.path.exists(ARQUIVO_COMBINACOES):
        try:
            with open(ARQUIVO_COMBINACOES, 'r', encoding='utf-8') as f:
                return set(tuple(p) for p in json.load(f))
        except:
            return set()
    return set()

def salvar_combinacao_usada(palavra1, palavra2):
    usadas = carregar_combinacoes_usadas()
    usadas.add((palavra1, palavra2))
    with open(ARQUIVO_COMBINACOES, 'w', encoding='utf-8') as f:
        json.dump([list(p) for p in usadas], f, indent=4, ensure_ascii=False)

# =====================================================
# FUNÇÕES DE PERMUTAÇÃO (COM ESTATÍSTICAS)
# =====================================================
def calcular_permutacoes(palavras):
    """Calcula total de permutações possíveis"""
    if len(palavras) < 2:
        return 0
    return len(palavras) * (len(palavras) - 1)

def contar_combinacoes_usadas():
    """Conta quantas combinações já foram usadas"""
    try:
        if os.path.exists(ARQUIVO_COMBINACOES):
            with open(ARQUIVO_COMBINACOES, 'r', encoding='utf-8') as f:
                return len(json.load(f))
        else:
            return 0
    except:
        return 0

def gerar_permutacao_unica(palavras):
    """Gera uma permutação única de duas palavras que ainda não foi usada"""
    if len(palavras) < 2:
        return None, "❌ Menos de 2 palavras"
    
    try:
        if os.path.exists(ARQUIVO_COMBINACOES):
            with open(ARQUIVO_COMBINACOES, 'r', encoding='utf-8') as f:
                usadas = set(tuple(p) for p in json.load(f))
        else:
            usadas = set()
    except:
        usadas = set()
    
    todas = set()
    for p1, p2 in itertools.permutations(palavras, 2):
        todas.add((p1, p2))
    
    disponiveis = todas - usadas
    if not disponiveis:
        return None, "❌ Acabaram as combinações"
    
    return random.choice(list(disponiveis)), None

# =====================================================
# FUNÇÕES DO BOT (VERSÃO RÁPIDA)
# =====================================================
def log_message(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    texto_log.insert(tk.END, f"[{timestamp}] {msg}\n")
    texto_log.see(tk.END)
    janela.update()

def iniciar_driver():
    service = Service(GeckoDriverManager().install())
    options = Options()
    options.add_argument("--window-size=1366,768")
    return webdriver.Firefox(service=service, options=options)

def login_instagram(driver, usuario, senha):
    try:
        log_message("Fazendo login...")
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(3)
        
        campo_user = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        campo_pass = driver.find_element(By.NAME, "pass")
        
        campo_user.clear()
        campo_user.send_keys(usuario)
        
        campo_pass.clear()
        campo_pass.send_keys(senha)
        
        campo_pass.send_keys(Keys.RETURN)
        time.sleep(4)
        
        log_message(f"✅ Login OK: {usuario}")
        return True
        
    except Exception as e:
        log_message(f"❌ Erro login: {e}")
        return False

def comentar_rapido(driver, frase):
    try:
        if not hasattr(comentar_rapido, "pagina_carregada"):
            comentar_rapido.pagina_carregada = False
        
        post_url = entry_post.get().strip()
        
        if not comentar_rapido.pagina_carregada:
            log_message("📌 Primeiro acesso ao link...")
            driver.get(post_url)
            time.sleep(5)
            
            log_message("🔄 Segundo acesso ao link (refresh)...")
            driver.get(post_url)
            time.sleep(5)
            
            driver.execute_script("window.scrollBy(0, 200);")
            time.sleep(1)
            comentar_rapido.pagina_carregada = True
            log_message("✅ Página carregada após duplo acesso")
        
        # TENTA FECHAR "AGORA NÃO"
        try:
            botoes_agora_nao = [
                "//div[contains(text(), 'Agora não')]",
                "//button[contains(text(), 'Agora não')]",
                "//div[contains(text(), 'Not now')]",
                "//button[contains(text(), 'Not now')]"
            ]
            for xpath in botoes_agora_nao:
                try:
                    botao = driver.find_element(By.XPATH, xpath)
                    if botao.is_displayed():
                        botao.click()
                        log_message("✅ Fechou 'Agora não'")
                        time.sleep(1)
                        break
                except:
                    continue
        except:
            pass
        
        # RELOCALIZA A CAIXA
        tentativas = 0
        while tentativas < 3:
            try:
                caixa = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "textarea[placeholder*='comentário'], textarea[placeholder*='comment'], form textarea, div[role='textbox']"))
                )
                
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", caixa)
                time.sleep(0.3)
                
                try:
                    caixa.click()
                except:
                    driver.execute_script("arguments[0].click();", caixa)
                
                caixa.clear()
                caixa.send_keys(frase)
                caixa.send_keys(Keys.CONTROL, Keys.ENTER)
                
                return True
                
            except Exception as e:
                tentativas += 1
                if tentativas < 3:
                    log_message(f"⚠️ Tentativa {tentativas} falhou, relocalizando...")
                    time.sleep(1)
                else:
                    log_message(f"❌ Erro: {e}")
                    return False
        
        return False
        
    except Exception as e:
        log_message(f"⚠️ Erro: {e}")
        return False

def executar_bot():
    global bot_ativo, bot_pausado, driver_instance
    
    usuario = entry_usuario.get().strip()
    senha = entry_senha.get().strip()
    post_url = entry_post.get().strip()
    
    if not usuario or not senha:
        log_message("❌ Usuário/senha vazios")
        bot_ativo = False
        btn_iniciar.config(state=tk.NORMAL)
        return
    
    if not post_url:
        log_message("❌ URL vazia")
        bot_ativo = False
        btn_iniciar.config(state=tk.NORMAL)
        return
    
    palavras = list(lista_palavras.get(0, tk.END))
    if len(palavras) < 2:
        log_message("❌ Menos de 2 palavras")
        bot_ativo = False
        btn_iniciar.config(state=tk.NORMAL)
        return
    
    try:
        valor = entry_qtd_comentarios.get().strip().replace(',', '.')
        comentarios = int(float(valor))
        if comentarios < 1:
            comentarios = 1
    except:
        comentarios = 8
    
    salvar_config()
    
    # ===== ESTATÍSTICAS DE PERMUTAÇÕES =====
    total_permutacoes = calcular_permutacoes(palavras)
    usadas = contar_combinacoes_usadas()
    restantes = total_permutacoes - usadas
    
    log_message("=" * 60)
    log_message(f"🔥 BOT INICIADO")
    log_message(f"📊 Estatísticas de Permutações:")
    log_message(f"   • Total possível: {total_permutacoes}")
    log_message(f"   • Já usadas: {usadas}")
    log_message(f"   • Restantes: {restantes}")
    log_message(f"📌 Post: {post_url}")
    log_message(f"📝 Comentários solicitados: {comentarios}")
    log_message("=" * 60)
    
    if restantes == 0:
        log_message("❌ Todas as permutações já foram usadas! Resete ou adicione palavras.")
        bot_ativo = False
        btn_iniciar.config(state=tk.NORMAL)
        return
    
    # Ajusta comentários se não houver restantes suficientes
    if comentarios > restantes:
        log_message(f"⚠️ Apenas {restantes} permutações restantes. Ajustando comentários.")
        comentarios = restantes
    
    total = 0
    feitos = 0
    
    try:
        driver_instance = iniciar_driver()
        driver = driver_instance
        
        if not login_instagram(driver, usuario, senha):
            driver.quit()
            bot_ativo = False
            btn_iniciar.config(state=tk.NORMAL)
            return
        
        status_label.config(text=f"Rodando")
        janela.update()
        
        while feitos < comentarios and bot_ativo and not bot_pausado:
            perm, erro = gerar_permutacao_unica(palavras)
            if erro:
                log_message(erro)
                break
            
            frase = f"{perm[0]} {perm[1]}"
            log_message(f"{feitos+1}/{comentarios}: '{frase}'")
            
            if comentar_rapido(driver, frase):
                total += 1
                feitos += 1
                salvar_combinacao_usada(perm[0], perm[1])
                log_message(f"✅ Total: {total}")
                
                # Atualiza estatísticas
                usadas_agora = contar_combinacoes_usadas()
                restantes_agora = total_permutacoes - usadas_agora
                log_message(f"📊 Restantes agora: {restantes_agora}")
            else:
                log_message("❌ Falha")
                break
            
            if feitos < comentarios and bot_ativo and not bot_pausado:
                time.sleep(0.5)
        
        driver.quit()
        driver_instance = None
        
    except Exception as e:
        log_message(f"❌ Erro: {e}")
        if driver_instance:
            driver_instance.quit()
    
    log_message(f"\n🏁 FINALIZADO! Total: {total}")
    status_label.config(text="Parado")
    bot_ativo = False
    btn_iniciar.config(state=tk.NORMAL)
    btn_parar.config(state=tk.DISABLED)
    btn_pausar.config(state=tk.DISABLED)

# =====================================================
# FUNÇÕES DA INTERFACE (ATUALIZADAS)
# =====================================================
def iniciar_bot():
    global bot_ativo, bot_thread
    if bot_ativo:
        messagebox.showwarning("Aviso", "Bot já rodando")
        return
    
    bot_ativo = True
    bot_pausado = False
    bot_thread = threading.Thread(target=executar_bot, daemon=True)
    bot_thread.start()
    btn_iniciar.config(state=tk.DISABLED)
    btn_parar.config(state=tk.NORMAL)
    btn_pausar.config(state=tk.NORMAL)

def parar_bot():
    global bot_ativo
    bot_ativo = False
    log_message("⏹️ Parando")

def pausar_bot():
    global bot_pausado
    bot_pausado = not bot_pausado
    btn_pausar.config(text="▶️" if bot_pausado else "⏸️")

def adicionar_palavra():
    palavra = entry_palavra.get().strip().lower()
    if palavra:
        if palavra not in [p.lower() for p in lista_palavras.get(0, tk.END)]:
            lista_palavras.insert(tk.END, palavra)
            entry_palavra.delete(0, tk.END)
            atualizar_estatisticas()
            salvar_config()

def remover_palavra():
    sel = lista_palavras.curselection()
    if sel:
        lista_palavras.delete(sel[0])
        atualizar_estatisticas()
        salvar_config()

def atualizar_estatisticas():
    """Atualiza as estatísticas na interface"""
    palavras = list(lista_palavras.get(0, tk.END))
    total = calcular_permutacoes(palavras)
    usadas = contar_combinacoes_usadas()
    restantes = total - usadas
    
    label_qtd_palavras.config(text=f"Palavras: {len(palavras)}")
    label_estatisticas.config(
        text=f"Permutações: Total {total} | Usadas {usadas} | Restantes {restantes}",
        fg="green" if restantes > 0 else "red"
    )

def limpar_log():
    texto_log.delete(1.0, tk.END)

def salvar_campos():
    salvar_config()
    log_message("💾 Salvo")

def resetar_combinacoes():
    if messagebox.askyesno("Confirmar", "Resetar combinações?"):
        if os.path.exists(ARQUIVO_COMBINACOES):
            os.remove(ARQUIVO_COMBINACOES)
        log_message("🔄 Combinações resetadas!")
        atualizar_estatisticas()

# =====================================================
# INTERFACE
# =====================================================
janela = tk.Tk()
janela.title("🔥 BOT RÁPIDO - Permutações")
janela.geometry("850x750")

config = carregar_config()

# Login
frame_login = tk.LabelFrame(janela, text="LOGIN", padx=10, pady=10)
frame_login.pack(fill=tk.X, padx=10, pady=5)

tk.Label(frame_login, text="Usuário:").grid(row=0, column=0, sticky=tk.W)
entry_usuario = tk.Entry(frame_login, width=40)
entry_usuario.grid(row=0, column=1, padx=5)
entry_usuario.insert(0, config.get("usuario", ""))

tk.Label(frame_login, text="Senha:").grid(row=1, column=0, sticky=tk.W)
entry_senha = tk.Entry(frame_login, width=40, show="*")
entry_senha.grid(row=1, column=1, padx=5)
entry_senha.insert(0, config.get("senha", ""))

btn_salvar = tk.Button(frame_login, text="SALVAR", command=salvar_campos, bg="blue", fg="white")
btn_salvar.grid(row=2, column=1, sticky=tk.W, pady=5)

# Post
frame_post = tk.LabelFrame(janela, text="POST", padx=10, pady=10)
frame_post.pack(fill=tk.X, padx=10, pady=5)

tk.Label(frame_post, text="URL:").pack(side=tk.LEFT)
entry_post = tk.Entry(frame_post, width=70)
entry_post.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
entry_post.insert(0, config.get("post_url", ""))

# Palavras
frame_palavras = tk.LabelFrame(janela, text="PALAVRAS", padx=10, pady=10)
frame_palavras.pack(fill=tk.X, padx=10, pady=5)

frame_add = tk.Frame(frame_palavras)
frame_add.pack(fill=tk.X, pady=5)

entry_palavra = tk.Entry(frame_add, width=50)
entry_palavra.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

btn_add = tk.Button(frame_add, text="➕", command=adicionar_palavra, bg="green", fg="white", width=3)
btn_add.pack(side=tk.LEFT, padx=2)

btn_remove = tk.Button(frame_add, text="➖", command=remover_palavra, bg="red", fg="white", width=3)
btn_remove.pack(side=tk.LEFT, padx=2)

# Lista de palavras
frame_lista = tk.Frame(frame_palavras)
frame_lista.pack(fill=tk.X, pady=5)

scrollbar = tk.Scrollbar(frame_lista)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

lista_palavras = tk.Listbox(frame_lista, yscrollcommand=scrollbar.set, height=4)
lista_palavras.pack(side=tk.LEFT, fill=tk.X, expand=True)
scrollbar.config(command=lista_palavras.yview)

for p in config.get("palavras", []):
    lista_palavras.insert(tk.END, p)

# Estatísticas
frame_stats = tk.Frame(frame_palavras)
frame_stats.pack(fill=tk.X, pady=5)

label_qtd_palavras = tk.Label(frame_stats, text=f"Palavras: {len(config.get('palavras', []))}", font=("Arial", 9, "bold"))
label_qtd_palavras.pack(side=tk.LEFT, padx=5)

label_estatisticas = tk.Label(frame_stats, text="", font=("Arial", 9))
label_estatisticas.pack(side=tk.LEFT, padx=5)

# Atualiza estatísticas iniciais
atualizar_estatisticas()

# Config
frame_config = tk.LabelFrame(janela, text="CONFIG", padx=10, pady=10)
frame_config.pack(fill=tk.X, padx=10, pady=5)

tk.Label(frame_config, text="Comentários:").pack(side=tk.LEFT, padx=5)
entry_qtd_comentarios = tk.Entry(frame_config, width=10)
entry_qtd_comentarios.pack(side=tk.LEFT, padx=5)
entry_qtd_comentarios.insert(0, config.get("qtd_comentarios", "8"))

btn_reset = tk.Button(frame_config, text="RESETAR COMBOS", command=resetar_combinacoes, bg="purple", fg="white")
btn_reset.pack(side=tk.RIGHT, padx=5)

# Controle
frame_controle = tk.Frame(janela, pady=10)
frame_controle.pack(fill=tk.X, padx=10)

btn_iniciar = tk.Button(frame_controle, text="▶️ INICIAR", command=iniciar_bot, bg="green", fg="white", width=12)
btn_iniciar.pack(side=tk.LEFT, padx=5)

btn_parar = tk.Button(frame_controle, text="⏹️ PARAR", command=parar_bot, bg="red", fg="white", width=12, state=tk.DISABLED)
btn_parar.pack(side=tk.LEFT, padx=5)

btn_pausar = tk.Button(frame_controle, text="⏸️ PAUSAR", command=pausar_bot, bg="orange", fg="white", width=12, state=tk.DISABLED)
btn_pausar.pack(side=tk.LEFT, padx=5)

btn_limpar = tk.Button(frame_controle, text="LIMPAR", command=limpar_log, width=12)
btn_limpar.pack(side=tk.RIGHT, padx=5)

# Status
frame_status = tk.Frame(janela, pady=5)
frame_status.pack(fill=tk.X, padx=10)

tk.Label(frame_status, text="Status:").pack(side=tk.LEFT)
status_label = tk.Label(frame_status, text="Parado", fg="gray")
status_label.pack(side=tk.LEFT, padx=5)

# Log
frame_log = tk.LabelFrame(janela, text="LOG", padx=10, pady=10)
frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

texto_log = scrolledtext.ScrolledText(frame_log, height=10, font=("Consolas", 9))
texto_log.pack(fill=tk.BOTH, expand=True)

log_message("✅ BOT PRONTO - Modo Permutações")
log_message("📊 Estatísticas de permutações disponíveis")
log_message("▶️ Configura e inicia")

janela.mainloop()