import os
import io
import pandas as pd
from lxml import etree


# Primeiro tipo de leitura XML
def ler_xml_tiss1(path):
    ns = {'ans': 'http://www.ans.gov.br/padroes/tiss/schemas'}

    def get_txt(node, xpath):
        result = node.xpath(xpath, namespaces=ns)
        return result[0].text if result and result[0].text is not None else ""

    # Carregar o arquivo com tratamento de codificação UTF-16
    try:
        with open(path, 'r', encoding='utf-16') as f:
            texto_xml = f.read().strip()
        tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
    except UnicodeError:
        try:
            with open(path, 'r', encoding='utf-16-le') as f:
                texto_xml = f.read().strip()
            tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
        except Exception as e:
            return f"Erro de codificação: {e}"
    except Exception as e:
        return f"Erro ao ler o arquivo: {e}"

    lista_final = []

    # Iteração Principal (por Guia SP-SADT)
    for guia in tree.xpath('.//ans:guiaSP-SADT', namespaces=ns):
        
        # Dados do Cabeçalho da Guia 
        dados_guia = {
            'num_guia_prestador': get_txt(guia, './/ans:numeroGuiaPrestador'),
            'data_autorizacao': get_txt(guia, './/ans:dataAutorizacao'),
            'carteira_beneficiario': get_txt(guia, './/ans:numeroCarteira'),
            'nome_medico': get_txt(guia, './/ans:nomeProfissional'),
            'cnpj_executante': get_txt(guia, './/ans:codigoPrestadorNaOperadora'),
            'valor_total_guia': get_txt(guia, './/ans:valorTotalGeral')
        }

        # Procedimentos
        for proc in guia.xpath('.//ans:procedimentoExecutado', namespaces=ns):
            item = dados_guia.copy()
            item.update({
                'tipo_item': 'PROCEDIMENTO',
                'seq': get_txt(proc, './/ans:sequencialItem'),
                'data_servico': get_txt(proc, './/ans:dataExecucao'),
                'cod_tabela': get_txt(proc, './/ans:codigoTabela'),
                'cod_item': get_txt(proc, './/ans:codigoProcedimento'),
                'descricao': get_txt(proc, './/ans:descricaoProcedimento'),
                'qtd': get_txt(proc, './/ans:quantidadeExecutada'),
                'valor_unit': get_txt(proc, './/ans:valorUnitario'),
                'valor_total_item': get_txt(proc, './/ans:valorTotal')
            })
            lista_final.append(item)

        # Outras despesas
        for despesa in guia.xpath('.//ans:despesa', namespaces=ns):
            servicos = despesa.xpath('.//ans:servicosExecutados', namespaces=ns)
            if servicos:
                srv = servicos[0]
                item = dados_guia.copy()
                item.update({
                    'tipo_item': 'OUTRAS_DESPESAS',
                    'seq': get_txt(despesa, './/ans:sequencialItem'),
                    'data_servico': get_txt(srv, './/ans:dataExecucao'),
                    'cod_tabela': get_txt(srv, './/ans:codigoTabela'),
                    'cod_item': get_txt(srv, './/ans:codigoProcedimento'),
                    'descricao': get_txt(srv, './/ans:descricaoProcedimento'),
                    'qtd': get_txt(srv, './/ans:quantidadeExecutada'),
                    'valor_unit': get_txt(srv, './/ans:valorUnitario'),
                    'valor_total_item': get_txt(srv, './/ans:valorTotal')
                })
                lista_final.append(item)

    # Criação do df
    df = pd.DataFrame(lista_final)

    if not df.empty:
        # Converter colunas numéricas
        cols_numericas = ['qtd', 'valor_unit', 'valor_total_item', 'valor_total_guia']
        for col in cols_numericas:
            if col in df.columns:
                # Garante que seja string antes do replace para evitar erro com NaNs
                df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df



