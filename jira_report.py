import os
import requests
from datetime import datetime, timedelta

# Cargar variables de entorno (aunque ahora se pasan principalmente por argumentos)
# from dotenv import load_dotenv
# load_dotenv()

class JiraAPIClient:
    def __init__(self, url, user=None, token=None):
        self.url = url.rstrip('/')
        self.user = user
        self.token = token
        
        if not self.url:
            raise ValueError("URL de Jira es obligatoria")
            
        if not self.token and not self.user:
             raise ValueError("Credenciales insuficientes")
             
    def _get_headers(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if self.user and self.token:
            # Basic Auth (Cloud o Server con usuario/pass)
            # requests.auth.HTTPBasicAuth lo maneja, pero aquí preparamos headers si fuera manual
            # Preferimos usar 'auth' param en requests
            pass 
        elif self.token:
            # Bearer (PAT)
            headers["Authorization"] = f"Bearer {self.token}"
            
        return headers

    def _get_auth(self):
        if self.user and self.token:
            return (self.user, self.token)
        return None

    def search_issues(self, jql, startAt=0, maxResults=100):
        api_endpoint = f"{self.url}/rest/api/2/search" # Revert to v2 based on HTML log saying "10.3.12" which is usually Server v8 or DC v9, Cloud is different. Let's stick to v2 as safer default for Server.
        
        params = {
            "jql": jql,
            "startAt": startAt,
            "maxResults": maxResults, 
            "fields": ["worklog", "summary", "issuetype"]
        }
        
        response = requests.get(
            api_endpoint,
            headers=self._get_headers(),
            auth=self._get_auth(),
            params=params
        )
        
        if response.status_code != 200:
             # Basic check to avoid re-parsing HTML
             if "html" in response.headers.get("Content-Type", ""):
                 print(f"DEBUG Response: {response.text[:500]}")
                 raise Exception(f"La respuesta fue HTML en lugar de JSON. Verifica autenticación y URL. Status: {response.status_code}")
             raise Exception(f"Error Jira API ({response.status_code}): {response.text}")
            
        return response.json()

    def get_issue_worklogs(self, issue_id):
        api_endpoint = f"{self.url}/rest/api/2/issue/{issue_id}/worklog"
        response = requests.get(
            api_endpoint,
            headers=self._get_headers(),
            auth=self._get_auth()
        )
        if response.status_code != 200:
            raise Exception(f"Error worklogs ({response.status_code})")
        return response.json()

    def get_myself(self):
        # Intentar obtener usuario actual
        api_endpoint = f"{self.url}/rest/api/3/myself"
        response = requests.get(
            api_endpoint,
            headers=self._get_headers(),
            auth=self._get_auth()
        )
        if response.status_code != 200:
            raise Exception(f"Error obteniendo usuario ({response.status_code}): {response.text}")
        try:
            return response.json()
        except Exception:
             print(f"Error parseando JSON (myself). Respuesta RAW:\n{response.text}")
             raise


def get_jira_client(url=None, user=None, token=None):
    # Wrapper para compatibilidad o inicialización simple
    jira_url = url or os.getenv('JIRA_URL')
    jira_user = user or os.getenv('JIRA_USER') or os.getenv('JIRA_EMAIL')
    jira_token = token or os.getenv('JIRA_API_TOKEN') or os.getenv('JIRA_PASSWORD')
    
    return JiraAPIClient(jira_url, jira_user, jira_token)


def get_worklogs_filtered(client, project_key, author_name, days=30, date_start=None, date_end=None):
    if date_start and date_end:
        date_limit_obj = datetime.strptime(date_start, '%Y-%m-%d')
        date_end_obj = datetime.strptime(date_end, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        date_str = date_start
    else:
        date_n_days_ago = datetime.now() - timedelta(days=days)
        date_str = date_n_days_ago.strftime('%Y-%m-%d')
        date_limit_obj = date_n_days_ago.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end_obj = None
    
    # JQL: Buscar issues en los proyectos (soporta múltiples separados por coma) que hayan sido actualizadas recientemente
    project_keys = [p.strip() for p in project_key.split(',') if p.strip()]
    projects_str = ", ".join(f'"{p}"' for p in project_keys)
    jql = f'project IN ({projects_str}) AND updatedDate >= "{date_str}"'
    
    print(f"Ejecutando JQL: {jql}")
    
    # 1. Obtener Issues (con paginación)
    issues = []
    start_at = 0
    max_results = 100
    
    while True:
        print(f"Buscando issues desde {start_at}...")
        data = client.search_issues(jql, startAt=start_at, maxResults=max_results)
        batch = data.get('issues', [])
        issues.extend(batch)
        
        total = data.get('total', 0)
        print(f"Recibidos {len(batch)} issues. Total disponible: {total}")
        
        if start_at + len(batch) >= total:
            break
            
        start_at += len(batch)
        
    print(f"Total Issues actualizados encontrados: {len(issues)}")
    
    # daily_hours = collections.defaultdict(float) # Cambiamos a lista detallada
    detailed_worklogs = []
    
    # Normalizar nombre autor para búsqueda (lowercase)
    target_author = author_name.lower().strip() if author_name else None
    
    matched_log_count = 0

    for issue in issues:
        fields = issue.get('fields', {})
        issue_key = issue.get('key')
        issue_summary = fields.get('summary', 'Sin título')
        issue_type = fields.get('issuetype', {}).get('name', 'N/A')

        worklog_container = fields.get('worklog', {})
        total_worklogs = worklog_container.get('total', 0)
        worklogs_list = worklog_container.get('worklogs', [])
        
        # Si hay mas de 20, pedir todos
        if total_worklogs > len(worklogs_list):
            try:
               full_worklogs = client.get_issue_worklogs(issue['id'])
               worklogs_list = full_worklogs.get('worklogs', [])
            except Exception as e:
                print(f"Error fetching detailed worklogs for {issue['key']}: {e}")
        
        for worklog in worklogs_list:
            author = worklog.get('author', {})
            a_name = author.get('name', '').lower()
            a_display = author.get('displayName', '').lower()
            a_key = author.get('key', '').lower() # JIRA 7+
            
            # Chequeo de autor
            is_match = False
            if target_author:
                if target_author in a_name or target_author in a_display or target_author in a_key:
                    is_match = True
            else:
                is_match = True 
                
            if not is_match:
                continue

            # Chequeo de fecha
            started_str = worklog.get('started') 
            if not started_str: continue
            
            # Parsear fecha
            try:
                worklog_date_str = started_str[:10]
                worklog_date = datetime.strptime(worklog_date_str, '%Y-%m-%d')
            except ValueError:
                continue
            
            if worklog_date >= date_limit_obj and (date_end_obj is None or worklog_date <= date_end_obj):
                seconds = worklog.get('timeSpentSeconds', 0)
                if seconds:
                    hours = seconds / 3600.0
                    
                    # Añadir detalle
                    detailed_worklogs.append({
                        "date": worklog_date_str,
                        "key": issue_key,
                        "type": issue_type,
                        "summary": issue_summary,
                        "hours": hours,
                        "author_match": author.get('displayName') or author.get('name')
                    })
                    matched_log_count += 1

    print(f"Total worklogs encontrados para '{author_name}': {matched_log_count}")
    return detailed_worklogs

def print_report(daily_hours):
    from tabulate import tabulate
    sorted_dates = sorted(daily_hours.keys())
    table_data = []
    total_hours = 0
    for date_str in sorted_dates:
        hours = daily_hours[date_str]
        table_data.append([date_str, f"{hours:.2f}"])
        total_hours += hours
        
    print("\nReporte de horas:")
    print(tabulate(table_data, headers=["Fecha", "Horas"], tablefmt="grid"))
    print(f"\nTotal horas: {total_hours:.2f}")

if __name__ == "__main__":
    try:
        client = get_jira_client()
        print(f"Conectando a {client.url}...")
        data = get_worklogs_last_days(client, 30)
        print_report(data)
    except Exception as e:
        print(f"Error: {e}")
