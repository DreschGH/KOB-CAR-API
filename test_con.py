from kob_car_api import KobCARClient, DataStorage, DataProcessor


client = KobCARClient(auto_authenticate=True)
storage = DataStorage(base_path="./data")
processor = DataProcessor()

compradores = client.get_compradores()
vendas =client.consultar_vendas()
reservas = client.consultar_reservas()

print(f"Total de compradores: {len(compradores)}")
print(f"Total de Vendas: {len(vendas)}")

storage = DataStorage(base_path="./data")

storage.save_to_database(vendas, "vendas", if_exists='replace', flatten=True)
storage.save_to_database(compradores, "compradores", if_exists='replace', flatten=True)
storage.upsert_to_database(reservas, "reservas", if_exists='replace', flatten=True)

if compradores:
    primeiro = compradores[0]
    nome = primeiro.get('pessoaJuridica', {}).get('nomeFantasia', 'N/A')
    print(f"Primeiro comprador: {nome}")