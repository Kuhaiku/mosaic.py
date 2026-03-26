import hashlib
import base64
from datetime import datetime, timedelta

# NUNCA PASSE ESTE ARQUIVO PARA O CLIENTE. ELE É SEU GERADOR.
SECRET_KEY = "RaposoTech_Seguranca_2026_Mosaico" # Chave mestre (não mude depois de gerar as licenças)

def gerar_chave(hwid_cliente, dias_validade=365):
    # Calcula a data de expiração
    data_expiracao = (datetime.now() + timedelta(days=dias_validade)).strftime("%Y-%m-%d")
    
    # Cria a string base: HWID + Data
    dados = f"{hwid_cliente}|{data_expiracao}"
    
    # Assina os dados com sua chave mestre para impedir falsificações
    assinatura = hashlib.sha256(f"{dados}|{SECRET_KEY}".encode()).hexdigest()[:16]
    
    # Junta tudo e converte para Base64 (fica parecido com um código de ativação legível)
    chave_final = f"{dados}|{assinatura}"
    chave_b64 = base64.b64encode(chave_final.encode()).decode()
    
    print("-" * 50)
    print(f"HWID do Cliente: {hwid_cliente}")
    print(f"Válido até: {data_expiracao}")
    print(f"CHAVE DE ATIVAÇÃO: {chave_b64}")
    print("-" * 50)

# Simulação de uso:
if __name__ == "__main__":
    hwid_recebido = input("Cole o HWID do cliente aqui: ")
    gerar_chave(hwid_recebido.strip())