import os
import re
import sys
import threading
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image
from converter import processar_arquivos_xml

# Configurações de visual
ctk.set_appearance_mode('write')
ctk.set_default_color_theme('blue')

# Configurações da primeira janela
janela = ctk.CTk()
janela.title('Leitura de XML')
janela.geometry('1100x700')
janela.minsize(1100,700)
janela.configure(fg_color='#546B41')



#================== IMAGENS ===================
# Função para compilar as imagens ao projeto
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

janela.iconbitmap(resource_path("ICONE.ico"))

# Função para converter as imagens em branco
def branco(img):
    img = img.convert("RGBA")
    branca = Image.new("RGBA", img.size, (255, 255, 255, 255))
    branca.putalpha(img.split()[3])
    return branca

pasta = ctk.CTkImage(
    light_image=branco(Image.open(resource_path("folder.png"))),
    dark_image=branco(Image.open(resource_path("folder.png"))),
    size=(20, 20)
)

conversao = ctk.CTkImage(
    light_image=branco(Image.open(resource_path("seta_conversao.png"))),
    dark_image=branco(Image.open(resource_path("seta_conversao.png"))),
    size=(30, 30)
)

raio = ctk.CTkImage(
    light_image=branco(Image.open(resource_path("raio.png"))),
    dark_image=branco(Image.open(resource_path("raio.png"))),
    size=(20, 20)
)


#==============================================

# Variáveis Globais
caminho_selecionado = ''
checkbox_vars = {}
checkboxes_arquivos = {}
resultados = []
lista = []

# ====================================================
def selecionar_pasta():
    global caminho_selecionado, checkboxes_arquivos
    caminho_pasta = filedialog.askdirectory()
    
    if caminho_pasta:
        caminho_selecionado = caminho_pasta
        nova_string = re.sub(r'^(.*?/){3}', 'HOME/', caminho_pasta)
        nova_string = nova_string.replace('/', ' > ')
        label_caminho.configure(text=nova_string, font=('Calibri', 14, 'bold'))
        
        # Limpa e reseta o dicionário de checkboxes
        checkboxes_arquivos = {}
        for widget in frame_lista.winfo_children():
            if int(widget.grid_info().get("row", 0)) > 0:
                widget.destroy()

        try:
            arquivos = [f for f in os.listdir(caminho_pasta) if f.lower().endswith('.xml')]
        except Exception as e:
            print(f"Erro: {e}")
            return

        for i, arquivo in enumerate(arquivos, start=1): 
            caminho_completo = os.path.join(caminho_pasta, arquivo)
            
            # CRIAMOS UMA VARIÁVEL PARA CADA ARQUIVO
            var_check = ctk.BooleanVar(value=True)
            checkboxes_arquivos[caminho_completo] = var_check

            check = ctk.CTkCheckBox(
                frame_lista, text="", width=10, variable=var_check, # Vincula a variável
                checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=2, fg_color='#2E7D32', hover_color='#1B5E20'
            )
            check.grid(row=i, column=0, padx=15, pady=5, sticky="w")

            ctk.CTkLabel(frame_lista, text=arquivo, anchor="w", text_color="black"
            ).grid(row=i, column=1, padx=10, sticky="ew")

            tamanho = os.path.getsize(caminho_completo) / 1024
            ctk.CTkLabel(frame_lista, text=f"{tamanho:.1f} KB", anchor="e", text_color="gray"
            ).grid(row=i, column=2, padx=10, sticky="e")