# Segundo tipo de leitura de XML 
def ler_xml_tiss2(caminho_arquivo):
    ns = {'ans': 'http://www.ans.gov.br/padroes/tiss/schemas'}

    def get_txt(node, xpath):
        result = node.xpath(xpath, namespaces=ns)
        return result[0].text if result and result[0].text is not None else ""

    try:
        # 1. Abre como texto informando a codificação UTF-16
        with open(caminho_arquivo, 'r', encoding='utf-16') as f:
            texto_xml = f.read().strip()
        
        # 2. Converte para bytes UTF-8, que é o padrão esperado pelo lxml
        tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
        
    except UnicodeError:
        # Fallback caso o arquivo seja UTF-16 Little Endian (comum em Windows)
        try:
            with open(caminho_arquivo, 'r', encoding='utf-16-le') as f:
                texto_xml = f.read().strip()
            tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
        except Exception as e:
            print(f"Erro de codificação: {e}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao abrir arquivo: {e}")
        return pd.DataFrame()

    lista_final = []

    # Procurar por qualquer tipo de guia suportada (SADT ou Internação)
    tags_guia = ['.//ans:guiaSP-SADT', './/ans:guiaResumoInternacao']
    
    for tag in tags_guia:
        for guia in tree.xpath(tag, namespaces=ns):
            # Cabeçalho
            dados_guia = {
                'tipo_guia': tag.split(':')[-1],
                'num_guia_prestador': get_txt(guia, './/ans:numeroGuiaPrestador'),
                'num_guia_operadora': get_txt(guia, './/ans:numeroGuiaOperadora'),
                'carteira_beneficiario': get_txt(guia, './/ans:numeroCarteira'),
                'data_inicio_fat': get_txt(guia, './/ans:dataInicioFaturamento'),
                'data_fim_fat': get_txt(guia, './/ans:dataFinalFaturamento'),
                'diagnostico': get_txt(guia, './/ans:diagnostico'),
                'cnpj_executante': get_txt(guia, './/ans:codigoPrestadorNaOperadora'),
                'valor_total_geral': get_txt(guia, './/ans:valorTotalGeral')
            }

            # Procedimentos
            for proc in guia.xpath('.//ans:procedimentoExecutado', namespaces=ns):
                item = dados_guia.copy()
                item.update({
                    'tipo_item': 'PROCEDIMENTO',
                    'seq': get_txt(proc, './/ans:sequencialItem'),
                    'data_execucao': get_txt(proc, './/ans:dataExecucao'),
                    'cod_tabela': get_txt(proc, './/ans:codigoTabela'),
                    'cod_item': get_txt(proc, './/ans:codigoProcedimento'),
                    'descricao': get_txt(proc, './/ans:descricaoProcedimento'),
                    'qtd': get_txt(proc, './/ans:quantidadeExecutada'),
                    'valor_unit': get_txt(proc, './/ans:valorUnitario'),
                    'valor_total_item': get_txt(proc, './/ans:valorTotal')
                })
                lista_final.append(item)

            # Outras despesas
            for despesa in guia.xpath('.//ans:despesa', namespaces=ns):
                servicos = despesa.xpath('.//ans:servicosExecutados', namespaces=ns)
                if servicos:
                    srv = servicos[0]
                    item = dados_guia.copy()
                    item.update({
                        'tipo_item': 'OUTRAS_DESPESAS',
                        'seq': get_txt(despesa, './/ans:sequencialItem'),
                        'data_execucao': get_txt(srv, './/ans:dataExecucao'),
                        'cod_tabela': get_txt(srv, './/ans:codigoTabela'),
                        'cod_item': get_txt(srv, './/ans:codigoProcedimento'),
                        'descricao': get_txt(srv, './/ans:descricaoProcedimento'),
                        'qtd': get_txt(srv, './/ans:quantidadeExecutada'),
                        'valor_unit': get_txt(srv, './/ans:valorUnitario'),
                        'valor_total_item': get_txt(srv, './/ans:valorTotal')
                    })
                    lista_final.append(item)

    df = pd.DataFrame(lista_final)

    # Conversão de tipos
    if not df.empty:
        cols_num = ['qtd', 'valor_unit', 'valor_total_item', 'valor_total_geral']
        for col in cols_num:
            if col in df.columns:
                # Remove espaços extras antes de converter
                df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df



