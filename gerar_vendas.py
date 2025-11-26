import pandas as pd
from kob_car_api import DataStorage
from datetime import date, timedelta, datetime
import os
import logging
from kob_car_api.utils import setup_logging
from dotenv import load_dotenv

load_dotenv()
vendas_path = os.getenv('VENDAS_PATH')

logger = setup_logging(log_level="INFO")


logger.info("Iniciando Relatório de Vendas a Gerar")

storage = DataStorage(db_path='data/kob_car.db')

logger.info("Iniciando Tratamento de Dados")

db_compradores = DataStorage.query_database(self=storage, query= "SELECT status, pessoaJuridica_cnpj, pessoaJuridica_nomeFantasia, substr(pessoaJuridica_cnpj, 1, 8) AS raiz FROM compradores WHERE status = 3")
compradores_disp = db_compradores['raiz'].to_list()

db_reservas = DataStorage.query_database(self=storage, query="SELECT * From reservas WHERE status = 3 And saldoDisponivel > 1 ORDER BY saldoDisponivel DESC")
db_reservas['comprador_cnpj'] = db_reservas['comprador_cnpj'].astype(str).str.zfill(14)
db_reservas['raiz'] = db_reservas['comprador_cnpj'].astype(str).str[:8]
db_vendas = DataStorage.query_database(self=storage, query="SELECT * From vendas")

nf_qlik = pd.read_csv(fr'{vendas_path}', sep=';')

naturezas_nao_consideradas = ['Conta-Ordem Remessa', 'Devolução NF Cliente', 'Dev.Conta e Ordem V', 'Devolução NF Propria']

nf_qlik = nf_qlik[~nf_qlik['Tipo Ordem Faturamento'].isin(naturezas_nao_consideradas)]
nf_qlik['CNPJ Parceiro Negócio'] = nf_qlik['CNPJ Parceiro Negócio'].astype(str).str.zfill(14)
nf_qlik['raiz'] = nf_qlik['CNPJ Parceiro Negócio'].astype(str).str[:8]

db_vendas['Chave'] = db_vendas['referenciaVendedor'].astype(str).str.zfill(15)
nf_qlik['Chave'] = nf_qlik['NF Faturamento'].astype(str).str.zfill(15)

merged = nf_qlik.merge(db_vendas, how='left', on='Chave')
merged = merged.drop_duplicates(subset='NF Faturamento')

vendas_JaCriadas = merged[~merged['vendedor_cnpj'].isna()].copy()
vendas_aCriar = merged[merged['vendedor_cnpj'].isna()].copy()


vendas_CompradoresBloquados = vendas_aCriar[~vendas_aCriar['raiz'].isin(compradores_disp)]
vendas_aCriar = vendas_aCriar[vendas_aCriar['raiz'].isin(compradores_disp)]


vendas_aCriar.to_excel('data/vendas_aProcessar.xlsx', engine='openpyxl')
vendas_JaCriadas.to_excel('data/vendas_JaCriadas.xlsx', engine='openpyxl')
vendas_CompradoresBloquados.to_excel('data/vendas_CompradoresBloqueados.xlsx', engine='openpyxl')

logger.info(f"Relatório de Vendas no GCP gerado com {len(vendas_aCriar)} vendas")

logger.info(f"Início do processo de Filtragem")

resultados_funil = {
    'entrada': vendas_aCriar.copy(),
    'sem_referencia_vendedor': [],
    'sem_raiz_correspondente': [],
    'sem_saldo_suficiente': [],
    'sucesso': []
}


contador = {
    'entrada': len(vendas_aCriar),
    'filtro1_passou': 0,
    'filtro1_rejeitado': 0,
    'filtro2_passou': 0,
    'filtro2_rejeitado': 0,
    'filtro3_passou': 0,
    'filtro3_rejeitado': 0
}

to_file = []
infos_disp = pd.DataFrame()