# ====================================================
# Função para gerar uma tela de sucesso
def mensagem_sucesso():
    sucesso = ctk.CTkToplevel(janela)
    sucesso.title('Concluído')
    sucesso.geometry('300x120')
    sucesso.maxsize(300,120)
    sucesso.minsize(300,120)

    sucesso.grab_set()
    

    # Logica de centralização
    sucesso.update_idletasks()
    x = janela.winfo_x() + (janela.winfo_width() // 2) - (300 // 2)
    y = janela.winfo_y() + (janela.winfo_height() // 2) - (150 // 2)
    sucesso.geometry(f'300x120+{x}+{y}')
    
    sucesso.after(200, lambda: sucesso.iconbitmap(resource_path("ICONE.ico")))

    label = ctk.CTkLabel(sucesso, text='Salvo com Sucesso!', font=('Calibri', 14, 'bold'))
    label.pack(pady=10)

    # Botão OK que apenas fecha essa janela
    btn_ok = ctk.CTkButton(sucesso, text='OK', width=80, command=sucesso.destroy, font=('Calibri', 14, 'bold'), fg_color='#2E7D32', hover_color='#1B5E20')
    btn_ok.pack(pady=5)


# ====================================================
# Função Genérica de Tela de Carregamento
def abrir_aviso(texto):
    aviso = ctk.CTkToplevel(janela)
    aviso.title('Aguarde')
    aviso.geometry('300x120')
    aviso.resizable(False, False)

    # Logica de centralização
    aviso.update_idletasks()
    x = janela.winfo_x() + (janela.winfo_width() // 2) - (300 // 2)
    y = janela.winfo_y() + (janela.winfo_height() // 2) - (150 // 2)
    aviso.geometry(f'300x120+{x}+{y}')
    
    aviso.after(200, lambda: aviso.iconbitmap(resource_path("ICONE.ico")))

    # Mantém o aviso na frente e bloqueia a janela principal
    #aviso.transient(janela)
    aviso.grab_set()

    label = ctk.CTkLabel(aviso, text=texto)
    label.pack(pady=15, anchor='center')

    progresso = ctk.CTkProgressBar(aviso, orientation='horizontal', mode='indeterminated', progress_color='#2E7D32')
    progresso.pack(padx=20, fill='x', anchor='center')
    progresso.start()
    
    return aviso

# ====================================================
# Função para Processar XML 
def visualizar_simples():
    if not caminho_selecionado:
        label_caminho.configure(text="Erro: Selecione uma pasta primeiro!", text_color="red")
        return

    # PEGA APENAS OS CAMINHOS QUE ESTÃO MARCADOS NA LISTA DA ESQUERDA
    selecao_atual = [caminho for caminho, var in checkboxes_arquivos.items() if var.get()]
    
    if not selecao_atual:
        print("Nenhum arquivo XML selecionado na lista.")
        return

    aviso = abrir_aviso('Lendo arquivos XML selecionados...')

    def tarefa_background():
        global resultados
        # CHAMADA DA FUNÇÃO USANDO O NOVO PARÂMETRO
        resultados = processar_arquivos_xml(arquivos_selecionados=selecao_atual)
        janela.after(0, lambda: atualizar_interface_pos_leitura(aviso))

    threading.Thread(target=tarefa_background).start()

def atualizar_interface_pos_leitura(aviso):
    global lista
    aviso.destroy() 
    
    # Limpa o quadro da direita (Resultados)
    for widget in quadro_fundo.winfo_children():
        if isinstance(widget, ctk.CTkCheckBox):
            widget.destroy()

    checkbox_vars.clear()


    lista = []
    # Mostra os DataFrames gerados (DF1, DF2...)
    for i, df in enumerate(resultados, 1):
        if df is not None and not df.empty:
            if i == 2:
                nome = f'DF{i} - Resumo - {len(df)} linhas'
            elif i == 1:
                nome = f'DF{i} - SP-SADT - {len(df)} linhas'
            elif i == 3:
                nome = f'DF{i} - Honorarios - {len(df)} linhas'
            elif i == 4:
                nome = f'DF{i} - Consultas - {len(df)} linhas'
            elif i == 5:
                nome = f'DF{i} - Resumo - {len(df)} linhas'
            else:
                nome = f'DF{i} - {len(df)} linhas'
            lista.append(nome)

            var = ctk.BooleanVar(value=True) # Inicia marcado para salvar
            checkbox_vars[nome] = var
            cb = ctk.CTkCheckBox(quadro_fundo, text=nome, variable=var, border_width=2.5, corner_radius=2, height=2,command=imprimir_selecionados, width=180, 
                                 fg_color='#2E7D32', hover_color='#1B5E20')
            cb.pack(pady=5, padx=55, anchor="w")
    
    label_resultado.pack_forget()
    #label_resultado.pack(pady=20)
    imprimir_selecionados()

# ====================================================
# Função para Salvar Excel
def mostrar_selecionados():
    selecionados = [nome for nome, var in checkbox_vars.items() if var.get()]
    if not selecionados:
        return

    caminho_salvar = filedialog.askdirectory()
    if not caminho_salvar:
        return

    # 1. Abre a tela de carregamento
    aviso = abrir_aviso('Salvando arquivos...')

    # 2. Define a tarefa pesada de salvamento
    def tarefa_salvar_background():
        for nome in selecionados:
            indice = int(nome.split(' - ')[0].replace('DF', '')) - 1
            df_selecionado = resultados[indice]
            df_selecionado.to_excel(f'{caminho_salvar}/{nome}.xlsx', index=False)
        
        # Fecha o aviso quando terminar
        janela.after(0, lambda: [aviso.destroy(), mensagem_sucesso()])

    # Inicia a thread
    threading.Thread(target=tarefa_salvar_background).start()

# ====================================================
# Função que lê o estado das variáveis e atualiza texto
def imprimir_selecionados():
    selecionados = [nome for nome, var in checkbox_vars.items() if var.get()]
    
    if selecionados:
        texto = f"Selecionados: {', '.join(selecionados)}"
    else:
        texto = "Nenhum item selecionado"
        
    label_resultado.configure(text=texto)

# ====================================================
# CONSTRUÇÃO DA INTERFACE PRINCIPAL
# Construção do frame de tras
tela_fundo = ctk.CTkFrame(master=janela,
                          fg_color='white',
                          corner_radius=6)

tela_fundo.pack(padx=15, pady=15, fill='both', expand=True, side='left')


# Construção da tela de exibição dos arquivos em pasta
tela_visua = ctk.CTkFrame(janela,
                          fg_color='white',
                          corner_radius=6,
                          width=320
                          )
tela_visua.pack(padx=15, pady=15, fill='y', side='right')
tela_visua.pack_propagate(False)


#====================================================================
# Frame superior
frame_superior = ctk.CTkFrame(tela_fundo, fg_color='transparent')
frame_superior.pack(fill='x', padx=10, pady=10)

# Criando um Frame para os botoes de selecionar pasta e converter XML
frame1 = ctk.CTkFrame(frame_superior, fg_color='transparent')
frame1.pack(side='left', anchor='w')

# Criando um frame para o botão de pasta
frame2 = ctk.CTkFrame(frame_superior,
                       fg_color='transparent', 
                       border_width=2,
                       border_color='#546B41', 
                       corner_radius=10)
frame2.pack(side='right', anchor='e')

# Titulo para o caminho
texto = ctk.CTkLabel(frame2, text='CAMINHO DA PASTA', font=('Calibri', 14, 'bold'), fg_color='transparent')
texto.pack(pady=5, anchor='center')

# Titulo para selecionar pasta
texto1 = ctk.CTkLabel(frame1, text='Selecione uma pasta para converter', font=('Calibri', 20, 'bold'))
texto1.pack(padx=10, anchor='w')

# Botão de selecionar pasta
botao_selecionar = ctk.CTkButton(frame1
                                 ,text='Selecionar Pasta'
                                 ,command=selecionar_pasta
                                 ,image=pasta
                                 ,font=('Calibri', 16, 'bold')
                                 ,fg_color='#2E7D32'
                                 ,hover_color='#1B5E20'
                                 ,width=170
                                 ,height=35)
botao_selecionar.pack(pady=10, padx=15, anchor="w")


label_caminho = ctk.CTkLabel(
    frame2, 
    text='Nenhuma pasta selecionada', 
    wraplength=250, 
    fg_color='#E0E0E0', 
    text_color='black',
    corner_radius=4, 
    width=280, 
    height=40,
    font=('Calibri', 14, 'bold')
)
label_caminho.pack(pady=5, padx=20, anchor="e")


botao_converter = ctk.CTkButton(frame1,
                                text='Converter XML',
                                command=visualizar_simples,
                                image=raio,
                                compound='left',
                                anchor='w',
                                font=('Calibri', 16, 'bold'),
                                fg_color='#2E7D32',
                                hover_color='#1B5E20',
                                height=35,
                                width=170)
botao_converter.pack(pady=10, padx=15, anchor="w" )

# Quadro de fundo
quadro_fundo = ctk.CTkFrame(tela_visua, fg_color='#E0E0E0', corner_radius=15, width=300, height=300)
quadro_fundo.pack_propagate(False) 
quadro_fundo.pack(side="top", pady=20, padx=10)

label_titulo = ctk.CTkLabel(quadro_fundo, text="Selecione os arquivos", font=("Calibri", 20, "bold"))
label_titulo.pack(pady=15)

# Label de resultado (inicia no final do quadro)
label_resultado = ctk.CTkLabel(quadro_fundo, text="Nenhum item selecionado", text_color="gray")
label_resultado.pack(pady=20)

# Botão de visualização (Salvar)
botao_visualizar = ctk.CTkButton(
    tela_visua, 
    text='Baixar tabelas .xlsx', 
    command=mostrar_selecionados,
    image=conversao,
    width=200,
    height=50,
    fg_color='#2E7D32',
    hover_color='#1B5E20',
    font=('Calibri', 17, 'bold')
)
botao_visualizar.pack(pady=30, side='bottom')


# Tela de visualização dos arquivos em xml
frame_lista = ctk.CTkScrollableFrame(
    tela_fundo, 
    fg_color="white",          # Fundo branco para contrastar com o texto
    corner_radius=10, 
    border_width=2, 
    border_color="#d0d0d0"
)
frame_lista.grid_columnconfigure(1, weight=1)
frame_lista._scrollbar.configure(width=10)
frame_lista.pack(padx=20, pady=20, fill="both", expand=True)
fonte_h = ctk.CTkFont(size=12, weight="bold")
ctk.CTkLabel(frame_lista, text="OK", font=fonte_h, text_color="gray").grid(row=0, column=0, padx=15, pady=10)
ctk.CTkLabel(frame_lista, text="NOME DO ARQUIVO XML", font=fonte_h, text_color="gray").grid(row=0, column=1, padx=10, pady=10, sticky="w")
ctk.CTkLabel(frame_lista, text="TAMANHO", font=fonte_h, text_color="gray").grid(row=0, column=2, padx=10, pady=10, sticky="e")

# Fechamento da janela
janela.mainloop()