# Terceiro tipo de leitura de XML
def ler_xml_tiss3(caminho_arquivo):
    ns = {'ans': 'http://www.ans.gov.br/padroes/tiss/schemas'}

    def get_txt(node, xpath):
        result = node.xpath(xpath, namespaces=ns)
        return result[0].text if result and result[0].text is not None else ""

    # Tratamento de codificação UTF-16 e caracteres nulos
    try:
        with open(caminho_arquivo, 'r', encoding='utf-16') as f:
            texto_xml = f.read().strip()
        tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
    except UnicodeError:
        try:
            with open(caminho_arquivo, 'r', encoding='utf-16-le') as f:
                texto_xml = f.read().strip()
            tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
        except Exception as e:
            print(f"Erro de codificação: {e}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao processar arquivo: {e}")
        return pd.DataFrame()

    lista_final = []

    # Localiza todas as guias de honorários no lote
    for guia in tree.xpath('.//ans:guiaHonorarios', namespaces=ns):
        
        # Cabeçalho
        dados_guia = {
            'num_guia_prestador': get_txt(guia, './/ans:numeroGuiaPrestador'),
            'guia_solic_internacao': get_txt(guia, './/ans:guiaSolicInternacao'),
            'senha': get_txt(guia, './/ans:senha'),
            'carteira': get_txt(guia, './/ans:numeroCarteira'),
            'hospital': get_txt(guia, './/ans:nomeContratado'),
            'data_inicio_fat': get_txt(guia, './/ans:dataInicioFaturamento'),
            'data_fim_fat': get_txt(guia, './/ans:dataFimFaturamento'),
            'valor_total_honorarios': get_txt(guia, './ans:valorTotalHonorarios')
        }

        # Procedimentos
        for proc in guia.xpath('.//ans:procedimentoRealizado', namespaces=ns):
            item = dados_guia.copy()
            
            # Info do Procedimento
            item.update({
                'data_execucao': get_txt(proc, './ans:dataExecucao'),
                'cod_procedimento': get_txt(proc, './/ans:codigoProcedimento'),
                'descricao': get_txt(proc, './/ans:descricaoProcedimento'),
                'qtd': get_txt(proc, './ans:quantidadeExecutada'),
                'valor_unitario': get_txt(proc, './ans:valorUnitario'),
                'valor_total_item': get_txt(proc, './ans:valorTotal'),
            })

            # Dados de profissionais
            prof = proc.xpath('.//ans:profissionais', namespaces=ns)
            if prof:
                p = prof[0]
                item.update({
                    'nome_medico': get_txt(p, './ans:nomeProfissional'),
                    'conselho': get_txt(p, './ans:conselhoProfissional'),
                    'num_conselho': get_txt(p, './ans:numeroConselhoProfissional'),
                    'uf_conselho': get_txt(p, './ans:UF'),
                    'cbo_medico': get_txt(p, './ans:CBO'),
                    'cpf_medico': get_txt(p, './/ans:cpfContratado')
                })
            
            lista_final.append(item)

    # Criação do Df
    df = pd.DataFrame(lista_final)

    # Tratamento de dados numéricos
    if not df.empty:
        colunas_financeiras = ['qtd', 'valor_unitario', 'valor_total_item', 'valor_total_honorarios']
        for col in colunas_financeiras:
            if col in df.columns:
                # Converte para string antes do replace para evitar erro com valores nulos
                df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


