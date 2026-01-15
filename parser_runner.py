import os
import json
import subprocess
import threading
from datetime import datetime

class ParserRunner:
    def __init__(self):
        self.status_file = 'parser_status.json'
        self.running = False
        self.process = None
        
    def run_parser(self):
        """Run parser - just call run_all.bat"""
        if self.running:
            return {'status': 'error', 'message': 'Парсер уже запущен'}
        
        thread = threading.Thread(target=self._run_parser_thread, daemon=True)
        thread.start()
        
        return {'status': 'success', 'message': 'Парсер запущен'}
    
    def _run_parser_thread(self):
        """Just run run_all.bat - NO output capture"""
        self.running = True
        self._update_status(True, 'Парсер запущен через run_all.bat')
        
        try:
            # Simply call run_all.bat - NO output capture, NO complexity
            result = subprocess.run(
                ['cmd', '/c', 'run_all.bat'],
                cwd='C:\\Users\\Kerher\\Desktop\\ParserProd',
                shell=False
            )
            
            if result.returncode == 0:
                self._update_status(False, 'Парсинг завершён успешно!')
            else:
                self._update_status(False, f'Парсинг завершён с кодом {result.returncode}')
        except Exception as e:
            self._update_status(False, f'Ошибка: {str(e)}')
        finally:
            self.running = False
    
    def get_status(self):
        """Get status"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'running': False,
            'message': 'Не запущен'
        }
    
    def _update_status(self, running, message):
        """Update status"""
        status = {
            'running': running,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'Error updating status: {e}')

# Global instance
parser_runner = ParserRunner()

def run_parser():
    return parser_runner.run_parser()

def get_parser_status():
    return parser_runner.get_status()
