#!/usr/bin/env python3
import os
import sys
import yaml
import shutil
from pathlib import Path

class KubeConfigEditor:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.expanduser("~/.kube/config")
        self.config = self._load_config()

    def _load_config(self):
        """Загрузка kubeconfig"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {
                'apiVersion': 'v1',
                'kind': 'Config',
                'preferences': {},
                'clusters': [],
                'contexts': [],
                'users': []
            }

    def _save_config(self):
        """Сохранение kubeconfig"""
        # Создаем backup
        backup = self.config_path + '.bak'
        if os.path.exists(self.config_path):
            shutil.copy2(self.config_path, backup)

        # Сохраняем новый конфиг
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

        # Устанавливаем правильные права
        os.chmod(self.config_path, 0o600)

    def _get_context_info(self, context):
        """Получение информации о контексте в формате: user @ cluster"""
        ctx_name = context.get('name', '')
        ctx_data = context.get('context', {})
        user = ctx_data.get('user', '')
        cluster = ctx_data.get('cluster', '')
        return f"{ctx_name}: '{user}' @ '{cluster}'"

    def ls_contexts(self):
        """Список контекстов в формате: context.name: 'context.user' @ 'context.cluster'"""
        current = self.config.get('current-context', '')
        contexts = self.config.get('contexts', [])

        for ctx in contexts:
            ctx_name = ctx.get('name', '')
            context_info = self._get_context_info(ctx)

            if ctx_name == current:
                print(f"* {context_info}")
            else:
                print(f"  {context_info}")

    def ls_users(self):
        """Список пользователей"""
        users = self.config.get('users', [])
        for user in users:
            print(user.get('name', ''))

    def ls_clusters(self):
        """Список кластеров"""
        clusters = self.config.get('clusters', [])
        for cluster in clusters:
            name = cluster.get('name', '')
            server = cluster.get('cluster', {}).get('server', '')
            print(f"{name} {server}")

    def import_context(self, filename, context_name=None):
        """Импорт контекста(ов) из файла"""
        try:
            with open(filename, 'r') as f:
                source_config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"Error: File {filename} not found")
            return False

        # Находим контексты для импорта
        source_contexts = source_config.get('contexts', [])
        if context_name:
            source_contexts = [c for c in source_contexts if c.get('name') == context_name]
            if not source_contexts:
                print(f"Error: Context '{context_name}' not found in {filename}")
                return False

        # Собираем все необходимые объекты
        clusters_to_import = set()
        users_to_import = set()
        contexts_to_import = []

        for ctx in source_contexts:
            ctx_name = ctx.get('name')
            ctx_context = ctx.get('context', {})
            cluster_name = ctx_context.get('cluster')
            user_name = ctx_context.get('user')

            if cluster_name:
                clusters_to_import.add(cluster_name)
            if user_name:
                users_to_import.add(user_name)

            contexts_to_import.append(ctx)

        # Импортируем кластеры
        existing_clusters = {c['name']: c for c in self.config.get('clusters', [])}
        source_clusters = {c['name']: c for c in source_config.get('clusters', [])}

        for cluster_name in clusters_to_import:
            if cluster_name in source_clusters and cluster_name not in existing_clusters:
                self.config.setdefault('clusters', []).append(source_clusters[cluster_name])

        # Импортируем пользователей
        existing_users = {u['name']: u for u in self.config.get('users', [])}
        source_users = {u['name']: u for u in source_config.get('users', [])}

        for user_name in users_to_import:
            if user_name in source_users and user_name not in existing_users:
                self.config.setdefault('users', []).append(source_users[user_name])

        # Импортируем контексты
        existing_contexts = {c['name']: c for c in self.config.get('contexts', [])}

        for ctx in contexts_to_import:
            ctx_name = ctx.get('name')
            if ctx_name not in existing_contexts:
                self.config.setdefault('contexts', []).append(ctx)
            else:
                # Обновляем существующий
                idx = next(i for i, c in enumerate(self.config['contexts']) if c['name'] == ctx_name)
                self.config['contexts'][idx] = ctx

        self._save_config()
        print(f"Successfully imported {len(contexts_to_import)} context(s)")
        return True

    def export_context(self, filename, context_name):
        """Экспорт контекста в файл с current-context"""
        # Находим контекст
        contexts = self.config.get('contexts', [])
        context = next((c for c in contexts if c.get('name') == context_name), None)

        if not context:
            print(f"Error: Context '{context_name}' not found")
            return False

        # Получаем связанные объекты
        ctx_context = context.get('context', {})
        cluster_name = ctx_context.get('cluster')
        user_name = ctx_context.get('user')

        # Находим кластер
        clusters = self.config.get('clusters', [])
        cluster = next((c for c in clusters if c.get('name') == cluster_name), None)

        # Находим пользователя
        users = self.config.get('users', [])
        user = next((u for u in users if u.get('name') == user_name), None)

        # Создаем новый конфиг
        export_config = {
            'apiVersion': 'v1',
            'kind': 'Config',
            'preferences': {},
            'current-context': context_name  # Добавляем current-context
        }

        if cluster:
            export_config['clusters'] = [cluster]
        if user:
            export_config['users'] = [user]

        export_config['contexts'] = [context]

        # Сохраняем в файл
        with open(filename, 'w') as f:
            yaml.dump(export_config, f, default_flow_style=False)

        print(f"Successfully exported context '{context_name}' to {filename}")
        return True

    def switch_context(self, context_name):
        """Переключение текущего контекста"""
        contexts = self.config.get('contexts', [])
        context_exists = any(c.get('name') == context_name for c in contexts)

        if not context_exists:
            print(f"Error: Context '{context_name}' not found")
            return False

        self.config['current-context'] = context_name
        self._save_config()
        print(f"Switched to context '{context_name}'")
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: kcedit.py <command> [args]")
        print("Commands: ls [context|users|cluster], import, export, switch")
        sys.exit(1)

    editor = KubeConfigEditor()
    command = sys.argv[1]

    try:
        if command == 'ls':
            if len(sys.argv) == 2 or sys.argv[2] == 'context':
                editor.ls_contexts()
            elif sys.argv[2] == 'users':
                editor.ls_users()
            elif sys.argv[2] == 'cluster':
                editor.ls_clusters()
            else:
                print("Unknown ls target. Use: context, users, cluster")

        elif command == 'import':
            if len(sys.argv) < 3:
                print("Usage: kcedit.py import <filename> [context-name]")
                sys.exit(1)

            filename = sys.argv[2]
            context_name = sys.argv[3] if len(sys.argv) > 3 else None
            editor.import_context(filename, context_name)

        elif command == 'export':
            if len(sys.argv) < 4:
                print("Usage: kcedit.py export <filename> <context-name>")
                sys.exit(1)

            filename = sys.argv[2]
            context_name = sys.argv[3]
            editor.export_context(filename, context_name)

        elif command == 'switch':
            if len(sys.argv) < 3:
                print("Usage: kcedit.py switch <context-name>")
                sys.exit(1)

            context_name = sys.argv[2]
            editor.switch_context(context_name)

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