# Quarto tipo de leitura do XML
def ler_xml_tiss4(caminho_arquivo):
    ns = {'ans': 'http://www.ans.gov.br/padroes/tiss/schemas'}

    def get_txt(node, xpath):
        result = node.xpath(xpath, namespaces=ns)
        return result[0].text if result and result[0].text is not None else ""

    # Tratamento de codificação UTF-16 e limpeza de caracteres nulos
    try:
        with open(caminho_arquivo, 'r', encoding='utf-16') as f:
            texto_xml = f.read().strip()
        tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
    except UnicodeError:
        try:
            with open(caminho_arquivo, 'r', encoding='utf-16-le') as f:
                texto_xml = f.read().strip()
            tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
        except Exception as e:
            print(f"Erro de codificação: {e}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao processar arquivo: {e}")
        return pd.DataFrame()

    lista_final = []

    # Localiza todas as guias de consulta no lote
    for guia in tree.xpath('.//ans:guiaConsulta', namespaces=ns):
        
        item = {
            # Guia
            'num_guia_prestador': get_txt(guia, './/ans:numeroGuiaPrestador'),
            'num_guia_operadora': get_txt(guia, './/ans:numeroGuiaOperadora'),
            'carteira_beneficiario': get_txt(guia, './/ans:numeroCarteira'),
            
            # Profissional executante
            'nome_medico': get_txt(guia, './/ans:nomeProfissional'),
            'crm_medico': get_txt(guia, './/ans:numeroConselhoProfissional'),
            'uf_medico': get_txt(guia, './/ans:UF'),
            'cbo_medico': get_txt(guia, './/ans:CBOS'),
            
            # Dados de atendimento
            'data_atendimento': get_txt(guia, './/ans:dataAtendimento'),
            'tipo_consulta': get_txt(guia, './/ans:tipoConsulta'),
            
            # Dados dos procedimentos
            'cod_tabela': get_txt(guia, './/ans:codigoTabela'),
            'cod_procedimento': get_txt(guia, './/ans:codigoProcedimento'),
            'valor_consulta': get_txt(guia, './/ans:valorProcedimento')
        }
        
        lista_final.append(item)

    # Criação do Df
    df = pd.DataFrame(lista_final)

    # Conversão de valores
    if not df.empty:
        if 'valor_consulta' in df.columns:
            # Garante que seja string para o replace e converte para numérico
            df['valor_consulta'] = df['valor_consulta'].astype(str).str.replace(',', '.')
            df['valor_consulta'] = pd.to_numeric(df['valor_consulta'], errors='coerce')
    
    return df


# Quinto tipo de leitura de XML
def ler_xml_tiss5(caminho_arquivo):
    ns = {'ans': 'http://www.ans.gov.br/padroes/tiss/schemas'}

    def get_txt(node, xpath):
        result = node.xpath(xpath, namespaces=ns)
        # Retorna "0.00" como padrão para campos que podem ser numéricos
        return result[0].text if result and result[0].text is not None else "0.00"

    # Tratamento de codificação UTF-16 e limpeza de caracteres nulos
    try:
        with open(caminho_arquivo, 'r', encoding='utf-16') as f:
            texto_xml = f.read().strip()
        tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
    except UnicodeError:
        try:
            with open(caminho_arquivo, 'r', encoding='utf-16-le') as f:
                texto_xml = f.read().strip()
            tree = etree.parse(io.BytesIO(texto_xml.encode('utf-8')))
        except Exception as e:
            print(f"Erro de codificação: {e}")
            return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao processar arquivo: {e}")
        return pd.DataFrame()

    lista_final = []

    # Localiza todas as guias de Resumo de Internação
    for guia in tree.xpath('.//ans:guiaResumoInternacao', namespaces=ns):
        
        # Estrutura de dados extraída
        dados = {
            # Identificação
            'num_guia_prestador': get_txt(guia, './/ans:numeroGuiaPrestador'),
            'num_guia_operadora': get_txt(guia, './/ans:numeroGuiaOperadora'),
            'senha': get_txt(guia, './/ans:senha'),
            'carteira': get_txt(guia, './/ans:numeroCarteira'),
            
            # Período e Diagnóstico 
            'data_inicio_internacao': get_txt(guia, './/ans:dataInicioFaturamento'),
            'data_fim_internacao': get_txt(guia, './/ans:dataFinalFaturamento'),
            'diagnostico': get_txt(guia, './/ans:diagnostico'),
            'motivo_encerramento': get_txt(guia, './/ans:motivoEncerramento'),
            
            # (Bloco valorTotal)
            'vlr_procedimentos': get_txt(guia, './/ans:valorProcedimentos'),
            'vlr_diarias': get_txt(guia, './/ans:valorDiarias'),
            'vlr_taxas_alugueis': get_txt(guia, './/ans:valorTaxasAlugueis'),
            'vlr_materiais': get_txt(guia, './/ans:valorMateriais'),
            'vlr_medicamentos': get_txt(guia, './/ans:valorMedicamentos'),
            'vlr_opme': get_txt(guia, './/ans:valorOPME'),
            'vlr_gases': get_txt(guia, './/ans:valorGasesMedicinais'),
            'vlr_total_geral': get_txt(guia, './/ans:valorTotalGeral'),
        }
        
        lista_final.append(dados)

    df = pd.DataFrame(lista_final)

    # Conversão de todas as colunas de valor para numérico
    if not df.empty:
        colunas_valor = [c for c in df.columns if c.startswith('vlr_')]
        for col in colunas_valor:
            # Converte para string antes do replace e trata nulos com fillna
            df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
    
    return df


