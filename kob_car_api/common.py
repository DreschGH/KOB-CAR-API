
import pandas as pd
from kob_car_api import KobCARClient, DataStorage, DataProcessor
from datetime import datetime
import calendar
import json
from kob_car_api.utils import normalize_vendas_columns, normalize_reservas_columns, get_last_n_months, normalize_compradores_columns

class CommonOps:
    def __init__(self, db_path):
        self.db_path = db_path

    def sync_ops_tables(self,n):
        """Função principal de sincronização de dados."""
        
        print("=" * 80)
        print("SINCRONIZAÇÃO DE DADOS KOB CAR - MODO UPSERT")
        print("=" * 80)
        print()
        
        print("Inicializando cliente KOB CAR...")
        client = KobCARClient(auto_authenticate=True)
        print("✓ Cliente inicializado e autenticado")
        print()
        storage = DataStorage(db_path=self.db_path)
        print("✓ Storage Conectada")
        print()
        
        all_vendas = []
        all_reservas = []
        
        print(f"Consultando dados dos últimos {n} meses...")
        print("-" * 80)
        
        for first, last, year, month in get_last_n_months(n):
            print(f"Período: {first.strftime('%Y-%m-%d')} até {last.strftime('%Y-%m-%d')}")
            
            try:
                vendas = client.consultar_vendas(
                    data_inicial=first.isoformat() + "Z",
                    data_final=last.isoformat() + "Z"
                )
                
                if vendas:
                    all_vendas.extend(vendas)
                    print(f"  ✓ Vendas: {len(vendas)} registros encontrados")
                else:
                    print(f"  - Vendas: Nenhum registro")
                    
            except Exception as e:
                print(f"  ✗ Erro ao consultar vendas: {e}")
            
            try:
                reservas = client.consultar_reservas(
                    data_inicial=first.strftime('%Y-%m-%d'),
                    data_final=last.strftime('%Y-%m-%d')
                )
                
                if reservas:
                    all_reservas.extend(reservas)
                    print(f"  ✓ Reservas: {len(reservas)} registros encontrados")
                else:
                    print(f"  - Reservas: Nenhum registro")
                    
            except Exception as e:
                print(f"  ✗ Erro ao consultar reservas: {e}")
            
            print()
        
        print("-" * 80)
        print(f"Total coletado: {len(all_vendas)} vendas, {len(all_reservas)} reservas")
        print()
        
        if all_vendas:
            print("Processando vendas...")
            
            df_vendas = pd.json_normalize(all_vendas)
            df_vendas = normalize_vendas_columns(df_vendas)
            
            print(f"Realizando UPSERT de {len(df_vendas)} vendas...")
            try:
                rows_affected = storage.upsert_to_database(
                    data=df_vendas,
                    table_name="vendas",
                    primary_keys=["id"]
                )
            except Exception as e:
                print(f"✗ Erro ao fazer UPSERT de vendas: {e}")
            
            print()
        else:
            print("Nenhuma venda para processar")
            print()
        
        if all_reservas:
            print("Processando reservas...")
            
            df_reservas = pd.json_normalize(all_reservas)
            df_reservas = normalize_reservas_columns(df_reservas)
            
            print(f"Realizando UPSERT de {len(df_reservas)} reservas...")
            try:
                rows_affected = storage.upsert_to_database(
                    data=df_reservas,
                    table_name="reservas",
                    primary_keys=["reservaId"],
                    
                )
                print(f"✓ UPSERT concluído: {rows_affected} registros processados")
            except Exception as e:
                print(f"✗ Erro ao fazer UPSERT de reservas: {e}")
            
            print()
        else:
            print("Nenhuma reserva para processar")
            print()
        

        compradores = client.get_compradores()
        if compradores:
            df_compradores= pd.json_normalize(compradores)
            df_compradores = normalize_compradores_columns(df_compradores)
            try:
                rows_affected = storage.upsert_to_database(
                    data=df_compradores,
                    table_name='compradores',
                    primary_keys=['pessoaJuridica_cnpj']
                    )
            except Exception as e:
                print(f'✗ Erro ao fazer UPSERT de Compradores: {e}')

        print("=" * 80)
        print("SINCRONIZAÇÃO CONCLUÍDA")
        print("=" * 80)
        
        try:
            total_vendas_db = DataProcessor.get_total_count(storage=storage, table_name="vendas")
            total_reservas_db = DataProcessor.get_total_count(storage=storage, table_name="reservas")
            total_compradores_db = DataProcessor.get_total_count(storage=storage, table_name="compradores")

            print(f"Total de vendas no banco: {total_vendas_db['total'].iloc[0]}")
            print(f"Total de reservas no banco: {total_reservas_db['total'].iloc[0]}")
            print(f"Quantidade de compradores no banco: {total_compradores_db['total'].iloc[0]}")
            
        except Exception as e:
            print(f"Não foi possível consultar totais: {e}")
        