db_reservas_atualizado = db_reservas.copy()


for idx, i in vendas_aCriar.iterrows():
    motivo_rejeicao = None
    
    filtro1 = db_reservas_atualizado[
        db_reservas_atualizado['referenciaVendedor'] == i['Cód. Condição Pagamento Faturamento']
    ]
    
    if filtro1.empty:
        motivo_rejeicao = 'sem_referencia_vendedor'
        registro = i.to_dict()
        registro['motivo_rejeicao'] = 'Nenhuma reserva encontrada com a referência de vendedor'
        resultados_funil['sem_referencia_vendedor'].append(registro)
        contador['filtro1_rejeitado'] += 1
        continue
    
    contador['filtro1_passou'] += 1
    
    
    filtro2 = filtro1[filtro1['raiz'] == i['raiz']]
    
    if filtro2.empty:
        motivo_rejeicao = 'sem_raiz_correspondente'
        registro = i.to_dict()
        registro['motivo_rejeicao'] = 'Nenhuma reserva encontrada com a mesma raiz de CNPJ'
        registro['reservas_com_referencia'] = len(filtro1)
        resultados_funil['sem_raiz_correspondente'].append(registro)
        contador['filtro2_rejeitado'] += 1
        continue
    
    contador['filtro2_passou'] += 1
    
    
    filtro3 = filtro2[filtro2['saldoDisponivel'] >= i['Valor Total']]
    
    if filtro3.empty:
        motivo_rejeicao = 'sem_saldo_suficiente'
        registro = i.to_dict()
        registro['motivo_rejeicao'] = 'Nenhuma reserva com saldo suficiente'
        registro['valor_necessario'] = i['Valor Total']
        registro['maior_saldo_disponivel'] = filtro2['saldoDisponivel'].max()
        registro['reservas_com_raiz'] = len(filtro2)
        resultados_funil['sem_saldo_suficiente'].append(registro)
        contador['filtro3_rejeitado'] += 1
        continue
    
    contador['filtro3_passou'] += 1
    
    
    reservas_disp = filtro3.head(1)
    id_reserva_selecionada = reservas_disp[['reservaId','comprador_cnpj']].reset_index()
    
    if len(id_reserva_selecionada) != 0:
        
        data_emissao = datetime.strptime(i['Data Emissão Faturamento'], '%d/%m/%Y').date()
        dif = date.today() - data_emissao
        emissao_sent = data_emissao.strftime('%Y-%m-%d') if dif.days <= 10 else (date.today() - timedelta(10)).strftime('%Y-%m-%d')
        cnpj = id_reserva_selecionada['comprador_cnpj'][0]
        reserva_id = int(id_reserva_selecionada['reservaId'][0])
        valor_venda = i['Valor Total']
        
        
        data = {
            "cnpjComprador": cnpj,
            "valorVenda": valor_venda,
            "descricao": i['Ordem Venda Faturamento'],
            "referenciaConciliacao": i['NF Faturamento'],
            "idReserva": reserva_id,
            "dataInicioPrazo": emissao_sent,
            "status": "Pendente"
        }
        infos_disp = pd.concat([infos_disp, reservas_disp])
        to_file.append(data)
        
        idx_reserva = db_reservas_atualizado[
            db_reservas_atualizado['reservaId'] == reserva_id
        ].index
        
        if len(idx_reserva) > 0:
            saldo_anterior = db_reservas_atualizado.loc[idx_reserva[0], 'saldoDisponivel']
            saldo_novo = saldo_anterior - valor_venda
            
            # Atualizar o saldo
            db_reservas_atualizado.loc[idx_reserva[0], 'saldoDisponivel'] = saldo_novo
            
            logger.info(f"Reserva {reserva_id}: Saldo {saldo_anterior:.2f} → {saldo_novo:.2f} (Diferença: {valor_venda:.2f})")
        
        registro = i.to_dict()
        registro['reservaId_selecionada'] = reserva_id
        registro['saldo_anterior'] = saldo_anterior
        registro['saldo_novo'] = saldo_novo
        registro['valor_utilizado'] = valor_venda
        resultados_funil['sucesso'].append(registro)