# Função para concatenar e ler todos os XMLs de uma pasta
def processar_arquivos_xml(diretorio=None, arquivos_selecionados=None):
    # Inicialização das listas para cada formato
    lista_tiss1 = []
    lista_tiss2 = []
    lista_tiss3 = []
    lista_tiss4 = []
    lista_tiss5 = [] 
    
    if arquivos_selecionados is not None:
        caminhos_para_processar = arquivos_selecionados
    elif diretorio is not None:
        # Listar apenas arquivos XML
        arquivos = [f for f in os.listdir(diretorio) if f.endswith('.xml')]
        caminhos_para_processar = [os.path.join(diretorio, f) for f in arquivos]
    else:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    for caminho_completo in caminhos_para_processar:
        arquivo = os.path.basename(caminho_completo)

        # TENTATIVA 1
        df_temp = ler_xml_tiss1(caminho_completo)
        if df_temp is not None and not df_temp.empty:
            lista_tiss1.append(df_temp)
            continue 
            
        # TENTATIVA 2
        df_temp = ler_xml_tiss2(caminho_completo)
        if df_temp is not None and not df_temp.empty:
            lista_tiss2.append(df_temp)
            continue 
            
        # TENTATIVA 3 
        df_temp = ler_xml_tiss3(caminho_completo)
        if df_temp is not None and not df_temp.empty:
            lista_tiss3.append(df_temp)
            continue

        # TENTATIVA 4
        df_temp = ler_xml_tiss4(caminho_completo)
        if df_temp is not None and not df_temp.empty:
            lista_tiss4.append(df_temp)
            continue # Adicionado continue para consistência

        # TENTATIVA 5
        df_temp = ler_xml_tiss5(caminho_completo)
        if df_temp is not None and not df_temp.empty:
            lista_tiss5.append(df_temp)
        else:
            print(f"Aviso: {arquivo} não compatível com nenhum formato (1, 2, 3, 4 ou 5).")

    # Consolidação dos DataFrames finais
    df_final_tiss1 = pd.concat(lista_tiss1, ignore_index=True) if lista_tiss1 else pd.DataFrame()
    df_final_tiss2 = pd.concat(lista_tiss2, ignore_index=True) if lista_tiss2 else pd.DataFrame()
    df_final_tiss3 = pd.concat(lista_tiss3, ignore_index=True) if lista_tiss3 else pd.DataFrame()
    df_final_tiss4 = pd.concat(lista_tiss4, ignore_index=True) if lista_tiss4 else pd.DataFrame()
    df_final_tiss5 = pd.concat(lista_tiss5, ignore_index=True) if lista_tiss5 else pd.DataFrame()
    
    return df_final_tiss1, df_final_tiss2, df_final_tiss3, df_final_tiss4, df_final_tiss5


