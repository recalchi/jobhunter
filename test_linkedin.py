import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.automation.linkedin_automation import LinkedInAutomation

if __name__ == '__main__':
    # Credenciais de teste (não usadas para login, apenas para simular o fluxo)
    linkedin_email = "rena.recalchi@gmail.com"
    linkedin_password = "Yumi1703$"

    # Tipos de vaga
    job_types = ["analista financeiro"]

    # Inicializa a automação
    automation = LinkedInAutomation(headless=False)
    automation.setup_driver()

    # A parte de login será feita manualmente pelo usuário para este teste
    print("Por favor, faça o login manualmente no navegador que será aberto.")
    print("Após o login, pressione Enter no terminal para continuar a automação.")
    input("Pressione Enter para continuar...")

    # Busca vagas
    automation.search_jobs(job_types)

    # Fecha o driver
    automation.close_driver()
    print("Teste de automação concluído.")