logger.info(f"Filtros Finalizados")

to_file = pd.DataFrame(to_file)
to_file = to_file.drop_duplicates(subset='referenciaConciliacao')
to_file.index.rename("vendaIndex", inplace=True)
to_file.to_excel('run.xlsx', engine='openpyxl', sheet_name='output_venda')

logger.info(f"Salvando Arquivos")

output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

pd.DataFrame(resultados_funil['entrada']).to_csv(
    f"{output_dir}/00_entrada_total.csv", 
    index=False, 
    sep=';', 
    encoding='utf-8-sig'
)

if resultados_funil['sem_referencia_vendedor']:
    pd.DataFrame(resultados_funil['sem_referencia_vendedor']).to_csv(
        f"{output_dir}/01_rejeitadas_filtro1_sem_referencia.csv",
        index=False,
        sep=';',
        encoding='utf-8-sig'
    )

if resultados_funil['sem_raiz_correspondente']:
    pd.DataFrame(resultados_funil['sem_raiz_correspondente']).to_csv(
        f"{output_dir}/02_rejeitadas_filtro2_sem_raiz.csv",
        index=False,
        sep=';',
        encoding='utf-8-sig'
    )

if resultados_funil['sem_saldo_suficiente']:
    pd.DataFrame(resultados_funil['sem_saldo_suficiente']).to_csv(
        f"{output_dir}/03_rejeitadas_filtro3_sem_saldo.csv",
        index=False,
        sep=';',
        encoding='utf-8-sig'
    )

if resultados_funil['sucesso']:
    pd.DataFrame(resultados_funil['sucesso']).to_csv(
        f"{output_dir}/04_sucesso_reservas_encontradas.csv",
        index=False,
        sep=';',
        encoding='utf-8-sig'
    )


resumo = pd.DataFrame([
    {'Etapa': 'Entrada', 'Quantidade': contador['entrada'], 'Percentual': '100.0%'},
    {'Etapa': 'Filtro 1 - Aprovado', 'Quantidade': contador['filtro1_passou'], 
     'Percentual': f"{(contador['filtro1_passou']/contador['entrada']*100):.1f}%"},
    {'Etapa': 'Filtro 1 - Rejeitado', 'Quantidade': contador['filtro1_rejeitado'],
     'Percentual': f"{(contador['filtro1_rejeitado']/contador['entrada']*100):.1f}%"},
    {'Etapa': 'Filtro 2 - Aprovado', 'Quantidade': contador['filtro2_passou'],
     'Percentual': f"{(contador['filtro2_passou']/contador['entrada']*100):.1f}%"},
    {'Etapa': 'Filtro 2 - Rejeitado', 'Quantidade': contador['filtro2_rejeitado'],
     'Percentual': f"{(contador['filtro2_rejeitado']/contador['entrada']*100):.1f}%"},
    {'Etapa': 'Filtro 3 - Aprovado', 'Quantidade': contador['filtro3_passou'],
     'Percentual': f"{(contador['filtro3_passou']/contador['entrada']*100):.1f}%"},
    {'Etapa': 'Filtro 3 - Rejeitado', 'Quantidade': contador['filtro3_rejeitado'],
     'Percentual': f"{(contador['filtro3_rejeitado']/contador['entrada']*100):.1f}%"},
])

resumo.to_csv(
    f"{output_dir}/00_resumo_funil.csv",
    index=False,
    sep=';',
    encoding='utf-8-sig'
)

db_reservas_atualizado.to_csv(
    f"{output_dir}/05_reservas_saldos_atualizados.csv",
    index=False,
    sep=';',
    encoding='utf-8-sig'
)
logger.info(f"Arquivos Salvos")